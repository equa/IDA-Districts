import pytest

from districts.PipeLayingAlgorithm import WorkerPipeLaying
from districts.utility_functions.topology import createTopology


class FakeConnection:
    def __init__(self):
        self.notices = ['NOTICE:  old notice\n']


class FakeCursor:
    def __init__(self, result, notices=()):
        self.connection = FakeConnection()
        self.result = result
        self.new_notices = list(notices)
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self.connection.notices.extend(self.new_notices)

    def fetchone(self):
        return {'result': self.result}


def test_ok_passes_table_and_tolerance():
    cur = FakeCursor('OK')
    createTopology(cur, 'temp.streets_help', .001)
    sql, params = cur.executed[0]
    assert 'pgr_createTopology' in sql
    assert params == ('temp.streets_help', .001)


def test_fail_raises_with_the_notices_of_this_call():
    cur = FakeCursor('FAIL', ['NOTICE:  Unexpected error duplicate key value\n'])
    with pytest.raises(RuntimeError) as err:
        createTopology(cur, 'temp.streets_help', .001)
    assert 'duplicate key value' in str(err.value)
    assert 'old notice' not in str(err.value)


def test_pipe_laying_without_a_network_is_refused():
    # without heating and cooling no network was prepared, the topology tables are missing
    worker = WorkerPipeLaying.__new__(WorkerPipeLaying)
    worker.check_heating_network = False
    worker.check_cooling_network = False
    assert len(worker.missingSelections()) == 1
    worker.check_heating_network = True
    worker.heating_lines_type, worker.heating_pipe_bundle, worker.heating_customer_template = '0', '1', 'keep type'
    assert worker.missingSelections() == []
