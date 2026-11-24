#generic geometry of a ground collector per trench meter, its presets, soil and surface properties
#(change ground-collector-model, design G2-G4); plain Python, no QGIS, no DB
import math
from dataclasses import dataclass

#smallest grid cell of the 2D reference; thinner source regions are widened to it
MIN_CELL_M = 0.05
#grid cell at a resolved pipe (bare pipe): fine enough that its heat flow no longer depends on the grid by more
#than about 1 %
PIPE_CELL_M = 0.01
#a square of side r_o / 0.5902 has the steady conduction resistance of a circle of radius r_o
SQUARE_PER_RADIUS = 1 / 0.5902
#wall-to-cell resistance of a resolved pipe: the wall temperature acts directly on the pipe's cells
RESOLVED_R_LOC = 1e-5

LATENT_HEAT_J7KG = 334000.0
RHO_WATER_KG7M3 = 1000.0


@dataclass(frozen=True)
class CollectorGeometry:
    spacing_m: float            # trench spacing = width of the cell of one loop
    source_width_m: float
    source_height_m: float
    source_depth_m: float       # depth of the source region's centre
    loop_length_per_m: float    # loop pipe per trench meter
    pipe_d_inner_m: float
    pipe_d_outer_m: float
    pipe_lambda_w7mk: float
    local_spacing_m: float      # distance between neighbouring pipe passes inside the region (design G6)
    preset: str = ''
    preset_inputs: tuple = ()   # ((name, value), ...) of the preset, kept for display
    pipe_resolved: bool = False # the source region is the pipe itself (bare pipe): fine grid, wall on its cells

    @property
    def source_top_m(self):
        return self.source_depth_m - self.source_height_m / 2

    @property
    def source_bottom_m(self):
        return self.source_depth_m + self.source_height_m / 2


@dataclass(frozen=True)
class SoilProperties:
    lambda_w7mk: float = 1.5
    rho_c_j7m3k: float = 2.2e6
    water_content: float = 0.25
    t_freeze_c: float = 0.0
    freeze_range_k: float = 1.0
    lambda_frozen_ratio: float = 1.0
    t_mean_surface_c: float = 9.0       # mean of the undisturbed annual wave at the surface
    amplitude_surface_k: float = 10.0
    phase_day: float = 15.0             # day of the year of the coldest surface
    geothermal_gradient_k7m: float = 0.025
    depth_deep_m: float = 15.0

    @property
    def latent_j7m3(self):
        return self.water_content * RHO_WATER_KG7M3 * LATENT_HEAT_J7KG

    @property
    def diffusivity_m27day(self):
        return self.lambda_w7mk / self.rho_c_j7m3k * 86400.0


@dataclass(frozen=True)
class SurfaceProperties:
    albedo: float = 0.25
    epsilon: float = 0.95
    h_conv_w7m2k: float = 10.0
    d_layer_m: float = 0.05
    rho_c_j7m3k: float = 2.2e6


def undisturbedTemperature(soil, depth_m, day):
    """Undisturbed ground temperature (Kusuda) at depth_m on day (day of year, may be fractional or beyond 365)."""
    a = soil.diffusivity_m27day
    damping = math.sqrt(math.pi / (365.0 * a))
    return (soil.t_mean_surface_c + soil.geothermal_gradient_k7m * depth_m
            - soil.amplitude_surface_k * math.exp(-depth_m * damping)
            * math.cos(2 * math.pi / 365.0 * (day - soil.phase_day - depth_m / 2 * math.sqrt(365.0 / (math.pi * a)))))


def deepTemperature(soil):
    """Temperature of the lower boundary: the annual wave has died out there."""
    return soil.t_mean_surface_c + soil.geothermal_gradient_k7m * soil.depth_deep_m


def nodeDepths(geometry, soil):
    """Representative depths (top, loc, near, far, top2, far2) of the RC nodes, for the undisturbed start state."""
    top, bottom, deep = geometry.source_top_m, geometry.source_bottom_m, soil.depth_deep_m
    return (top / 4, geometry.source_depth_m, geometry.source_depth_m, min(bottom + 1.5, (bottom + deep) / 2),
            top * 0.75, (bottom + deep) / 2)


def _positive(**values):
    for name, value in values.items():
        if not (isinstance(value, (int, float)) and value > 0 and math.isfinite(value)):
            raise ValueError('{} must be a positive number, not {!r}'.format(name, value))


def _make(preset, inputs, spacing, width, height, depth, loop_length, d_inner, d_outer, lambda_pipe, soil=None,
          pipe_resolved=False):
    if d_inner >= d_outer:
        raise ValueError('pipe inner diameter {} must be below the outer diameter {}'.format(d_inner, d_outer))
    _positive(loop_length_per_m=loop_length)
    smallest = PIPE_CELL_M if pipe_resolved else MIN_CELL_M
    #the distance between neighbouring pipe passes follows from the pipe density in the region, not from the pitch:
    #with the pitch, sparse coils got a far too large R_loc (2D 30 % below a validated 3D model, design G6)
    local_spacing = max(width, height) / loop_length
    width, height = max(width, smallest), max(height, smallest)
    geometry = CollectorGeometry(spacing, width, height, depth, loop_length, d_inner, d_outer, lambda_pipe,
                                 local_spacing, preset, tuple(inputs.items()), pipe_resolved)
    checkGeometry(geometry, soil or SoilProperties())
    return geometry


