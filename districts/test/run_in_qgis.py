# coding=utf-8
"""Run the pytest tests inside the running QGIS (QGIS Python console: "Run script").

Uses the real iface, the plugin settings and the authentication DB of the
current QGIS profile. pytest must be installed in the QGIS Python:
    python -m pip install --user pytest

Edit PYTEST_ARGS to select tests, e.g. ["-k", "heating"] or ["-m", "not ida"].
"""
import os
import sys

import pytest

PYTEST_ARGS = ["-v", "-k", "heating"]

test_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else \
    os.path.join(os.path.dirname(os.path.dirname(__import__("districts").__file__)), "districts", "test")
plugin_dir = os.path.dirname(test_dir)

os.environ["DISTRICTS_TEST_IN_QGIS"] = "1"
# QGIS already runs: no pytest-qgis app, no cache folder in the plugin dir;
# the QGIS console has no real stdout/stderr file descriptors (capture=sys, no faulthandler)
exit_code = pytest.main([os.path.join(test_dir, "test_workflow.py"), "--rootdir", plugin_dir,
                         "-p", "no:pytest_qgis", "-p", "no:cacheprovider", "-p", "no:faulthandler",
                         "--capture=sys"] + PYTEST_ARGS)
os.environ.pop("DISTRICTS_TEST_IN_QGIS", None)

# pytest keeps the imported test modules; remove them so that changed tests are reloaded next time
for name in [m for m in sys.modules if m.startswith("districts.test")]:
    del sys.modules[name]
print("--finished testing: {}--".format("OK" if exit_code == 0 else "FAILED ({})".format(int(exit_code))))
