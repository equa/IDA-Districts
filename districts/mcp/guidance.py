# coding=utf-8
"""Guidance of the AI connection (D8): the workflow map (wiki_map.json), the state of each step from the database and
the project files, and the wiki IDA_Districts read through its public REST API."""
import glob
import json
import os
import urllib.error
import urllib.parse
import urllib.request

MAP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wiki_map.json')
TIMEOUT_S = 10
_cache = {}


def loadMap():
    with open(MAP_FILE, encoding='utf-8') as f:
        return json.load(f)


# ---------------- workflow state ----------------
def _count(cur, schema, table, where='true'):
    cur.execute('SELECT to_regclass(%s) IS NOT NULL AS ok;', ('"{}"."{}"'.format(schema, table) if schema else table,))
    if not cur.fetchone()['ok']:
        return 0
    cur.execute('SELECT count(*) AS n FROM {} WHERE {};'.format('"{}"."{}"'.format(schema, table) if schema else table, where))  # nosec B608
    return cur.fetchone()['n']


def _versionDir(config):
    return os.path.join(config['pathProjects'] + config['projectName'], 'versions', config['versionName'])


def _projectDir(config):
    return config['pathProjects'] + config['projectName']


def stepState(cur, config, key):
    """(state, reason) of a step: done, missing or stale"""
    from ..utility_functions.network_economics import resultTables
    s = config['versionName']
    vdir = _versionDir(config)
    if key == 'project':
        return 'done', 'project {}'.format(config['projectName'])
    if key == 'version':
        return 'done', 'version {}'.format(s)
    if key == 'import':
        n = _count(cur, s, 'streets') + _count(cur, s, 'buildings')
        return ('done', '{} streets and buildings'.format(n)) if n else ('missing', 'no streets or buildings')
    if key == 'climate':
        return ('done', 'climate set') if _count(cur, s, 'climate') else ('missing', 'no climate data in the version')
    if key == 'features':
        c, e = _count(cur, s, 'customers'), _count(cur, s, 'energy_plants')
        return ('done' if c and e else 'missing'), '{} customers, {} energy plants'.format(c, e)
    if key == 'elevation':
        n = _count(cur, s, 'customers')
        z = _count(cur, s, 'customers', "ST_Z(geom) IS NOT NULL AND ST_Z(geom) <> 0 AND ST_Z(geom) <> 'NaN'::float8")
        if not n:
            return 'missing', 'no customers'
        return ('done', 'heights of all customers') if z == n else ('missing', '{} of {} customers without height'.format(n - z, n))
    if key == 'templates':
        n = _count(cur, None, 'public.customer_templates') + _count(cur, None, 'public.energy_plant_templates')
        return ('done', '{} templates'.format(n)) if n else ('missing', 'no templates')
    if key == 'pipe_data':
        n = _count(cur, None, 'public.pipes', 'innerpipediameter > 0')
        return ('done', '{} pipes'.format(n)) if n else ('missing', 'no pipes in the pipe database')
    if key == 'pipe_series':
        n = _count(cur, None, 'public.pipe_series')
        return ('done', '{} pipe series'.format(n)) if n else ('missing', 'no pipe series')
    if key == 'lines':
        n = _count(cur, s, 'lines')
        return ('done', '{} lines'.format(n)) if n else ('missing', 'no lines')
    if key == 'topology':
        from ..utility_functions.topology import checkNetworkTopology
        if not _count(cur, s, 'customer_connections'):
            return 'missing', 'no topology generated'
        cur.execute('SELECT DISTINCT network FROM "{}".lines WHERE network IS NOT NULL;'.format(s))  # nosec B608
        networks = [r['network'] for r in cur.fetchall()]
        problems = checkNetworkTopology(cur, s, networks) if networks else []
        if problems:
            return 'stale', 'the topology no longer matches the lines ({} problems, see run_checks)'.format(sum(p['count'] for p in problems))
        return 'done', 'topology matches the lines'
    if key == 'sizing':
        n = _count(cur, s, 'lines')
        unsized = _count(cur, s, 'lines', 'pipe_bundle_type_id IS NULL')
        if not n:
            return 'missing', 'no lines'
        return ('done', 'every line has a pipe bundle') if not unsized else ('missing', '{} lines without pipe bundle'.format(unsized))
    if key == 'outputs':
        return ('done', 'outputs requested') if os.path.exists(os.path.join(vdir, 'invokedOutputs.txt')) else ('missing', 'no outputs requested yet')
    if key == 'energy_use':
        return ('done', 'energyUse.json') if os.path.exists(os.path.join(_projectDir(config), 'energyUse.json')) else ('missing', 'no energy-use list')
    if key == 'network_pumps':
        return ('done', 'networkPumps.json') if os.path.exists(os.path.join(_projectDir(config), 'networkPumps.json')) else ('missing', 'no network pump list')
    if key == 'build':
        built = glob.glob(os.path.join(vdir, 'network_*', '*.idm'))
        return ('done', 'network model built') if built else ('missing', 'no network model built')
    if key == 'run':
        ran = glob.glob(os.path.join(vdir, 'network_*', '*.prn')) or os.path.exists(os.path.join(vdir, 'simulatedOutputs.txt'))
        return ('done', 'simulation outputs present') if ran else ('missing', 'not simulated')
    if key == 'results':
        tables = resultTables(cur, s, 'line_s_') + resultTables(cur, s, 'customer_s_')
        if not tables:
            return 'missing', 'no results loaded'
        topo = stepState(cur, config, 'topology')
        if topo[0] == 'stale':
            return 'stale', 'results loaded, but the lines changed afterwards: ' + topo[1]
        return 'done', '{} result tables'.format(len(tables))
    if key == 'economics':
        return ('done', 'economic scenarios') if _count(cur, None, 'public.economic_scenarios') else ('missing', 'no economic scenario')
    if key == 'dynamic_sizing':
        return ('done', 'sizing iterations') if glob.glob(os.path.join(vdir, 'dynamic_sizing_iter*.json')) else ('missing', 'no dynamic sizing run')
    if key == 'periods':
        return ('done', 'periods.json') if os.path.exists(os.path.join(vdir, 'periods.json')) else ('missing', 'no period run')
    if key == 'cost_optimization':
        return ('done', 'optimization iterations') if glob.glob(os.path.join(vdir, 'cost_optimization_iter*.json')) else ('missing', 'no cost optimization run')
    raise ValueError('unknown done_when ' + key)


