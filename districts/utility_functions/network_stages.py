# coding=utf-8
"""A network built in stages (OpenSpec change network-stages): the stage table of the cost optimization, its check and
the NPV of the stages from the evaluation of each stage version."""
import psycopg2.extras

from .db import getParentVersion
from .economics import rangeFactor, stageYears, stagedNetPresentValue

# a line of a later stage lies on a line of the previous stage when this share of its length is within the tolerance
# (the pipe laying of an extension rewrites the lines: new IDs, split where new customers connect; network-stages D7)
MATCH_TOLERANCE_M = 0.5
MATCH_SHARE = 0.99


def isDescendant(cur, version, ancestor):
    """version is a child (grandchild, ...) of ancestor in public.versionhandling"""
    seen = set()
    parent = getParentVersion(cur, version)
    while parent and parent not in seen:
        if parent == ancestor:
            return True
        seen.add(parent)
        parent = getParentVersion(cur, parent)
    return False


def stageProblems(cur, stages):
    """[(kind, detail)] of a stage table [{'version', 'start'}] (network-stages D1): stage 1 in year 0, increasing start
    years, each stage a descendant of the previous one, every line of a stage with the same ID and geometry in the
    later stage; [] for a valid table or one row"""
    problems = []
    if not stages:
        return [('empty', '')]
    if int(stages[0]['start']) != 0:
        problems.append(('first_start', stages[0]['version']))
    for before, after in zip(stages, stages[1:]):
        if int(after['start']) <= int(before['start']):
            problems.append(('start_order', after['version']))
        if not isDescendant(cur, after['version'], before['version']):
            problems.append(('not_descendant', '{} / {}'.format(after['version'], before['version'])))
            continue
        missing = uncoveredLines(cur, before['version'], after['version'])
        if missing:
            problems.append(('lines', '{}: {}'.format(after['version'], ', '.join(str(lid) for lid in missing[:20]) + (' ...' if len(missing) > 20 else ''))))
    return problems


def lineMatches(cur, before, after):
    """{lid of after: lid of before} for the lines of version 'after' lying on a line of version 'before'"""
    # a short line (e.g. 0.2 m at a junction) lies within the buffer of several lines: among those covering it, the
    # closest by Hausdorff distance (0 for an unchanged line, the parent for a segment of a split line)
    cur.execute("""SELECT DISTINCT ON (n.id) n.id AS lid, p.id AS parent,
            ST_Length(ST_Intersection(n.geom, ST_Buffer(p.geom, %(tol)s))) / NULLIF(ST_Length(n.geom), 0) AS share
        FROM "{a}".lines n JOIN "{b}".lines p ON ST_DWithin(n.geom, p.geom, %(tol)s)
        ORDER BY n.id, ST_Length(ST_Intersection(n.geom, ST_Buffer(p.geom, %(tol)s))) >= %(share)s * ST_Length(n.geom) DESC,
            ST_HausdorffDistance(n.geom, p.geom);""".format(a=after, b=before), {'tol': MATCH_TOLERANCE_M, 'share': MATCH_SHARE})  # nosec B608
    return {row['lid']: row['parent'] for row in cur.fetchall() if row['share'] is not None and row['share'] >= MATCH_SHARE}


def uncoveredLines(cur, before, after):
    """lines of 'before' whose length the lines of 'after' lying on them do not cover (removed or moved)"""
    matches = lineMatches(cur, before, after)
    cur.execute('SELECT id, ST_Length(geom) AS length FROM "{}".lines;'.format(after))  # nosec B608
    lengths = {row['id']: float(row['length'] or 0) for row in cur.fetchall()}
    covered: dict = {}
    for lid, parent in matches.items():
        covered[parent] = covered.get(parent, 0.0) + lengths.get(lid, 0.0)
    cur.execute('SELECT id, ST_Length(geom) AS length FROM "{}".lines ORDER BY id;'.format(before))  # nosec B608
    return [row['id'] for row in cur.fetchall() if covered.get(row['id'], 0.0) < MATCH_SHARE * float(row['length'] or 0)]


def stageRoots(cur, versions):
    """[{lid: root}] per stage version: root = (index of the stage the line first appears in, its id there); a line of a
    later stage lying on a line of the previous stage has that line's root"""
    cur.execute('SELECT id FROM "{}".lines;'.format(versions[0]))  # nosec B608
    roots = [{row['id']: (0, row['id']) for row in cur.fetchall()}]
    for k in range(1, len(versions)):
        matches = lineMatches(cur, versions[k - 1], versions[k])
        cur.execute('SELECT id FROM "{}".lines;'.format(versions[k]))  # nosec B608
        roots.append({row['id']: roots[k - 1].get(matches[row['id']], (k, row['id'])) if row['id'] in matches else (k, row['id'])
                      for row in cur.fetchall()})
    return roots


def writeBundles(cur, version, bundles):
    """pipe bundles {lid: bid} into the lines of a version, with the update trigger of the version handling disabled:
    it would copy the bundle by ID into the descendants, where the same ID may be another line (network-stages D8)"""
    if not bundles:
        return
    cur.execute("""SELECT t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND c.relname = 'lines' AND t.tgname = 'column_update_trigger' AND t.tgenabled <> 'D';""", (version,))
    active = cur.fetchone() is not None
    if active:
        cur.execute('ALTER TABLE "{}".lines DISABLE TRIGGER column_update_trigger;'.format(version))  # nosec B608
    try:
        psycopg2.extras.execute_values(cur, 'UPDATE "{}".lines l SET pipe_bundle_type_id = v.bid FROM (VALUES %s) AS v(id, bid) WHERE l.id = v.id;'.format(version),  # nosec B608
                                       sorted((int(lid), bid) for lid, bid in bundles.items()))
    finally:
        if active:
            cur.execute('ALTER TABLE "{}".lines ENABLE TRIGGER column_update_trigger;'.format(version))  # nosec B608


