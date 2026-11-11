"""Static type check of the plugin sources with mypy (configuration: mypy.ini in the plugin folder).

The plugin has no type annotations, mypy checks the function bodies anyway (check_untyped_defs): undefined names,
wrong numbers of arguments, unknown attributes and methods, wrong string formatting, None/str mix-ups, ...
QGIS and PyQt objects are not checked (no type information).

The findings which existed when the check was introduced are listed in test/mypy_baseline.txt
(file, error code, message and how often; without line numbers, so that edits elsewhere in a file don't matter).
The tests fail
  * for every finding which is not in the baseline (new code has to be clean) and
  * for baseline entries which no longer occur (fixed: remove them, so that they can't come back).
After fixing findings (or to accept one on purpose) rewrite the baseline:
    python -m pytest test/test_static_mypy.py --update-mypy-baseline
A single line is accepted in the source with:  # type: ignore[error-code]

mypy is needed in the Python of QGIS (pip install --user mypy), without it the tests are skipped.
By hand, from the plugin folder:  python -m mypy
"""
import collections
import os
import re
import subprocess
import sys
import tempfile

import pytest

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASELINE = os.path.join(PLUGIN_DIR, 'test', 'mypy_baseline.txt')
# path:line: error: message  [code]
FINDING = re.compile(r'^(?P<path>[^:\n]+\.py):(?P<line>\d+): error: (?P<message>.*?)\s+\[(?P<code>[a-z0-9-]+)\]$')
# a baseline line: count <tab> path <tab> code <tab> message
SEP = '\t'


def run_mypy():
    """(findings, output) of mypy for the plugin; a finding is (path, line, code, message)"""
    pytest.importorskip('mypy', reason='mypy is not installed in this Python: pip install --user mypy')
    # the cache is kept outside of the plugin folder (the folder is zipped for the upload); a second run takes seconds
    cache_dir = os.path.join(tempfile.gettempdir(), 'districts_mypy_cache')
    cmd = [sys.executable, '-m', 'mypy', '--config-file', os.path.join(PLUGIN_DIR, 'mypy.ini'),
           '--cache-dir', cache_dir, '--no-color-output', '--no-error-summary', '--hide-error-context']
    env = dict(os.environ, PYTHONUTF8='1')
    proc = subprocess.run(cmd, cwd=PLUGIN_DIR, env=env, capture_output=True, text=True, encoding='utf-8',
                          errors='replace', timeout=1800)
    output = proc.stdout + proc.stderr
    findings = []
    for text in proc.stdout.splitlines():
        m = FINDING.match(text.strip())
        if m:
            findings.append((m['path'].replace('\\', '/'), int(m['line']), m['code'], m['message']))
    # 0: no findings, 1: findings, everything else: mypy could not check (crash, syntax error, wrong configuration)
    assert proc.returncode in (0, 1), 'mypy failed (exit code {}):\n{}'.format(proc.returncode, output)
    assert proc.returncode == 0 or findings, 'mypy reports errors which are not understood:\n{}'.format(output)
    return findings, output


def count_findings(findings):
    """{(path, code, message): number of findings}"""
    return collections.Counter((path, code, message) for path, line, code, message in findings)


def read_baseline():
    known = collections.Counter()
    if not os.path.exists(BASELINE):
        return known
    with open(BASELINE, encoding='utf-8') as f:
        for text in f:
            text = text.rstrip('\n')
            if not text or text.startswith('#'):
                continue
            count, path, code, message = text.split(SEP, 3)
            known[(path, code, message)] = int(count)
    return known


def write_baseline(findings):
    from mypy.version import __version__ as mypy_version
    counts = count_findings(findings)
    with open(BASELINE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# Known findings of mypy (test/test_static_mypy.py): count, file, error code, message (tab separated).\n')
        f.write('# Written with: python -m pytest test/test_static_mypy.py --update-mypy-baseline\n')
        f.write('# Only remove findings here by fixing them. mypy {}, {} findings.\n'.format(mypy_version, len(findings)))
        for (path, code, message), count in sorted(counts.items()):
            f.write(SEP.join([str(count), path, code, message]) + '\n')


@pytest.fixture(scope='module')
def mypy_findings(request):
    findings, output = run_mypy()
    if request.config.getoption('--update-mypy-baseline'):
        write_baseline(findings)
    return findings


def test_no_new_mypy_findings(mypy_findings):
    known = read_baseline()
    counts = count_findings(mypy_findings)
    new = []
    for key in sorted(counts):
        if counts[key] > known[key]:
            path, code, message = key
            lines = sorted(line for p, line, c, m in mypy_findings if (p, c, m) == key)
            new.append('{}: [{}] {}\n    {} x (known: {}), lines {}'.format(
                path, code, message, counts[key], known[key], ', '.join(str(n) for n in lines)))
    assert not new, ('{} new mypy findings (not in test/mypy_baseline.txt). Fix them, or accept a line with '
                     '"# type: ignore[code]":\n'.format(len(new)) + '\n'.join(new))


def test_mypy_baseline_is_up_to_date(mypy_findings):
    known = read_baseline()
    counts = count_findings(mypy_findings)
    fixed = ['{}: [{}] {}  ({} -> {})'.format(path, code, message, known[(path, code, message)], counts[(path, code, message)])
             for (path, code, message) in sorted(known) if counts[(path, code, message)] < known[(path, code, message)]]
    assert not fixed, ('{} known mypy findings no longer occur (or less often). Remove them from the baseline:\n'
                       '    python -m pytest test/test_static_mypy.py --update-mypy-baseline\n'.format(len(fixed))
                       + '\n'.join(fixed))


def test_mypy_checks_the_plugin():
    """the check itself: a wrong call in a copy of the configuration's scope is found (guards against a
    configuration that silently checks nothing, e.g. a wrong exclude or ignore_errors)"""
    pytest.importorskip('mypy', reason='mypy is not installed in this Python: pip install --user mypy')
    with tempfile.TemporaryDirectory() as folder:
        package = os.path.join(folder, 'districts')
        os.makedirs(os.path.join(package, 'utility_functions'))
        open(os.path.join(package, '__init__.py'), 'w').close()
        with open(os.path.join(package, 'utility_functions', 'helper.py'), 'w') as f:
            f.write('def area(width, height):\n    return width * height\n')
        with open(os.path.join(package, 'broken.py'), 'w') as f:
            f.write('from qgis.core import QgsProject\n'
                    'from .utility_functions.helper import area\n'
                    'from districts.utility_functions import helper\n\n'
                    'def run():\n'
                    '    QgsProject.instance().anything()\n'      # QGIS objects are not checked
                    '    area(1)\n'                               # call-arg
                    '    helper.volume(1, 2, 3)\n'                # attr-defined
                    '    return undefined_name\n')                # name-defined
        with open(os.path.join(PLUGIN_DIR, 'mypy.ini'), encoding='utf-8') as f:
            config = f.read()
        config_file = os.path.join(package, 'mypy.ini')
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config)
        proc = subprocess.run([sys.executable, '-m', 'mypy', '--config-file', config_file, '--no-incremental',
                               '--no-color-output'], cwd=package, env=dict(os.environ, PYTHONUTF8='1'),
                              capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    codes = sorted(m['code'] for m in (FINDING.match(t.strip()) for t in proc.stdout.splitlines()) if m)
    assert codes == ['attr-defined', 'call-arg', 'name-defined'], proc.stdout + proc.stderr
