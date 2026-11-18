# coding=utf-8
"""A network built in stages (OpenSpec change network-stages): the stage table of the cost optimization, its check and
the NPV of the stages from the evaluation of each stage version."""
from .db import getParentVersion
from .economics import rangeFactor, stageYears, stagedNetPresentValue


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
        cur.execute("""SELECT a.id FROM "{b}".lines a LEFT JOIN "{a}".lines n ON n.id = a.id
            WHERE n.id IS NULL OR NOT ST_Equals(a.geom, n.geom) ORDER BY a.id;""".format(b=before['version'], a=after['version']))  # nosec B608
        missing = [row['id'] for row in cur.fetchall()]
        if missing:
            problems.append(('lines', '{}: {}'.format(after['version'], ', '.join(str(lid) for lid in missing[:20]) + (' ...' if len(missing) > 20 else ''))))
    return problems


def newItems(items, previous):
    """the investment items new in a stage: the cost of each item minus its cost in the previous stage (the lines kept
    from earlier stages have the same pipes)"""
    result = []
    for key, item in items.items():
        cost = float(item.get('cost') or 0) - float((previous or {}).get(key, {}).get('cost') or 0)
        if cost > 1e-6:
            result.append(dict(item, cost=cost))
    return result


def stagesNpv(scenario, stages, evaluations, yearly_penalties):
    """NPV of the stages from the evaluation of each stage version (network-stages D3): the items new in a stage from its
    start year, the pump increase of a stage at its start, the operating costs and the yearly penalty in its years.
    Returns stagedNetPresentValue's dict with the part 'penalties' added to the split and to each stage."""
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
            investments.append(dict(pump, cost=float(pump.get('cost') or 0) * share))
            peak_kw = evaluation['pump_kw']
        staged.append({'start': int(stage['start']), 'investments': investments, 'yearly': evaluation.get('npv_yearly', evaluation['costs']),
                       'by_carrier': evaluation.get('by_carrier')})
    result = stagedNetPresentValue(scenario, staged)
    ranges = stageYears([int(s['start']) for s in stages], period)
    penalties = [penalty * rangeFactor(interest, first, last) for penalty, (first, last) in zip(yearly_penalties, ranges)]
    result['split']['penalties'] = sum(penalties)
    for part, value in zip(result['stages'], penalties):
        part['split']['penalties'] = value
        part['npv'] += value
    result['npv'] += sum(penalties)
    return result
