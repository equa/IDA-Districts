#parameter contract of the Modelica components GroundCollector and GroundSurface (IDA Districts library), change
#ground-collector-model: the model build (change ground-collector-routes) writes these names, the Python ground model
#(ground_rc.py) reads the ground and surface parameters by them; no QGIS, no DB
from dataclasses import dataclass

#raised whenever a name, unit, shape or meaning changes; the model build refuses an IDA model of another version
CONTRACT_VERSION = 1

PARAMETER = 'parameter'
INPUT = 'input'
OUTPUT = 'output'
PORT = 'port'

SCALAR = 'scalar'
SECTIONS = 'nSections'


@dataclass(frozen=True)
class Entry:
    name: str
    kind: str
    unit: str
    shape: str
    meaning: str
    #True: part of the ground model that exists in Python as well (ground_rc.py); False: Modelica only
    ground: bool = False


COLLECTOR = (
    Entry('liq1', PORT, '', SCALAR, 'fluid connector at the first end of the route (as FDpipebundle)'),
    Entry('liq2', PORT, '', SCALAR, 'fluid connector at the second end of the route (as FDpipebundle)'),
    Entry('surface', PORT, '', SECTIONS, 'heat port of each section to its GroundSurface'),
    Entry('nLoops', PARAMETER, '-', SCALAR, 'parallel loops (trenches) of the route; flows and heat flows times nLoops'),
    Entry('lTrench', PARAMETER, 'm', SCALAR, 'trench length = route length'),
    Entry('nSections', PARAMETER, '-', SCALAR, 'ground sections along the trench (M)'),
    Entry('loopLengthPerM', PARAMETER, 'm/m', SCALAR, 'loop pipe length per trench meter'),
    Entry('dInner', PARAMETER, 'm', SCALAR, 'inner diameter of the loop pipe'),
    Entry('dOuter', PARAMETER, 'm', SCALAR, 'outer diameter of the loop pipe'),
    Entry('lambdaWall', PARAMETER, 'W/(m K)', SCALAR, 'conductivity of the pipe wall'),
    Entry('roughness', PARAMETER, 'm', SCALAR, 'roughness of the pipe wall'),
    Entry('liqType', PARAMETER, '', SCALAR, 'liquid of the loop (as FDpipebundle)'),
    Entry('TFreeze', PARAMETER, 'degC', SCALAR, 'freezing temperature of the liquid'),
    Entry('cTop', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the shallow layer above the coil, per trench meter', True),
    Entry('cTop2', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the layer just above the coil (unfrozen), per trench meter', True),
    Entry('cLoc', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the coil region (unfrozen), per trench meter', True),
    Entry('cNear', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the soil around the coil region (unfrozen), per trench meter', True),
    Entry('cFar', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the soil below and beside the coil (unfrozen), per trench meter', True),
    Entry('cFar2', PARAMETER, 'J/(K m)', SCALAR, 'capacity of the deep soil, per trench meter', True),
    Entry('rSt', PARAMETER, 'K m/W', SCALAR, 'surface port to top node', True),
    Entry('rTt', PARAMETER, 'K m/W', SCALAR, 'top node to top2 node', True),
    Entry('rTn', PARAMETER, 'K m/W', SCALAR, 'top2 node to near node', True),
    Entry('rTf', PARAMETER, 'K m/W', SCALAR, 'top node to far node', True),
    Entry('rLn', PARAMETER, 'K m/W', SCALAR, 'loc node to near node', True),
    Entry('rNf', PARAMETER, 'K m/W', SCALAR, 'near node to far node', True),
    Entry('rFf', PARAMETER, 'K m/W', SCALAR, 'far node to far2 node', True),
    Entry('rFd', PARAMETER, 'K m/W', SCALAR, 'far2 node to the deep boundary', True),
    Entry('rLoc', PARAMETER, 'K m/W', SCALAR, 'pipe wall (outside) to loc node', True),
    Entry('TDeep', PARAMETER, 'degC', SCALAR, 'undisturbed temperature at the lower boundary', True),
    Entry('rhoCSoil', PARAMETER, 'J/(m3 K)', SCALAR, 'volumetric capacity of the unfrozen soil; the latent volume of a '
          'freezing node (loc, near, top2, far) is its capacity / rhoCSoil', True),
    Entry('waterContent', PARAMETER, '-', SCALAR, 'volume fraction of water in the soil', True),
    Entry('TFreezeSoil', PARAMETER, 'degC', SCALAR, 'upper end of the freezing range of the soil water', True),
    Entry('freezeRange', PARAMETER, 'K', SCALAR, 'width of the freezing range (ice fraction linear over it)', True),
    Entry('lambdaFrozenRatio', PARAMETER, '-', SCALAR, 'conductivity frozen/unfrozen; a conductance between two nodes is '
          'multiplied by 1+(ratio-1)*(mean ice of the two, 0 for a node that does not freeze), rLoc with the loc ice', True),
    Entry('TStartTop', PARAMETER, 'degC', SECTIONS, 'start value of the top nodes'),
    Entry('TStartTop2', PARAMETER, 'degC', SECTIONS, 'start value of the top2 nodes (the ice fraction follows)'),
    Entry('TStartLoc', PARAMETER, 'degC', SECTIONS, 'start value of the loc nodes (the ice fraction follows)'),
    Entry('TStartNear', PARAMETER, 'degC', SECTIONS, 'start value of the near nodes (the ice fraction follows)'),
    Entry('TStartFar', PARAMETER, 'degC', SECTIONS, 'start value of the far nodes (the ice fraction follows)'),
    Entry('TStartFar2', PARAMETER, 'degC', SECTIONS, 'start value of the far2 nodes'),
    Entry('TIn', OUTPUT, 'degC', SCALAR, 'temperature of the inflowing liquid'),
    Entry('TOut', OUTPUT, 'degC', SCALAR, 'temperature of the outflowing liquid'),
    Entry('QExtracted', OUTPUT, 'W', SCALAR, 'heat from the ground into the liquid, all loops (positive = extraction)'),
    Entry('QSurface', OUTPUT, 'W', SCALAR, 'heat from the surfaces into the ground, all loops'),
    Entry('TLoc', OUTPUT, 'degC', SECTIONS, 'temperature of the loc nodes'),
    Entry('TNear', OUTPUT, 'degC', SECTIONS, 'temperature of the near nodes'),
    Entry('iceFraction', OUTPUT, '-', SECTIONS, 'ice fraction of the freezing nodes, weighted by their latent volumes'),
)

SURFACE = (
    Entry('ground', PORT, '', SCALAR, 'heat port to the surface port of a GroundCollector section'),
    Entry('albedo', PARAMETER, '-', SCALAR, 'reflected part of the global radiation', True),
    Entry('epsilon', PARAMETER, '-', SCALAR, 'long-wave emissivity of the surface', True),
    Entry('hConv', PARAMETER, 'W/(m2 K)', SCALAR, 'convective heat transfer coefficient to the air', True),
    Entry('dLayer', PARAMETER, 'm', SCALAR, 'thickness of the surface layer', True),
    Entry('rhoCLayer', PARAMETER, 'J/(m3 K)', SCALAR, 'volumetric capacity of the surface layer', True),
    Entry('spacing', PARAMETER, 'm', SCALAR, 'trench spacing = surface width per trench meter', True),
    Entry('TStart', PARAMETER, 'degC', SCALAR, 'start value of the surface layer'),
    Entry('TAir', INPUT, 'degC', SCALAR, 'air temperature (climate_processor TAIR2)'),
    Entry('IGlob', INPUT, 'W/m2', SCALAR, 'global radiation on the horizontal (IDIRNORM*sin(ELEVSUN)+IDIFFHOR)'),
    Entry('TSky', INPUT, 'degC', SCALAR, 'sky temperature (climate_processor TSKY)'),
    Entry('TSurface', OUTPUT, 'degC', SCALAR, 'temperature of the surface layer'),
)

COMPONENTS = {'GroundCollector': COLLECTOR, 'GroundSurface': SURFACE}


def entries(component, kind=None, ground=None):
    """Entries of a component, optionally of one kind and only those (not) in the Python ground model."""
    return [e for e in COMPONENTS[component]
            if (kind is None or e.kind == kind) and (ground is None or e.ground == ground)]


def groundParameterNames():
    """Names of the parameters the Python ground model takes: the ground part of GroundCollector and GroundSurface."""
    return [e.name for c in COMPONENTS for e in entries(c, PARAMETER, True)]


def checkGroundParameters(params):
    """ValueError unless params has exactly the ground parameters of the contract, each a finite number."""
    expected = set(groundParameterNames())
    missing = sorted(expected - set(params))
    extra = sorted(set(params) - expected)
    if missing or extra:
        raise ValueError('ground parameters not as in contract version {}: missing {}, unknown {}'.format(
            CONTRACT_VERSION, missing, extra))
    for name in expected:
        value = params[name]
        if not isinstance(value, (int, float)) or value != value or value in (float('inf'), float('-inf')):
            raise ValueError('ground parameter {} is not a finite number: {!r}'.format(name, value))