def workflowState(cur, config):
    data = loadMap()
    steps = []
    for step in data['steps']:
        if not cur.connection.autocommit:
            cur.execute('SAVEPOINT workflow_step;')
        try:
            state, reason = stepState(cur, config, step['done_when'])
        except Exception as e:
            if not cur.connection.autocommit:
                cur.execute('ROLLBACK TO SAVEPOINT workflow_step;')
            state, reason = 'unknown', '{}: {}'.format(type(e).__name__, e)
        entry = {'step': step['step'], 'title': step['title'], 'state': state, 'reason': reason, 'optional': step.get('optional', False),
                 'rules': step['rules']}
        if step['wiki'] == 'missing':
            entry['wiki'] = 'missing'
            entry['note'] = 'the wiki has no page for this step yet; rely on the check rules, the key figures and the tool descriptions'
        else:
            entry['wiki'] = [{'page': p, 'url': pageUrl(data, p)} for p in step['wiki']]
        steps.append(entry)
    nxt = next((s['step'] for s in steps if s['state'] in ('missing', 'stale') and not s['optional']), None)
    return {'version': config['versionName'], 'steps': steps, 'next_step': nxt}


# ---------------- wiki ----------------
def splitPage(full_name):
    """'A.B.C.WebHome' -> (['A', 'B', 'C'], 'WebHome')"""
    parts = full_name.split('.')
    if len(parts) < 2 or not all(parts):
        raise ValueError('not a full page name: ' + full_name)
    return parts[:-1], parts[-1]


def pageUrl(data, full_name):
    spaces, page = splitPage(full_name)
    return '{}/bin/view/{}/'.format(data['base_url'], '/'.join(urllib.parse.quote(s) for s in spaces)) if page == 'WebHome' else \
        '{}/bin/view/{}/{}'.format(data['base_url'], '/'.join(urllib.parse.quote(s) for s in spaces), urllib.parse.quote(page))


def restUrl(data, full_name):
    spaces, page = splitPage(full_name)
    return '{}/rest/wikis/xwiki/{}/pages/{}?media=json'.format(
        data['base_url'], '/'.join('spaces/' + urllib.parse.quote(s) for s in spaces), urllib.parse.quote(page))


class WikiError(Exception):
    pass


def fetchJson(url):
    if url in _cache:
        return _cache[url]
    request = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'DistrictsModeler'})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:  # nosec B310 (fixed https base URL)
            data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise WikiError('wiki page not found') from e
        raise WikiError('wiki unreachable (HTTP {})'.format(e.code)) from e
    except (urllib.error.URLError, OSError, ValueError) as e:
        raise WikiError('wiki unreachable ({})'.format(getattr(e, 'reason', e))) from e
    _cache[url] = data
    return data


def searchHelp(query, limit=10):
    data = loadMap()
    url = '{}/rest/wikis/xwiki/query?{}'.format(data['base_url'], urllib.parse.urlencode(
        {'q': query, 'type': 'solr', 'number': 50, 'media': 'json'}))
    results = fetchJson(url).get('searchResults') or []
    prefix = data['space'] + '.'
    hits = [{'page': r['pageFullName'], 'title': r.get('title'), 'url': pageUrl(data, r['pageFullName'])}
            for r in results if (r.get('pageFullName') or '').startswith(prefix)]
    return {'query': query, 'results': hits[:max(1, min(limit, 50))]}


def readHelpPage(full_name):
    data = loadMap()
    if not full_name.startswith(data['space'] + '.'):
        raise WikiError('only pages of the space {} can be read'.format(data['space']))
    page = fetchJson(restUrl(data, full_name))
    return {'page': full_name, 'title': page.get('title'), 'url': pageUrl(data, full_name), 'syntax': page.get('syntax'),
            'modified': page.get('modified'), 'content': page.get('content') or ''}