VERSION_TRIGGERS = ('my_insert_trigger', 'my_delete_trigger', 'my_truncate_trigger', 'column_update_trigger')


def versionTriggers(cur, version, enable):
    """switches the version handling triggers of every table of a version (only the loaded version has them); returns
    the number of triggers switched. The run over stages writes into each stage itself (network-stages D11)."""
    cur.execute("""SELECT c.relname AS tab, t.tgname FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s AND t.tgname = ANY(%s) AND (t.tgenabled = 'D') = %s;""", (version, list(VERSION_TRIGGERS), bool(enable)))
    rows = cur.fetchall()
    for row in rows:
        # one statement each: the event trigger restrict_column_alterations fails on a query with several
        cur.execute('ALTER TABLE "{}"."{}" {} TRIGGER {};'.format(version, row['tab'], 'ENABLE' if enable else 'DISABLE', row['tgname']))  # nosec B608
    return len(rows)


def linkStages(cur, versions):
    """each stage version a child of the one before in public.versionhandling (network-stages D11): the versions of a
    run belong together; each was copied from its own stage version, so it holds that stage's network"""
    for before, after in zip(versions, versions[1:]):
        cur.execute("""UPDATE public.versionhandling SET id_base = (SELECT id FROM public.versionhandling WHERE name = %s)
            WHERE name = %s;""", (before, after))


def stageLinks(cur, before, after):
    """lines of 'after' that the version handling, which copies a change of 'before' by ID, would treat wrongly:
    {'other': [IDs of a line of 'before' on another or a shorter line (split)], 'not_reached': [lines lying on a line of
    'before' under another ID]}"""
    matches = lineMatches(cur, before, after)
    cur.execute("""SELECT n.id FROM "{a}".lines n JOIN "{b}".lines p ON p.id = n.id
        WHERE ST_HausdorffDistance(n.geom, p.geom) > %s ORDER BY n.id;""".format(a=after, b=before), (MATCH_TOLERANCE_M,))  # nosec B608
    other = [row['id'] for row in cur.fetchall()]
    return {'other': other, 'not_reached': sorted(lid for lid, parent in matches.items() if parent != lid)}


def inheritPipes(cur, versions, roots):
    """the lines of later stages get the pipe bundle of their root (the pipe laying may have given them others);
    returns the number of lines changed"""
    states = []
    for version in versions:
        cur.execute('SELECT id, pipe_bundle_type_id AS bid FROM "{}".lines;'.format(version))  # nosec B608
        states.append({row['id']: row['bid'] for row in cur.fetchall()})
    changed = 0
    for k in range(1, len(versions)):
        new = {lid: states[root[0]][root[1]] for lid, root in roots[k].items()
               if root[0] < k and states[root[0]].get(root[1]) is not None and states[k].get(lid) != states[root[0]][root[1]]}
        writeBundles(cur, versions[k], new)
        states[k].update(new)
        changed += len(new)
    return changed


def newItems(items, previous):
    """the investment items new in a stage: the cost of each item minus its cost in the previous stage (the lines kept
    from earlier stages have the same pipes)"""
    result = []
    for key, item in items.items():
        cost = float(item.get('cost') or 0) - float((previous or {}).get(key, {}).get('cost') or 0)
        if cost > 1e-6:
            result.append(dict(item, cost=cost, kind=key[0]))
    return result


def stagesNpv(scenario, stages, evaluations, yearly_penalties):
    """NPV of the stages from the evaluation of each stage version (network-stages D3): the items new in a stage from its
    start year, the pump increase of a stage at its start, the operating costs and the yearly penalty in its years.
    Returns stagedNetPresentValue's dict with the part 'penalties' added to the split and to each stage, and 'inputs':
    per stage its investments (with 'start'), yearly costs and operating years."""
    sc = scenario['scenario']
    period = int(sc.get('period_a') or 0)
    interest = float(sc.get('interest_pct') or 0)
    staged, previous_items, peak_kw = [], None, 0.0
    for stage, evaluation in zip(stages, evaluations):
        items = dict(evaluation['items'])
        investments = newItems(items, previous_items)
        previous_items = items
        pump = evaluation['pump_item']
        if evaluation['pump_kw'] > peak_kw:
            share = (evaluation['pump_kw'] - peak_kw) / evaluation['pump_kw'] if evaluation['pump_kw'] else 0.0
            investments.append(dict(pump, cost=float(pump.get('cost') or 0) * share, kind='pumps', power_kw=evaluation['pump_kw'] - peak_kw))
            peak_kw = evaluation['pump_kw']
        staged.append({'start': int(stage['start']), 'investments': investments, 'yearly': evaluation.get('npv_yearly', evaluation['costs']),
                       'by_carrier': evaluation.get('by_carrier')})
    result = stagedNetPresentValue(scenario, staged)
    ranges = stageYears([int(s['start']) for s in stages], period)
    # the report's terms of each stage (npvRecord) from the same inputs
    result['inputs'] = [dict(stage, investments=[dict(item, start=stage['start']) for item in stage['investments']], operating=years)
                        for stage, years in zip(staged, ranges)]
    penalties = [penalty * rangeFactor(interest, first, last) for penalty, (first, last) in zip(yearly_penalties, ranges)]
    result['split']['penalties'] = sum(penalties)
    for part, value in zip(result['stages'], penalties):
        part['split']['penalties'] = value
        part['npv'] += value
    result['npv'] += sum(penalties)
    return result
