# coding=utf-8
"""isoplus flexible pipes (planning manual chapter 3 "Flexible Verbundsysteme", as of 2015-03-25 / 2016-12-30):
catalogue values, the layers and twin geometry derived from them, their heat loss coefficient u, and the rows of the
plugin templates built from them (OpenSpec change pipe-series-catalog, D5-D9).

Nothing is fitted to u (D7): the casing wall is assumed, the twin geometry follows a rule, and u only checks the result
against the catalogue. The templates heating_network and db_default_values contain exactly the rows of templateRows()
(test_flexible_pipe_catalog.py)."""
import math
from collections import namedtuple
from decimal import Decimal

import numpy as np

from districts.utility_functions.pipe_resistances import casingResistanceMatrix

SOURCE = 'isoplus planning manual chapter 3 (2015/2016)'
LAMBDA_FOAM = 0.0221     # PUR of the flexible pipes, lambda50
LAMBDA_SOIL = 1.0        # conditions of the catalogue's u: ground 1.0 W/(m K), cover 0.80 m,
COVER = 0.80             # single pipes with a neighbour at 100 mm
SINGLE_GAP = 0.100
TWIN_DEPTH = 1.0         # depth of the casing centre in the pipe bundles of the templates

# name: (lambda, cp, rho, E, alpha, Re, nu); 20 degC values of the catalogue; cp and rho of the casing and the foam are
# not in the catalogue and taken from the rigid PEHD and PUR rows (the simulation reads them, D8)
MATERIALS = {
    'PE-Xa': (0.38, 2300, 938, 600, 0.00015, 17, None),
    'P195GH': (55.2, 430, 7850, 211800, 0.0000113, 195, None),
    'Cu-DHP': (305, 386, 8940, 132000, 0.0000168, 65, None),
    'PE 100': (0.40, 2350, 960, 1000, 0.00018, 23, None),
    'PE-LLD': (0.33, 1900, 950, None, None, None, None),
    'PUR flexible foam': (LAMBDA_FOAM, 130, 60, None, None, None, None),
}