def checkGeometry(geometry, soil):
    """ValueError when the source region does not lie inside the cell, below the surface and above the lower boundary."""
    g = geometry
    _positive(spacing_m=g.spacing_m, source_width_m=g.source_width_m, source_height_m=g.source_height_m,
              source_depth_m=g.source_depth_m, loop_length_per_m=g.loop_length_per_m, pipe_d_inner_m=g.pipe_d_inner_m,
              pipe_d_outer_m=g.pipe_d_outer_m, pipe_lambda_w7mk=g.pipe_lambda_w7mk, local_spacing_m=g.local_spacing_m)
    if g.source_width_m > g.spacing_m:
        raise ValueError('source region ({} m wide) is wider than the trench spacing ({} m)'.format(
            g.source_width_m, g.spacing_m))
    if g.source_top_m < MIN_CELL_M:
        raise ValueError('source region reaches the surface: top at {:.3f} m depth'.format(g.source_top_m))
    if g.source_bottom_m > soil.depth_deep_m - 1.0:
        raise ValueError('source region reaches the lower boundary: bottom at {:.3f} m, boundary at {} m'.format(
            g.source_bottom_m, soil.depth_deep_m))


def horizontalRing(ring_diameter_m, pitch_m, depth_m, spacing_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk,
                   soil=None):
    """Rings lying flat in the trench: region D wide and one pipe high; no return pipe (it is a route of its own)."""
    _positive(ring_diameter_m=ring_diameter_m, pitch_m=pitch_m)
    inputs = dict(ring_diameter_m=ring_diameter_m, pitch_m=pitch_m, depth_m=depth_m, spacing_m=spacing_m)
    return _make('horizontal_ring', inputs, spacing_m, ring_diameter_m, pipe_d_outer_m, depth_m,
                 math.pi * ring_diameter_m / pitch_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk, soil)


def verticalRing(ring_diameter_m, pitch_m, depth_m, spacing_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk,
                 soil=None):
    """Rings standing in the trench, depth_m = depth of the ring centre: region one pipe wide and D high."""
    _positive(ring_diameter_m=ring_diameter_m, pitch_m=pitch_m)
    inputs = dict(ring_diameter_m=ring_diameter_m, pitch_m=pitch_m, depth_m=depth_m, spacing_m=spacing_m)
    return _make('vertical_ring', inputs, spacing_m, pipe_d_outer_m, ring_diameter_m, depth_m,
                 math.pi * ring_diameter_m / pitch_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk, soil)


def flatMeander(layer_width_m, pipe_spacing_m, depth_m, spacing_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk,
                soil=None):
    """Pipe laid back and forth across a layer of the given width."""
    _positive(layer_width_m=layer_width_m, pipe_spacing_m=pipe_spacing_m)
    inputs = dict(layer_width_m=layer_width_m, pipe_spacing_m=pipe_spacing_m, depth_m=depth_m, spacing_m=spacing_m)
    return _make('flat_meander', inputs, spacing_m, layer_width_m, pipe_d_outer_m, depth_m,
                 layer_width_m / pipe_spacing_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk, soil)


def barePipe(depth_m, spacing_m, pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk, soil=None):
    """A single straight pipe without insulation; spacing_m large for a trench without neighbours."""
    inputs = dict(depth_m=depth_m, spacing_m=spacing_m)
    #the region is the pipe itself, resolved in the reference: a single coarse cell would make its temperature
    #depend on the grid
    side = pipe_d_outer_m / 2 * SQUARE_PER_RADIUS
    return _make('bare_pipe', inputs, spacing_m, side, side, depth_m, 1.0,
                 pipe_d_inner_m, pipe_d_outer_m, pipe_lambda_w7mk, soil, pipe_resolved=True)


PRESETS = {
    'horizontal_ring': horizontalRing,
    'vertical_ring': verticalRing,
    'flat_meander': flatMeander,
    'bare_pipe': barePipe,
}


def localResistance(geometry, soil):
    """R_loc [K m/W] per trench meter from the outer pipe wall to the region's mean temperature (design G6): couples
    the wall to the region in the reference and starts the fit. A resolved pipe has none."""
    if geometry.pipe_resolved:
        return RESOLVED_R_LOC
    r_o = geometry.pipe_d_outer_m / 2
    r_eq = max(geometry.local_spacing_m / math.pi, 1.5 * r_o)
    return math.log(r_eq / r_o) / (2 * math.pi * soil.lambda_w7mk * geometry.loop_length_per_m)


def wallResistance(geometry):
    """Conduction resistance of the pipe wall [K m/W] per trench meter."""
    return (math.log(geometry.pipe_d_outer_m / geometry.pipe_d_inner_m)
            / (2 * math.pi * geometry.pipe_lambda_w7mk * geometry.loop_length_per_m))
