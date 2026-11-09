# coding=utf-8
"""IDA Districts simulation tests (formerly test_functions/automated_component_testing.py).

Not part of the default test run (pytest.ini: testpaths = test), start them explicitly:

    python-qgis.bat -m pytest simulation_tests -v --sim-workers 4

Every model (*.idm) in the cases folder is one test case. The simulations run in parallel in separate
processes (run_simulation.py), each with its own work folder: a copy of the model (IDA saves the model after
the simulation) and its own TEMP folder (IDA writes footprint.txt there). The test compares the footprint
with the reference values of the case (<model>.reference.json next to the model).

Options:
    --sim-cases DIR         folder with the models (env DISTRICTS_SIM_CASES, default C:\\EQUA\\Projekte\\districts\\testing)
    --sim-workers N         parallel simulations (default: half of the CPU cores, max. 4)
    --sim-timeout S         timeout per simulation in seconds (default 18000 = 5 h)
    --update-references     store the footprints of this run as reference values
    --sim-rtol / --sim-atol tolerances of the comparison with the references (default 1e-3 / 1e-3)
    --keep-sim-files        keep the work folders (default: kept only for failed cases)
    --store-results         store the footprints in the DB table test_results (like the former script);
                            env DISTRICTS_SIM_DB_HOST/_PORT/_USER/_PASSWORD/_NAME (default component_testing)
"""
import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

DEFAULT_CASES = "C:\\EQUA\\Projekte\\districts\\testing"
RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_simulation.py")
REFERENCE_SUFFIX = ".reference.json"


def pytest_addoption(parser):
    group = parser.getgroup("districts simulation tests")
    group.addoption("--sim-cases", default=os.environ.get("DISTRICTS_SIM_CASES", DEFAULT_CASES))
    group.addoption("--sim-workers", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)))
    group.addoption("--sim-timeout", type=float, default=5 * 3600)
    group.addoption("--sim-rtol", type=float, default=1e-3)
    group.addoption("--sim-atol", type=float, default=1e-3)
    group.addoption("--update-references", action="store_true")
    group.addoption("--keep-sim-files", action="store_true")
    group.addoption("--store-results", action="store_true")
    group.addoption("--sim-districts-path", default=os.environ.get(
        "DISTRICTS_TEST_PATH_DISTRICTS", "C:\\Program Files (x86)\\IDA Districts"))


def collect_cases(root):
    """{case id: model path}; case id = path relative to the cases folder without .idm ('/' separated)"""
    cases = {}
    for folder, _, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".idm"):
                path = os.path.join(folder, name)
                cases[os.path.relpath(path, root)[:-4].replace("\\", "/")] = path
    return dict(sorted(cases.items()))


def pytest_generate_tests(metafunc):
    if "sim_case" in metafunc.fixturenames:
        root = metafunc.config.getoption("--sim-cases")
        cases = collect_cases(root) if os.path.isdir(root) else {}
        metafunc.parametrize("sim_case", list(cases) or [pytest.param(None, marks=pytest.mark.skip(
            reason="no simulation models (*.idm) in {} (--sim-cases)".format(root)))], ids=list(cases) or ["no_cases"])


class SimulationPool:
    """Runs the simulations of the selected cases in parallel processes (started at the beginning of the session)."""

    def __init__(self, config, cases):
        self.config = config
        self.cases = cases
        self.work_root = os.path.join(tempfile.gettempdir(), "districts_simtests", time.strftime("%Y%m%d_%H%M%S"))
        self.processes = {}
        # large models first: the long simulations start first, the small ones fill the gaps
        order = sorted(cases, key=lambda c: os.path.getsize(cases[c]), reverse=True)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=config.getoption("--sim-workers"))
        self.futures = {case: self.executor.submit(self._simulate, case) for case in order}

    def work_dir(self, case):
        return os.path.join(self.work_root, case.replace("/", "__"))

    def _simulate(self, case):
        work_dir = self.work_dir(case)
        os.makedirs(work_dir, exist_ok=True)
        model = os.path.join(work_dir, os.path.basename(self.cases[case]))
        shutil.copyfile(self.cases[case], model)
        result_file = os.path.join(work_dir, "result.json")
        log_file = os.path.join(work_dir, "runner.log")
        cmd = [sys.executable, RUNNER, model, work_dir, result_file, self.config.getoption("--sim-districts-path")]
        timeout = self.config.getoption("--sim-timeout")
        with open(log_file, "w") as log:
            process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)  # nosec B603
            self.processes[case] = process
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                kill_tree(process.pid)
                return {"status": "timeout", "errors": ["no result after {} s".format(timeout)], "footprint": None,
                        "work_dir": work_dir}
        if not os.path.exists(result_file):
            with open(log_file, errors="replace") as log:
                return {"status": None, "errors": ["runner failed (exit code {}):\n{}".format(
                    process.returncode, log.read()[-3000:])], "footprint": None, "work_dir": work_dir}
        with open(result_file) as f:
            result = json.load(f)
        result["work_dir"] = work_dir
        return result

    def result(self, case):
        return self.futures[case].result()

    def shutdown(self):
        for future in self.futures.values():
            future.cancel()
        for process in self.processes.values():
            if process.poll() is None:
                kill_tree(process.pid)
        self.executor.shutdown(wait=True)


def kill_tree(pid):
    """end the runner and the IDA Districts process it started"""
    subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)  # nosec B603 B607


@pytest.fixture(scope="session")
def simulations(request):
    root = request.config.getoption("--sim-cases")
    all_cases = collect_cases(root)
    selected = {item.callspec.params["sim_case"] for item in request.session.items
                if hasattr(item, "callspec") and item.callspec.params.get("sim_case")}
    pool = SimulationPool(request.config, {case: all_cases[case] for case in selected if case in all_cases})
    request.config._sim_summary = []
    yield pool
    pool.shutdown()
    # the work folders of passed cases are removed by the test: remove the folder of the run if it is empty
    try:
        os.rmdir(pool.work_root)
    except OSError:
        pass


@pytest.fixture(scope="session")
def results_db(request):
    """connection to the DB of the former component testing (test_results), only with --store-results"""
    if not request.config.getoption("--store-results"):
        yield None
        return
    import psycopg2
    user = os.environ.get("DISTRICTS_SIM_DB_USER")
    if not user:
        pytest.fail("--store-results: DISTRICTS_SIM_DB_USER / DISTRICTS_SIM_DB_PASSWORD not set", pytrace=False)
    conn = psycopg2.connect(host=os.environ.get("DISTRICTS_SIM_DB_HOST", "localhost"),
                            port=os.environ.get("DISTRICTS_SIM_DB_PORT", "5432"),
                            dbname=os.environ.get("DISTRICTS_SIM_DB_NAME", "component_testing"),
                            user=user, password=os.environ.get("DISTRICTS_SIM_DB_PASSWORD", ""))
    conn.autocommit = True
    yield conn
    conn.close()


def pytest_terminal_summary(terminalreporter, config):
    rows = getattr(config, "_sim_summary", None)
    if not rows:
        return
    terminalreporter.section("simulation results")
    width = max(len(r["case"]) for r in rows)
    terminalreporter.write_line("{:<{w}}  {:<20}  {:>10}  {:>15}".format(
        "case", "status", "duration s", "simulation time", w=width))
    for r in sorted(rows, key=lambda r: r["case"]):
        terminalreporter.write_line("{:<{w}}  {:<20}  {:>10}  {:>15}".format(
            r["case"], str(r["status"]), r["duration_s"] if r["duration_s"] is not None else "-",
            r["simulation_time"] if r["simulation_time"] is not None else "-", w=width))
