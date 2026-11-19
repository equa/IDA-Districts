## Context

Roadmap T1–T12 (archived change `pipe-series-catalog`, section "Pipe statics roadmap") fixes the statics as a full
EN 13941 / AGFW FW 401 verification with an own solver (T5) on an automatically generated model (T6). This change
builds that model; it calculates nothing.

Inputs that already exist:
- `lines.geom` (LineStringZ, Z = route height), `lines.type` (`line_types`), `lines.pipe_bundle_type_id`;
- `junctions` (types tee, cross, reducer, end_cap, y_connector) and `junction_connections`;
- `bundle_pipes` (sequence, pipe_id, x, y; y is the depth of the pipe centre in m, e.g. 1 in the templates);
- `pipes` with `casing_construction_id` (twin), `series`, `min_bend_radius_m`; `pipe_constructions` /
  `pipe_layers` / `materials` with the mechanical values; `pipe_series` with `system_type`.

The decision session of 2026-11-19 answered the open points of the roadmap for this change (M1–M5).

QGIS versions: 3.44 (Qt5) and 4.2 (Qt6). The change touches PostGIS layer loading and renderers
(`QgsVectorLayer`, `QgsCategorizedSymbolRenderer`); enum access goes through the fully scoped names that both
versions accept, as in `utility_functions/height_check.py`. No `compat.py` helper is needed.

## Goals / Non-Goals

**Goals:**
- A stored, reproducible model per version that both solver changes and `statics-results` read by element id.
- Bend classification by rule, adjustable by parameters and by overrides on the map.
- Overrides that survive a regeneration of the topology.
- A report that names everything the build skipped, could not match or found implausible.

**Non-Goals:**
- Stresses, friction lengths, expansion pads, fatigue, utilisation (solver and result changes).
- Soil and traffic values beyond storing them (they are columns of `statics_sections` and parameters; the solvers
  use them).
- Editing the generated model tables by hand (they are replaced by every build).

## Decisions

### M1 Route geometry shared, one pipe chain per single pipe and per twin
The route is built once per line: nodes at the line's ends and vertices, sections between them. Each pipe of the
bundle gets its own chain over these sections (own outer diameter, wall, casing, cover, offset x). A twin (two
sequences with the same `casing_construction_id`) is one chain with one casing and two carrier pipes, the casing
centre at the midpoint of the two pipes (as `twin_pipe.convertTwinPipes`). The pipes of one bundle are not coupled
through the soil (EN 13941 treats each pipe separately).
*Alternatives:* one element per bundle (wrong for single pipes); geometry only (moves the per-pipe data into the
solver).

### M2 Stored in version tables, with a fingerprint
Tables of the version (created by `DB_versionTablesDefault.txt`, and for existing versions by
`upgrade.upgradeVersionDB` through `statics_db.ensureStaticsTables`):
- `statics_model_nodes` (id, geom POINTZ, line_ids, vertex_index, kind: vertex | junction | end, junction_id,
  junction_type, angle_deg, bend_class, radius_m, bend_id, source: rule | merge | override, override_id, override_kind);
- `statics_model_sections` (id, geom LINESTRINGZ, line_id, node_from, node_to, length_m, line_type, and the values of
  the applied section override);
- `statics_model_pipes` (id, geom: the section offset by x for the map, section_id, line_id, sequences, pipe_ids,
  twin, system_type, series_id, d_inner_m / d_outer_m / wall_m as arrays with one value per carrier pipe, casing_d_m,
  cover_m, x_m, y_m, min_bend_radius_m);
- `statics_model_build` (one row: built_at, fingerprint, report jsonb).

The build deletes and refills the three model tables in one transaction (the connection is in autocommit, so the
build opens an explicit `BEGIN`/`COMMIT`). The fingerprint is an md5 over the ordered inputs: lines (id, geom,
bundle, type), junctions, the used bundle rows, pipes, constructions, layers and materials, the parameters and both
override tables. `statics_db.modelState(cur, schema)` returns missing | current | out of date; the solvers refuse a
model that is not current. A child version gets all tables through the schema copy (`db.copy_schema`).
*Alternatives:* built in memory per run (no stable ids, no view without a build); JSON file (no SQL, no map).

### M3 Bends by angle classes
The angle at a vertex is the 3D angle between the two adjacent segments. Per system type of the chain (from
`pipe_series.system_type`; pipes without a series count as rigid):
- rigid steel (single, twin): angle < `bend_ignore_deg` (1°) → none; ≤ `kink_max_deg` (5°) → small-angle kink;
  larger → prefabricated bend with radius `bend_radius_factor` (1.5) × steel outer diameter;
