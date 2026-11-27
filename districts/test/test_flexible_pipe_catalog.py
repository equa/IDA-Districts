# coding=utf-8
"""isoplus flexible pipes (OpenSpec change pipe-series-catalog): u of every type against the catalogue, series rules and
the template rows. No database, no QGIS layers."""
import os
from collections import defaultdict

import pytest

from districts.test.flexible_pipe_catalog import (PIPES, SERIES, foamRadius, isTwin, isUnequal, templateRows, twinGeometry,
                                                  uComputed)
from districts.utility_functions.hydraulic_balancing import getNextSmallerPipe
from districts.utility_functions.twin_pipe import twinPipeEquivalent

TEMPLATES = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
TABLES = ('materials', 'pipe_constructions', 'pipe_layers', 'pipes', 'pipe_bundle_types', 'bundle_pipes', 'pipe_series',
          'pipe_series_pressure_ratings')


def copyBlocks(template):
    """{table: [row tuples]} of the COPY blocks of the template's db_tables.sql."""
    blocks, table = defaultdict(list), None
    with open(os.path.join(TEMPLATES, template, 'db_tables.sql'), encoding='utf-8') as f:
        for line in f.read().splitlines():
            if line.startswith('COPY public.'):
                table = line.split()[1][len('public.'):]
            elif line == '\\.':
                table = None
            elif table:
                blocks[table].append(tuple(line.split('\t')))
    return blocks


def band(pipe):
    if isTwin(pipe):
        return 0.0, 0.23
    if pipe.bend is None:  # the 12 m bars are the only pipes below the catalogue (design D7)
        return -0.08, 0.13
    return 0.0, 0.13


@pytest.mark.parametrize('pipe', PIPES, ids=[p.name for p in PIPES])
def test_u_within_band_of_the_catalogue(pipe):
    low, high = band(pipe)
    assert low <= uComputed(pipe) / pipe.u - 1.0 <= high


def test_isopex_h63_single():
    pipe = next(p for p in PIPES if p.name == 'isoplus isopex H-63')
    assert 0.1712 <= uComputed(pipe) <= 0.1935


def test_unequal_twin_geometry_and_conversion():
    """S-50+32: the smaller pipe on top, both inside the foam with the same clearance, convertible for FDpipebundle"""
    pipe = next(p for p in PIPES if p.name == 'isoplus isopex S-50+32')
    y1, y2, gap = twinGeometry(pipe)
    r1, r2, rc = pipe.d1 / 2000.0, pipe.d2 / 2000.0, foamRadius(pipe)
    assert y2 < 0 < y1 and gap > 0
    assert rc - (y1 + r1) == pytest.approx(gap)
    assert (y1 - r1) - (y2 + r2) == pytest.approx(gap)
    assert 0.1960 <= uComputed(pipe) <= 0.2411
    thicknesses, dx = twinPipeEquivalent(((0.0, y1, r1), (0.0, y2, r2)), rc, 1.0, 0.0221, 1.18)
    assert min(thicknesses) > 0 and dx > 0


def test_unique_inner_diameters_per_series():
    diameters = defaultdict(list)
    for pipe in PIPES:
        if pipe.series:
            diameters[pipe.series].append(pipe.d1 - 2 * pipe.s1)
    for series, values in diameters.items():
        assert len(values) == len(set(values)), series


def test_series_of_the_pipes():
    names = {s.name for s in SERIES}
    assert all(p.series in names for p in PIPES if not isUnequal(p))
    assert all(p.series is None for p in PIPES if isUnequal(p))
    assert 'isoplus isopex S twin' in names
    assert not any('isowell' in p.name for p in PIPES)


@pytest.mark.parametrize('template', ['heating_network', 'db_default_values'])
def test_templates_contain_the_derived_rows(template):
    """the rows of the templates are those of templateRows (ids after the rigid catalogue)"""
    blocks = copyBlocks(template)
    bundle = min(int(r[0]) for r in blocks['pipe_bundle_types'] if r[1].startswith('twin pipe isoplus '))
    bundle_pipe = min(int(r[0]) for r in blocks['bundle_pipes'] if int(r[1]) == bundle)
    rows = templateRows({'materials': {'PE-Xa': 4}, 'material': 6, 'construction': 51, 'layer': 118, 'pipe': 40, 'bundle': bundle,
                         'bundle_pipe': bundle_pipe, 'series': 1, 'rating': 1})
    for table in TABLES[:3] + TABLES[4:]:
        assert set(rows[table]) <= set(blocks[table]), table
    assert set(rows['materials_replace']) <= set(blocks['materials'])
    pipes = {r[1]: r for r in blocks['pipes']}
    for row in rows['pipes']:
        assert pipes[row[1]][1:] == row[1:], row[1]


@pytest.mark.parametrize('template', ['heating_network', 'db_default_values'])
def test_template_pipe_values(template):
    blocks = copyBlocks(template)
    pipes = {r[1]: r for r in blocks['pipes']}
    h50 = pipes['isoplus isopex H-50']
    assert float(h50[2]) == pytest.approx(0.0408) and h50[13] == '0.9' and h50[11] == '6' and h50[7] == 'isoplus isopex H'
    layers = [r for r in blocks['pipe_layers'] if r[1] == h50[4]]
    assert 0.050 + 2 * sum(float(r[3]) for r in layers[1:]) == pytest.approx(0.110)
    assert pipes['isoplus isopex S-40'][11] == '10'
    cu = pipes['isoplus isocu 22']
    assert cu[5] == '\\N' and cu[12] == 'f'
    assert all(r[13] == '\\N' for name, r in pipes.items() if name.startswith('Isoplus DR'))
    series = {r[1]: r for r in blocks['pipe_series']}
    assert series['Isoplus DRE Standard'][2:6] == ('rigid_single', 'EN 253', '120', '140') and series['Isoplus DRE Standard'][7] == '190'
    sid = series['isoplus isopex H'][0]
    assert ('8.5',) == tuple(r[4] for r in blocks['pipe_series_pressure_ratings'] if r[1] == sid and r[2:4] == ('50', '70'))
    materials = {r[1]: r for r in blocks['materials']}
    assert materials['PE-Xa'][5:8] == ('600', '0.00015', '17')


@pytest.mark.parametrize('template', ['heating_network', 'db_default_values'])
def test_unequal_twin_not_resized(template):
    """the pipe sizing finds no smaller pipe for a carrier of an unequal twin (no series text, own construction)"""
    blocks = copyBlocks(template)
    catalog = {int(r[0]): {'d': float(r[2]), 'k': float(r[3]), 'construction': int(r[4]),
                           'series': r[7] if r[7] != '\\N' else ('construction', int(r[4])), 'name': r[1]} for r in blocks['pipes']}
    big = next(pid for pid, p in catalog.items() if p['name'] == 'isoplus isopex S-50+32 (50 mm)')
    assert getNextSmallerPipe(big, catalog) is None
    h63 = next(pid for pid, p in catalog.items() if p['name'] == 'isoplus isopex H-63')
    assert catalog[getNextSmallerPipe(h63, catalog)]['name'] == 'isoplus isopex H-50'
