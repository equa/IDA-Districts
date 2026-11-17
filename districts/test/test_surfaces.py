# coding=utf-8
"""Surfaces of the trench costs: dropdown values, the streets form of older projects, surfaces without trench costs."""
from districts.economic_scenarios_dialog import defaultSurfaceDropdown
from districts.utility_functions.economic_data import trenchSurfaces
from districts.utility_functions.layer_visualization import addMissingFormFields
from districts.utility_functions.network_economics import surfacesWithoutTrenchCosts


class FakeCursor:
    def __init__(self, surfaces, defaults=('paved',), table=True):
        self.surfaces, self.defaults, self.table = surfaces, defaults, table
        self.result = []

    def execute(self, sql, args=()):
        if 'to_regclass' in sql:
            self.result = [{'ok': self.table}]
        elif 'FROM public.trench_costs' in sql:
            self.result = [{'surface': s} for s in self.surfaces]
        elif 'default_surface FROM public.economic_scenarios' in sql:
            self.result = [{'default_surface': s} for s in self.defaults]

    def fetchone(self):
        return self.result[0]

    def fetchall(self):
        return self.result


def test_surfaces_of_the_trench_costs_and_those_in_use():
    cur = FakeCursor(['unpaved', 'paved', 'green area'])
    assert trenchSurfaces(cur, ['main road', None, '']) == ['green area', 'main road', 'paved', 'unpaved']
    assert trenchSurfaces(FakeCursor([], table=False), ['paved']) == ['paved']


def test_default_surface_dropdown_keeps_the_value_set():
    cur = FakeCursor(['paved', 'unpaved'], defaults=('gravel', None))
    assert defaultSurfaceDropdown(cur) == [5, None, ('gravel', 'paved', 'unpaved')]


def test_surface_added_to_the_streets_form_of_an_older_project():
    config = {'streets': {'general': [], 'physical_data': ['length_m', 'costs_eur7m']}, 'lines': {'general': ['id']}}
    assert addMissingFormFields(config)
    assert config['streets']['physical_data'] == ['length_m', 'costs_eur7m', 'surface']
    assert not addMissingFormFields(config)
    moved = {'streets': {'general': ['surface'], 'physical_data': []}}
    assert not addMissingFormFields(moved)  # a field the user moved to another tab stays there


def test_surfaces_without_trench_costs():
    scenario = {'trench': {'paved': (155, 9.4), 'unpaved': (120, 5.5)}}
    trench = {1: {'paved': 10.0, 'gravel': 3.0}, 2: {'Paved': 5.0}}
    assert surfacesWithoutTrenchCosts(scenario, trench) == ['Paved', 'gravel']


def test_built_in_surfaces_shown_translated_and_saved_as_key(monkeypatch):
    import districts.ida_resources as resources
    monkeypatch.setattr(resources, 'tr_msg', {'paved': 'befestigt', 'unpaved': 'unbefestigt'}.get)
    assert resources.displayValue('surface', 'paved') == 'befestigt'
    assert resources.displayValue('surface', 'green area') == 'green area'
    assert resources.displayValue('description', 'paved') == 'paved'
    assert resources.storedValue('surface', 'befestigt ') == 'paved'
    assert resources.storedValue('surface', 'Wiese') == 'Wiese'
    assert resources.storedValue('description', 'befestigt') == 'befestigt'
