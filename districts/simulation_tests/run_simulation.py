# coding=utf-8
"""Simulate one IDA Districts model in its own process (started by the simulation tests).

    python-qgis.bat run_simulation.py <model.idm> <work_dir> <result.json> <path IDA Districts> [api delay s]

Own process: idaapi2.dll holds one IDA connection per process, parallel simulations need separate processes.
Own TEMP folder (<work_dir>/tmp): IDA writes footprint.txt to %TEMP%/idamod*/, parallel IDA sessions would
overwrite it otherwise. The model is simulated as given (the caller passes a copy, IDA saves the model).
"""
import glob
import json
import os
import sys
import time
import traceback


def read_footprint(path):
    """footprint.txt of IDA: key = value lines"""
    result = {}
    with open(path, "r", errors="replace") as f:
        for line in f:
            if "=" in line:
                key, value = line.split("=", 1)
                value = value.strip()
                try:
                    result[key.strip()] = float(value)
                except ValueError:
                    result[key.strip()] = value
    return result


def main(model, work_dir, result_file, path_districts, api_delay="10"):
    result = {"model": model, "status": None, "errors": [], "footprint": None, "footprint_file": None}
    start = time.time()
    try:
        # before IDA is started: IDA inherits the environment of this process
        tmp = os.path.join(work_dir, "tmp")
        os.makedirs(tmp, exist_ok=True)
        os.environ["TEMP"] = tmp
        os.environ["TMP"] = tmp

        # the districts package (plugin folder) and a QgsApplication (QgsMessageLog of the plugin code)
        plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, os.path.dirname(plugin_dir))
        from qgis.core import QgsApplication
        app = QgsApplication([], False)
        app.initQgis()
        messages = []
        QgsApplication.messageLog().messageReceived.connect(
            lambda message, tag, level: messages.append(message) if tag == "Districts" else None)

        from districts.utility_functions.workers import WorkerSimulateAPI

        config = {"pathDistricts": os.path.join(path_districts, ""), "districts_api_delay": api_delay}
        worker = WorkerSimulateAPI(model, plugin_dir, config)
        worker.signals.status.connect(lambda s: result.__setitem__("status", s))
        worker.signals.error.connect(result["errors"].append)
        worker.run()  # synchronously in this process
        app.processEvents()
        result["errors"] += messages

        footprints = glob.glob(os.path.join(tmp, "idamod*", "footprint.txt"))
        if footprints:
            result["footprint_file"] = footprints[0]
            result["footprint"] = read_footprint(footprints[0])
    except Exception:
        result["errors"].append(traceback.format_exc())
    result["duration_s"] = round(time.time() - start, 1)
    with open(result_file, "w") as f:
        json.dump(result, f, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
    # do not wait for Qt/QGIS cleanup (exit_ida already closed IDA)
    os._exit(0)
