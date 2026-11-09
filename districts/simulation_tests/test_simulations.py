# coding=utf-8
"""IDA Districts simulation tests: simulate each model of the cases folder and compare its footprint
(mean values of the connections) with the reference values. See conftest.py for the options."""
import json
import os
import shutil
import time
import warnings

import pytest

from .conftest import REFERENCE_SUFFIX

pytestmark = [pytest.mark.simulation]

# not compared with the reference (performance, depends on the machine and the load)
NOT_COMPARED = {"Simulation time"}


def reference_file(model):
    return model[:-4] + REFERENCE_SUFFIX


def store_result(conn, case, footprint):
    """like the former script: one row per simulation in test_results (columns = footprint keys)"""
    row = dict(footprint, sim_case=case.split("/")[-1])
    sql = 'INSERT INTO test_results ({},test_date) VALUES ({},CURRENT_TIMESTAMP);'.format(  # nosec B608
        ','.join('"{}"'.format(key.replace('"', '')) for key in row), ','.join(['%s'] * len(row)))
    with conn.cursor() as cur:
        cur.execute(sql, list(row.values()))


def test_simulation(sim_case, simulations, results_db, request):
    model = simulations.cases[sim_case]
    result = simulations.result(sim_case)
    footprint = result.get("footprint")
    request.config._sim_summary.append({
        "case": sim_case, "status": result.get("status"), "duration_s": result.get("duration_s"),
        "simulation_time": (footprint or {}).get("Simulation time")})

    assert result.get("status") == "Simulation finished" and not result.get("errors"), \
        "simulation of {} failed (status: {}):\n{}\nwork folder: {}".format(
            sim_case, result.get("status"), "\n".join(result.get("errors") or []), result.get("work_dir"))
    assert footprint, "no footprint.txt written by IDA (work folder: {})".format(result.get("work_dir"))

    if results_db is not None:
        store_result(results_db, sim_case, footprint)

    ref_file = reference_file(model)
    if request.config.getoption("--update-references"):
        with open(ref_file, "w") as f:
            json.dump({"footprint": footprint, "updated": time.strftime("%Y-%m-%d %H:%M:%S")}, f, indent=1)
    elif not os.path.exists(ref_file):
        warnings.warn("{}: no reference values ({}), run with --update-references".format(sim_case, ref_file))
    else:
        with open(ref_file) as f:
            reference = json.load(f)["footprint"]
        rtol = request.config.getoption("--sim-rtol")
        atol = request.config.getoption("--sim-atol")
        keys = (set(reference) | set(footprint)) - NOT_COMPARED
        differences = []
        for key in sorted(keys):
            if key not in footprint or key not in reference:
                differences.append("{}: {} (reference {})".format(key, footprint.get(key, "missing"),
                                                                    reference.get(key, "missing")))
            elif footprint[key] != pytest.approx(reference[key], rel=rtol, abs=atol):
                differences.append("{}: {} (reference {})".format(key, footprint[key], reference[key]))
        assert not differences, "{}: footprint differs from {} (rtol {}, atol {}):\n{}".format(
            sim_case, ref_file, rtol, atol, "\n".join(differences))

    if not request.config.getoption("--keep-sim-files"):
        shutil.rmtree(result["work_dir"], ignore_errors=True)
