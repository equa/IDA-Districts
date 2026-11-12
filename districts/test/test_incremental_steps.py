"""Hooks of the incremental workflow steps (conftest.py): which skip or failure of a step skips the later steps."""
from types import SimpleNamespace

import pytest

from . import conftest


class Workflow:
    """stands in for the class of the workflow steps"""


def step(name, template='DB default values', templates=None):
    marker = SimpleNamespace(args=templates) if templates else None
    return SimpleNamespace(
        keywords={'incremental': True}, cls=Workflow, originalname=name, name=name,
        callspec=SimpleNamespace(indices={'wf': 0}, params={'wf': template}),
        get_closest_marker=lambda marker_name: marker if marker_name == 'templates' else None)


def outcome(when, raise_it):
    try:
        raise_it()
    except BaseException:
        return SimpleNamespace(when=when, excinfo=pytest.ExceptionInfo.from_current())


def skip(reason):
    def raise_it():
        pytest.skip(reason)
    return raise_it


def fail():
    raise AssertionError("step failed")


def setup_skip_reason(item):
    """reason why pytest_runtest_setup skips the step, None if it runs"""
    try:
        conftest.pytest_runtest_setup(item)
    except pytest.skip.Exception as e:
        return e.msg
    return None


@pytest.fixture(autouse=True)
def no_recorded_steps(monkeypatch):
    monkeypatch.setattr(conftest, '_failed_steps', {})


def test_failure_skips_later_steps():
    conftest.pytest_runtest_makereport(step('test_a'), outcome('call', fail))
    assert setup_skip_reason(step('test_b')) == "previous step failed (test_a)"


def test_fixture_skip_skips_later_steps_with_reason():
    conftest.pytest_runtest_makereport(step('test_import_streets'), outcome('setup', skip("sample data not found: X")))
    assert setup_skip_reason(step('test_pipe_laying_algorithm')) == \
        "previous step skipped (test_import_streets: sample data not found: X)"


def test_skip_in_the_test_keeps_the_workflow_running():
    conftest.pytest_runtest_makereport(step('test_create_materials'),
                                       outcome('call', skip("not part of the template 'DB default values'")))
    assert setup_skip_reason(step('test_create_pipes')) is None


def test_first_reason_is_kept():
    conftest.pytest_runtest_makereport(step('test_import_streets'), outcome('setup', skip("sample data not found: X")))
    later = step('test_import_buildings')
    reason = setup_skip_reason(later)
    conftest.pytest_runtest_makereport(later, outcome('setup', skip(reason)))
    assert setup_skip_reason(step('test_pipe_laying_algorithm')) == reason


def test_other_workflow_is_not_affected():
    conftest.pytest_runtest_makereport(step('test_a'), outcome('call', fail))
    other = step('test_b')
    other.callspec = SimpleNamespace(indices={'wf': 1}, params={'wf': 'Heating network'})
    assert setup_skip_reason(other) is None


def test_templates_marker_skips_before_the_fixtures_without_stopping_the_workflow():
    item = step('test_import_streets', template='Heating network', templates=('Empty project', 'DB default values'))
    reason = setup_skip_reason(item)
    assert reason == "not part of the template 'Heating network'"
    conftest.pytest_runtest_makereport(item, outcome('setup', skip(reason)))
    assert setup_skip_reason(step('test_generate_network_topology', template='Heating network')) is None


def test_templates_marker_lets_a_listed_template_run():
    item = step('test_import_streets', templates=('Empty project', 'DB default values'))
    assert setup_skip_reason(item) is None