- flexible and bare plastic: elastic bend; the radius from the geometry is checked against `min_bend_radius_m`
  and reported when it is smaller.

A run of consecutive vertices, each with an angle ≤ `kink_max_deg` and spacing ≤ `merge_distance_m` (5 m), whose
total deflection is ≥ `bend_ignore_deg`, becomes one elastic bend with the radius of the fitted arc
(mean vertex spacing / mean angle per vertex). For steel the run is merged only if that radius is ≥ `elastic_radius_factor`
(1000) × outer diameter; otherwise its vertices stay single kinks and the report names the run. The bend class
lives on the route node, so the bundle's pipes share it: the line counts as rigid when any of its pipes is rigid,
with the largest steel outer diameter for the limits; the radius check runs per pipe.
Vertices at junctions are not bends (the junction type decides). Parameters: `public.statics_parameters`
(id, key unique, value, unit, description; the id because the generic table dialog keys its rows by id), created
with defaults by `upgradeProjectDB`, edited in a table dialog where only the value is editable.
*Alternatives:* every vertex a bend with one radius (small kinks indistinguishable); no merge (a digitised curve
becomes dozens of kinks).

### M4 Overrides by location
`statics_points` (geom POINT, 2D so it can be digitised without heights; kind: fixed_point | compensator | one_time_compensator | valve | bend; bend_class,
radius_m, note) and `statics_sections` (geom LINESTRING; cover_m, soil_unit_weight_kn_m3, friction_angle_deg,
friction_coefficient, groundwater_depth_m, traffic_load_kn_m2, laying_temperature_c, laying_method, note) are
version tables; a build only reads them. At every build:
- a point snaps to the nearest model node within `snap_tolerance_m` (0.5 m); two nodes within the tolerance →
  ambiguous, not applied;
- a section applies to every model section whose midpoint lies within the tolerance of its geometry;
- an override without a match is kept and listed.

An override of the bend class wins over the rule (`source = override`); a cover override wins over
`bundle_pipes.y`. Overrides are stored in the model rows they apply to, so the solvers need not repeat the
matching.
*Alternatives:* by line id and vertex index, or by line id and chainage (both lost when the topology renumbers
lines).

### M5 Layer group "Statics model" from the stored tables
"Build statics model" builds, then loads or refreshes a layer group with: model nodes (categorised by bend class),
model pipes (on their section geometry, offset by x), `statics_points` and `statics_sections` (editable). Renderers
are built in code, like the height check; no `.qml` files. The report opens in a dialog with the lists of M4,
skipped lines (no bundle, pipe without construction, twin that does not fit), negative cover and bends below the
minimum radius. Reloading the version restores the group only on demand (button), not automatically.

### M6 Where the code goes
- `utility_functions/statics_model.py`: pure functions (angles, classification, run merge, arc radius, snapping) on
  plain coordinates, testable without DB or QGIS.
- `utility_functions/statics_db.py`: tables, inputs, build, fingerprint, model state, report.
- `utility_functions/statics_layers.py`: layer group and renderers.
- `districts.py` / `districts_dialog_base.ui`: buttons "Build statics model" and "Statics parameters".

## Risks / Trade-offs

- [The defaults 1°, 5°, 1.5 × Da, 1000 × Da and 5 m are starting values, not checked against AGFW FW 401] →
  all are parameters of the project, shown in the report header; the user checks them before the solver change
  relies on them.
- [A snap tolerance of 0.5 m can attach a point to the wrong vertex where vertices are dense] → ambiguous matches
  are not applied and are listed; the tolerance is a parameter.
- [The stored model goes out of date after any edit of lines, bundles or overrides] → the fingerprint marks it,
  the build dialog and the solvers say so; no silent use.
- [The md5 over all inputs is slow on very large networks] → it hashes ordered SQL aggregates in the DB
  (`md5(string_agg(...))`), not in Python.
- [Templates and old projects have no series for some pipes] → they are treated as rigid and the report names
  them.

## Migration Plan

`upgradeProjectDB` creates `public.statics_parameters` with the defaults; `upgradeVersionDB` creates the version
tables when they are missing. Both run at every version load, so old projects need no manual step. Nothing is
removed; rollback is dropping the new tables.

## Open Questions

None. The default values above are parameters (see Risks).
