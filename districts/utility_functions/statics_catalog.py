#isoplus tables used by the pipe statics (change statics-steel-solver); source: isoplus planning manual, 6th
#edition ("PHB chapter/page"), copy only with isoplus' permission, therefore only the values needed here
import bisect

SOURCE_EKO = 'isoplus PHB 7/2'
SOURCE_PAD = 'isoplus PHB 7/9'
SOURCE_MIN_COVER = 'isoplus PHB 9/11'

#steel outer diameter (mm) per DN of the rigid isoplus pipes (PHB 12/4)
DN_OUTER_MM = {20: 26.9, 25: 33.7, 32: 42.4, 40: 48.3, 50: 60.3, 65: 76.1, 80: 88.9, 100: 114.3, 125: 139.7, 150: 168.3,
               200: 219.1, 250: 273.0, 300: 323.9, 350: 355.6, 400: 406.4, 450: 457.2, 500: 508.0, 600: 610.0,
               700: 711.0, 800: 813.0, 900: 914.0, 1000: 1016.0}

#one-time compensator type TC, PN 25: DN -> (maximum travel u_m mm, axial spring rate N/mm, bellows area cm2) (PHB 7/2)
EKO = {20: (50, 176, 9.7), 25: (50, 176, 9.7), 32: (50, 204, 15.1), 40: (50, 177, 16.3), 50: (50, 224, 25.9),
       65: (70, 219, 42.1), 80: (70, 180, 67.8), 100: (80, 212, 109.9), 125: (80, 226, 159.9), 150: (100, 261, 230.5),
       200: (120, 361, 383.9), 250: (120, 362, 594.0), 300: (140, 353, 834.2), 350: (140, 617, 1004.3),
       400: (140, 505, 1310.0), 450: (150, 528, 1656.1), 500: (150, 537, 2042.8), 600: (150, 864, 2937.8)}

#expansion pad: (compression, stress N/mm2) at 20 degC (PHB 7/9); the curve ends at 50 %
PAD_CURVE = ((0.0, 0.0), (0.25, 0.045), (0.50, 0.110))

#minimum cover (m) by traffic class (PHB 9/11); single pipes: upper DN of each column
_COVER_SINGLE_DN = (125, 150, 200, 250, 300, 350, 400, 450, 500, 550, 1000)
_COVER_SINGLE = {'SLW 12': (0.40, 0.40, 0.40, 0.40, 0.40, 0.50, 0.50, 0.50, 0.60, 0.80, 1.00),
                 'SLW 30': (0.40, 0.40, 0.40, 0.40, 0.50, 0.50, 0.50, 0.60, 0.70, 0.90, 1.10),
                 'SLW 60': (0.40, 0.50, 0.50, 0.60, 0.60, 0.60, 0.70, 0.80, 0.90, 1.00, 1.20)}
_COVER_TWIN_DN = (80, 100, 125, 150, 200)
_COVER_TWIN = {'SLW 12': (0.40, 0.40, 0.40, 0.40, 0.40),
               'SLW 30': (0.40, 0.40, 0.40, 0.40, 0.50),
               'SLW 60': (0.40, 0.50, 0.50, 0.60, 0.60)}
#equivalent area load of the traffic classes, kN/m2 (PHB 9/11)
TRAFFIC_CLASSES = (('SLW 12', 6.7), ('SLW 30', 16.7), ('SLW 60', 33.3))


def nominalDiameter(d_outer_m):
    """DN of the rigid isoplus pipe with this steel outer diameter (nearest within 2 mm), else None."""
    d = d_outer_m * 1000.0
    dn = min(DN_OUTER_MM, key=lambda k: abs(DN_OUTER_MM[k] - d))
    return dn if abs(DN_OUTER_MM[dn] - d) <= 2.0 else None


def oneTimeCompensator(dn):
    """(maximum travel m, spring rate N/m, bellows area m2) of the isoplus one-time compensator of this DN, else None."""
    row = EKO.get(dn)
    if row is None:
        return None
    return row[0] / 1000.0, row[1] * 1000.0, row[2] / 1e4


def trafficClass(load_kn_m2):
    """The lightest traffic class whose area load is at least the given load; above SLW 60 still SLW 60."""
    for name, load in TRAFFIC_CLASSES:
        if load_kn_m2 <= load + 1e-9:
            return name
    return TRAFFIC_CLASSES[-1][0]


def minimumCover(dn, twin, load_kn_m2):
    """Minimum cover (m) of PHB 9/11, or None when the DN is outside the table."""
    cls = trafficClass(load_kn_m2)
    limits, values = (_COVER_TWIN_DN, _COVER_TWIN[cls]) if twin else (_COVER_SINGLE_DN, _COVER_SINGLE[cls])
    if dn is None or dn > limits[-1]:
        return None
    return values[bisect.bisect_left(limits, dn)]


def padStrain(stress_n_mm2):
    """Compression of an expansion pad under this pressure; beyond 50 % the last slope of the curve is extended."""
    s = abs(stress_n_mm2)
    for (e0, s0), (e1, s1) in zip(PAD_CURVE, PAD_CURVE[1:]):
        if s <= s1:
            return e0 + (s - s0) * (e1 - e0) / (s1 - s0)
    (e0, s0), (e1, s1) = PAD_CURVE[-2], PAD_CURVE[-1]
    return e1 + (s - s1) * (e1 - e0) / (s1 - s0)