Series = namedtuple('Series', 'name system_type standard t_cont t_peak t_min sigma safety description')
SERIES = [
    Series('Isoplus DRE Standard', 'rigid_single', 'EN 253', 120, 140, None, None, None,
           'isoplus rigid single pipes (planning manual chapter 2); temperatures of EN 253, axial stress by EN 13941 from Re'),
    Series('Isoplus DRD Standard', 'rigid_twin', 'EN 15698-1', 120, 140, None, None, None,
           'isoplus rigid twin pipes (planning manual chapter 2); temperatures of EN 253, axial stress by EN 13941 from Re'),
    Series('isoplus isoflex', 'flexible_metal', 'EN 15632-4', 120, 140, None, 150, None, SOURCE + ', 3.2 isoflex: steel P195GH'),
    Series('isoplus isoflex v', 'flexible_metal', 'EN 15632-4', 120, 140, None, 150, None, SOURCE + ', 3.2 isoflex, reinforced insulation'),
    Series('isoplus isoflex twin', 'flexible_metal', 'EN 15632-4', 120, 140, None, 150, None, SOURCE + ', 3.2 isoflex twin pipe'),
    Series('isoplus isocu', 'flexible_metal', 'EN 15632-4', 120, 140, None, 110, None, SOURCE + ', 3.4 isocu: copper Cu-DHP'),
    Series('isoplus isocu twin', 'flexible_metal', 'EN 15632-4', 120, 140, None, 110, None, SOURCE + ', 3.4 isocu twin pipes'),
    Series('isoplus isopex H', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating 6 bar: PE-Xa SDR 11; ratings DIN 16893, water'),
    Series('isoplus isopex H u', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating, reduced insulation'),
    Series('isoplus isopex H v', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating, reinforced insulation'),
    Series('isoplus isopex H bar', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating, straight 12 m bars'),
    Series('isoplus isopex H twin', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating twin pipes'),
    Series('isoplus isopex H twin v', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex heating twin pipes, reinforced insulation'),
    Series('isoplus isopex S', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25, SOURCE + ', 3.5 isopex sanitary 10 bar: PE-Xa; ratings DIN 16893, water'),
    Series('isoplus isopex S twin', 'flexible_plastic', 'EN 15632-2', 80, 95, None, None, 1.25,
           SOURCE + ', 3.5 isopex sanitary twin pipes (unequal carriers; their pipes have no series text and are not resized)'),
    Series('isoplus isoclima', 'flexible_plastic', 'EN 12201-2', 40, None, -40, None, 1.25, SOURCE + ', 3.6 isoclima: PE 100 SDR 11, cold water'),
    Series('isoplus isoclima u', 'flexible_plastic', 'EN 12201-2', 40, None, -40, None, 1.25, SOURCE + ', 3.6 isoclima, reduced insulation'),
]

_TEMPS = (10, 20, 30, 40, 50, 60, 70, 80, 90, 95)
_YEARS = (1, 5, 10, 25, 50)
# allowed pressure [bar] by operating time (rows) and continuous temperature (columns); None: not allowed
_ISOPEX_H = ((17.9, 15.8, 14.0, 12.5, 11.1, 9.9, 8.9, 8.0, 7.2, 6.8),
             (17.5, 15.5, 13.8, 12.2, 10.9, 9.7, 8.7, 7.8, 7.0, 6.6),
             (17.4, 15.4, 13.7, 12.1, 10.8, 9.7, 8.6, 7.7, 6.9, None),
             (17.2, 15.2, 13.5, 12.0, 10.7, 9.5, 8.5, 7.6, None, None),
             (17.1, 15.1, 13.4, 11.9, 10.6, 9.5, 8.5, None, None, None))
_ISOPEX_S = ((28.3, 25.1, 22.3, 19.8, 17.7, 15.8, 14.1, 12.7, 11.4, 10.8),
             (27.8, 24.6, 21.9, 19.4, 17.3, 15.5, 13.8, 12.4, 11.1, None),
             (27.6, 24.4, 21.7, 19.3, 17.2, 15.3, 13.7, 12.3, 11.0, None),
             (27.3, 24.2, 21.4, 19.1, 17.0, 15.2, 13.6, 12.1, None, None),
             (27.1, 24.0, 21.3, 18.9, 16.8, 15.0, 13.4, None, None, None))


def _grid(table):
    return [(y, t, p) for y, row in zip(_YEARS, table) for t, p in zip(_TEMPS, row) if p is not None]


_ISOCLIMA = [(5, 10, 20.2), (10, 10, 19.8), (25, 10, 19.3), (50, 10, 19.0), (5, 20, 16.9), (10, 20, 16.6), (25, 20, 16.2), (50, 20, 16.0),
             (5, 30, 14.4), (10, 30, 14.1), (25, 30, 13.8), (50, 30, 13.5), (5, 40, 12.3), (10, 40, 12.1), (25, 40, 11.8), (50, 40, 11.6),
             (5, 50, 10.7), (10, 50, 10.4), (15, 50, 9.5), (5, 60, 7.7)]
RATINGS = {name: _grid(_ISOPEX_H) for name in ('isoplus isopex H', 'isoplus isopex H u', 'isoplus isopex H v', 'isoplus isopex H bar',
                                               'isoplus isopex H twin', 'isoplus isopex H twin v')}
RATINGS.update({'isoplus isopex S': _grid(_ISOPEX_S), 'isoplus isopex S twin': _grid(_ISOPEX_S),
                'isoplus isoclima': _ISOCLIMA, 'isoplus isoclima u': _ISOCLIMA})

# type, series, carrier material, roughness [m], p_max [bar], carrier (outer diameter, wall) [mm], second carrier of a twin
# (None: single pipe), casing outer diameter [mm], minimum bend radius [m] (None: straight bars), u [W/(m K)]
Pipe = namedtuple('Pipe', 'name series material k p_max d1 s1 d2 s2 casing bend u')
_KINDS = {'isoflex': ('P195GH', 0.00001, 25), 'isocu': ('Cu-DHP', 0.0000015, 25), 'isopex H': ('PE-Xa', 0.000007, 6),
          'isopex S': ('PE-Xa', 0.000007, 10), 'isoclima': ('PE 100', 0.000015, 11.6)}


def _pipe(kind, name, series, d1, s1, d2, s2, casing, bend, u):
    material, k, p_max = _KINDS[kind]
    return Pipe('isoplus ' + name, series and 'isoplus ' + series, material, k, p_max, d1, s1, d2, s2, casing, bend, u)


PIPES = [
    _pipe('isoflex', 'isoflex 20', 'isoflex', 20, 2.0, None, None, 75, 0.8, 0.0955),
    _pipe('isoflex', 'isoflex 28', 'isoflex', 28, 2.0, None, None, 75, 0.8, 0.1248),
    _pipe('isoflex', 'isoflex 28 v', 'isoflex v', 28, 2.0, None, None, 90, 0.9, 0.1072),
    _pipe('isoflex', 'isoflex 28+28', 'isoflex twin', 28, 2.0, 28, 2.0, 110, 1.1, 0.1615),
    _pipe('isocu', 'isocu 22', 'isocu', 22, 1.0, None, None, 65, 0.8, 0.1146),
    _pipe('isocu', 'isocu 28', 'isocu', 28, 1.2, None, None, 75, 0.8, 0.1248),
    _pipe('isocu', 'isocu 22+22', 'isocu twin', 22, 1.0, 22, 1.0, 90, 0.9, 0.1586),
    _pipe('isocu', 'isocu 28+28', 'isocu twin', 28, 1.2, 28, 1.2, 90, 0.9, 0.2182),
]
for _d, _s, _da, _r, _u, _dav, _rv, _uv in [(25, 2.3, 75, 0.7, 0.1121, 90, 0.8, 0.0976), (32, 2.9, 75, 0.8, 0.1405, 90, 0.8, 0.1185),
                                            (40, 3.7, 90, 0.8, 0.1468, 110, 0.9, 0.1214), (50, 4.6, 110, 0.9, 0.1514, 125, 1.0, 0.1329),
                                            (63, 5.8, 125, 1.0, 0.1712, 140, 1.1, 0.1498), (75, 6.8, 140, 1.1, 0.1851, 160, 1.2, 0.1573),
                                            (90, 8.2, 160, 1.2, 0.1989, 180, 1.4, 0.1704), (110, 10.0, 180, 1.4, 0.2270, 200, 1.6, 0.1939),
                                            (125, 11.4, 180, 1.4, 0.2880, 200, 1.6, 0.2368)]:
    PIPES.append(_pipe('isopex H', 'isopex H-{}'.format(_d), 'isopex H', _d, _s, None, None, _da, _r, _u))
    PIPES.append(_pipe('isopex H', 'isopex H-{} v'.format(_d), 'isopex H v', _d, _s, None, None, _dav, _rv, _uv))
PIPES += [
    _pipe('isopex H', 'isopex H-140', 'isopex H', 140, 12.7, None, None, 200, 1.6, 0.2945),
    _pipe('isopex H', 'isopex H-110 u', 'isopex H u', 110, 10.0, None, None, 160, 1.2, 0.2807),
    _pipe('isopex H', 'isopex H-125 Stg.', 'isopex H bar', 125, 11.4, None, None, 225, None, 0.2307),
    _pipe('isopex H', 'isopex H-140 Stg.', 'isopex H bar', 140, 12.7, None, None, 225, None, 0.2747),
    _pipe('isopex H', 'isopex H-160 Stg.', 'isopex H bar', 160, 14.6, None, None, 250, None, 0.2903),
]
for _d, _s, _da, _r, _u, _dav, _rv, _uv in [(20, 2.0, 75, 0.9, 0.1735, 90, 0.9, 0.1391), (25, 2.3, 90, 0.9, 0.1773, 110, 0.9, 0.1394),
                                            (32, 2.9, 110, 0.9, 0.1901, 125, 1.0, 0.1593), (40, 3.7, 125, 1.0, 0.2154, 140, 1.1, 0.1788),
                                            (50, 4.6, 160, 1.2, 0.2001, 180, 1.4, 0.1687), (63, 5.8, 180, 1.4, 0.2401, 200, 1.6, 0.1986)]:
    PIPES.append(_pipe('isopex H', 'isopex H-{0}+{0}'.format(_d), 'isopex H twin', _d, _s, _d, _s, _da, _r, _u))
    PIPES.append(_pipe('isopex H', 'isopex H-{0}+{0} v'.format(_d), 'isopex H twin v', _d, _s, _d, _s, _dav, _rv, _uv))
PIPES.append(_pipe('isopex H', 'isopex H-75+75', 'isopex H twin', 75, 6.8, 75, 6.8, 200, 1.4, 0.2751))
for _d, _s, _da, _r, _u in [(25, 3.5, 75, 0.7, 0.1114), (32, 4.4, 75, 0.8, 0.1395), (40, 5.5, 90, 0.8, 0.1457), (50, 6.9, 110, 0.9, 0.1503),
                            (63, 8.7, 125, 1.0, 0.1698)]:
    PIPES.append(_pipe('isopex S', 'isopex S-{}'.format(_d), 'isopex S', _d, _s, None, None, _da, _r, _u))
for _d, _s, _d2, _s2, _da, _r, _u in [(25, 3.5, 20, 2.8, 90, 0.9, 0.1616), (32, 4.4, 20, 2.8, 110, 0.9, 0.1587), (40, 5.5, 25, 3.5, 125, 1.0, 0.1722),
                                      (50, 6.9, 32, 4.4, 140, 1.1, 0.1960), (63, 8.7, 32, 4.4, 160, 1.2, 0.1954)]:
    PIPES.append(_pipe('isopex S', 'isopex S-{}+{}'.format(_d, _d2), None, _d, _s, _d2, _s2, _da, _r, _u))
for _d, _s, _da, _r, _u in [(20, 2.0, 65, 0.8, 0.1051), (25, 2.3, 75, 0.8, 0.1121), (32, 2.9, 75, 0.9, 0.1406), (40, 3.7, 90, 0.9, 0.1469),
                            (50, 4.6, 110, 1.0, 0.1515), (63, 5.8, 125, 1.1, 0.1714), (75, 6.8, 140, 1.2, 0.1852), (90, 8.2, 160, 1.4, 0.1990),
                            (110, 10.0, 180, 1.4, 0.2272)]:
    PIPES.append(_pipe('isoclima', 'isoclima {}'.format(_d), 'isoclima', _d, _s, None, None, _da, _r, _u))
PIPES.append(_pipe('isoclima', 'isoclima 110 u', 'isoclima u', 110, 10.0, None, None, 160, 1.4, 0.2810))


def isTwin(pipe):
    return pipe.d2 is not None


def isUnequal(pipe):
    return isTwin(pipe) and (pipe.d2, pipe.s2) != (pipe.d1, pipe.s1)


def casingWall(casing_mm):
    """Assumed wall of the PE-LLD casing [mm] (D6: the catalogue gives none)."""
    return max(2.0, 0.02 * casing_mm)


def foamRadius(pipe):
    """Radius of the foam body [m]."""
    return (pipe.casing / 2.0 - casingWall(pipe.casing)) / 1000.0


def twinGeometry(pipe):
    """(y of the larger pipe, y of the smaller pipe, clearance) [m] relative to the casing centre, y downwards: one pipe
    above the other, the smaller (for equal pipes the return) on top, the centres symmetric about the casing centre as
    convertTwinPipes assumes, the clearance between the pipes equal to the one of the larger pipe to the foam body (D7)."""
    r1, r2, rc = pipe.d1 / 2000.0, pipe.d2 / 2000.0, foamRadius(pipe)
    gap = (2.0 * rc - 3.0 * r1 - r2) / 3.0
    half = (r1 + r2 + gap) / 2.0
    return half, -half, gap


def uComputed(pipe):
    """Heat loss coefficient [W/(m K)] by the plugin's resistance model under the catalogue's conditions: per metre of a
    single pipe (both pipes of the pair at the same temperature) or of a twin pipe."""
    rc = foamRadius(pipe)
    depth = COVER + pipe.casing / 2000.0
    if not isTwin(pipe):
        a11 = casingResistanceMatrix([(0.0, 0.0, pipe.d1 / 2000.0)], rc, depth, LAMBDA_FOAM, LAMBDA_SOIL)[0, 0]
        dx = pipe.casing / 1000.0 + SINGLE_GAP
        a12 = math.log(math.sqrt(dx ** 2 + 4.0 * depth ** 2) / dx) / (2.0 * math.pi * LAMBDA_SOIL)
        return 1.0 / (a11 + a12)
    y1, y2, _ = twinGeometry(pipe)
    matrix = casingResistanceMatrix([(0.0, y1, pipe.d1 / 2000.0), (0.0, y2, pipe.d2 / 2000.0)], rc, depth, LAMBDA_FOAM, LAMBDA_SOIL)
    return float(np.linalg.inv(matrix).sum())


def _num(value):
    """Number as written in the templates (no float noise, None as \\N)."""
    if value is None:
        return '\\N'
    text = format(Decimal(repr(float(value))), 'f')
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text if text not in ('', '-0') else '0'


def _mm(value):
    return _num(round(value, 2))


def templateRows(ids):
    """Rows of the templates for the materials, series, ratings and pipes of this module.

    ids: {'materials': {name: id of an existing row to replace}, 'material': next id, 'construction', 'layer', 'pipe',
    'bundle', 'bundle_pipe', 'series', 'rating': next ids, 'existing_materials': {name: id} (P235, PEHD, foam, unused)}.
    Returns {table: [row tuples of strings]} in the column order of the COPY blocks; 'materials_replace' are rows that
    replace an existing row with the same id."""
    rows = {t: [] for t in ('materials', 'materials_replace', 'pipe_constructions', 'pipe_layers', 'pipes', 'pipe_bundle_types', 'bundle_pipes',
                            'pipe_series', 'pipe_series_pressure_ratings')}
    material_ids = {}
    next_material = ids['material']
    for name, (lam, cp, rho, e, alpha, re, nu) in MATERIALS.items():
        if name in ids['materials']:
            mid, target = ids['materials'][name], 'materials_replace'
        else:
            mid, target, next_material = next_material, 'materials', next_material + 1
        material_ids[name] = mid
        rows[target].append((str(mid), name, _num(lam), _num(cp), _num(rho), _num(e), _num(alpha), _num(re), _num(nu)))
    counters = {key: ids[key] for key in ('construction', 'layer', 'pipe', 'bundle', 'bundle_pipe', 'series', 'rating')}

    def take(key):
        counters[key] += 1
        return counters[key] - 1

    def construction(name, layers):
        cid = take('construction')
        rows['pipe_constructions'].append((str(cid), name))
        for seq, (material, thickness) in enumerate(layers, 1):
            rows['pipe_layers'].append((str(take('layer')), str(cid), str(material_ids[material]), _num(round(thickness, 5)), str(seq)))
        return cid

    def pipeRow(pipe, name, d, s, cid, casing_id, description):
        pid = take('pipe')
        series = None if isUnequal(pipe) else pipe.series
        rows['pipes'].append((str(pid), name, _num(round((d - 2.0 * s) / 1000.0, 5)), _num(pipe.k), str(cid), '\\N', description,
                              series or '\\N', '\\N' if casing_id is None else str(casing_id), '\\N', '\\N', _num(pipe.p_max), 'f',
                              _num(pipe.bend)))
        return pid

    for pipe in PIPES:
        wall = casingWall(pipe.casing)
        short = pipe.name[len('isoplus '):]
        if not isTwin(pipe):
            foam = (pipe.casing - pipe.d1) / 2.0 - wall
            cid = construction('{}: {} x {} mm {}, {} mm PUR flexible foam, {} x {} mm PE-LLD'.format(
                short, _mm(pipe.d1), _mm(pipe.s1), pipe.material, _mm(foam), _mm(pipe.casing), _mm(wall)),
                [(pipe.material, pipe.s1 / 1000.0), ('PUR flexible foam', foam / 1000.0), ('PE-LLD', wall / 1000.0)])
            pipeRow(pipe, pipe.name, pipe.d1, pipe.s1, cid, None, '{}; Da {} mm; casing wall assumed {} mm'.format(SOURCE, _mm(pipe.casing), _mm(wall)))
            continue
        y1, y2, gap = twinGeometry(pipe)
        casing_id = construction('{} twin pipe casing: PUR flexible foam (radius {} mm), {} x {} mm PE-LLD'.format(
            short, _mm(foamRadius(pipe) * 1000.0), _mm(pipe.casing), _mm(wall)),
            [('PUR flexible foam', foamRadius(pipe)), ('PE-LLD', wall / 1000.0)])
        description = '{}; twin pipe, Da {} mm; casing wall {} mm and carriers one above the other with {} mm clearance assumed'.format(
            SOURCE, _mm(pipe.casing), _mm(wall), _mm(gap * 1000.0))
        carriers = [(pipe.d1, pipe.s1)] + ([(pipe.d2, pipe.s2)] if isUnequal(pipe) else [])
        pids = []
        for d, s in carriers:
            cid = construction('{} carrier pipe: {} x {} mm {}'.format(short, _mm(d), _mm(s), pipe.material), [(pipe.material, s / 1000.0)])
            name = pipe.name if len(carriers) == 1 else '{} ({} mm)'.format(pipe.name, _mm(d))
            pids.append(pipeRow(pipe, name, d, s, cid, casing_id, description))
        supply, ret = pids[0], pids[-1]
        bid = take('bundle')
        rows['pipe_bundle_types'].append((str(bid), 'twin pipe {}: pipes: {},{}; {} m depth'.format(pipe.name, supply, ret, _num(TWIN_DEPTH))))
        for seq, pid, y in ((1, supply, y1), (2, ret, y2)):
            rows['bundle_pipes'].append((str(take('bundle_pipe')), str(bid), str(seq), str(pid), '0', _num(round(TWIN_DEPTH + y, 5)), '2'))

    for series in SERIES:
        sid = take('series')
        rows['pipe_series'].append((str(sid), series.name, series.system_type, series.standard, _num(series.t_cont), _num(series.t_peak),
                                    _num(series.t_min), _num(series.sigma), _num(series.safety), series.description))
        for years, temperature, pressure in RATINGS.get(series.name, []):
            rows['pipe_series_pressure_ratings'].append((str(take('rating')), str(sid), _num(years), _num(temperature), _num(pressure)))
    return rows
