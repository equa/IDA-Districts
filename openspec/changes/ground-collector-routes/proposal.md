## Why

The ground collector model now exists: the parameter contract, the fit and the Python ground model in the plugin
(change `ground-collector-model`, contract version 2), and the Modelica components `GroundCollector` and
`GroundSurface` in the IDA Districts library GroundMo, validated in IDA Districts against the Python model (within
0.3 %) and the 2D reference. A user still cannot use them: collectors are neither a resource nor a route of the network,
and the model build writes every route as an `FDpipebundle` with a fixed ground temperature. This change brings
collectors into the network: as resources, as routes, in the model build, the costs and the results.

## What Changes

- Collector resources: a new table `public.ground_collectors` in the resources tab (preset and its inputs, loop pipe,
  soil at the collector, surface, default loops and mean fluid temperature, costs, lifetime, the cached RC fit), with
  export and import; each resource has a row in `line_types` linked by `line_types.ground_collector_id`, which the
  resources tab keeps in sync.
- Route type: a line is a collector when its `lines.type` is a line type linked to a collector resource; the existing
  dropdown of `lines.type` lists the collector resources with the line types, no new column on `lines`. Per line
  the number of parallel loops and the mean fluid temperature of the start state (defaults from the resource).
- Model build: a collector line becomes a `GroundCollector` (one pipe of its bundle runs through the loops) with one
  `GroundSurface` bound to the climate macro (`TAIR2`, `TSKY`, `IGlob`); the other pipes of the bundle stay an
  `FDpipebundle`. Fitted ground values from the resource; start values undisturbed or pre-calculated from the mean
  fluid temperature, written as parameters and as the values of the node temperatures.
- RC fit at the model build for every used resource whose stored fit is missing or stale (fingerprint over the
  resource, the project's Kusuda settings and `FIT_VERSION`), cached in the resource; a "Fit" action in the resources
  tab shows the errors and the acceptance. An unaccepted fit stops the build with a message naming the resource.
- Checks before a build: IDA Districts has GroundMo installed with the expected contract version.
- Sizing and cost optimization leave collector lines unchanged; their investment is per trench meter and per loop
  meter of the resource, in place of the pipe and trench costs; operation and lifetime from the resource.
- Results: per collector line inlet and outlet temperature, extracted heat, surface heat, loc and near temperature and
  ice fraction on the map; key figures in the network report and `version_kpis` (trench and loop meters, extracted
  kWh/(m a), lowest outlet temperature, largest ice fraction); collector lines stay out of the pipe heat-loss check.
- Depends on the change `climate-macro-build` (the generated climate macro with `IGlob`), which is applied first.

## Capabilities

### New Capabilities
- `ground-collector-routes`: collector resources and their fit, collector routes in the lines layer, the model build
  with `GroundCollector`/`GroundSurface` and their start values, the checks before a build, costs, and results of
  collector lines.

### Modified Capabilities
None. Pipe sizing and the cost optimization skip collector lines; their existing requirements for ordinary lines stay
as they are.

## Impact

- DB: new table `public.ground_collectors`, new column `public.line_types.ground_collector_id`, and on the version
  table `lines` the columns `n_loops` and `t_mean_init` (empty = the resource's default), created for existing projects
  by `upgrade.py`; the route type itself needs no new column.
- Code: resources tab (`districts.py`, `districts_dialog_base.ui`, `ida_resources.py`, `ida_resources_dialog.py` and the
  two resource `.ui` files), the lines form (`layer_visualization.py`), the model build (`invoke_network.py`,
  `outputs.py`), results (`load_results.py`, `show_on_map.py`, `reports.py`, `version_kpis.py`), economics
  (`network_economics.py`, `cost_model.py`, `cost_model_data.py`, `pipe_losses.py`), sizing (`hydraulic_balancing.py`,
  `pipe_sizing.py`), model checks; the ground modules of change 1 are used unchanged.
- IDA Districts: needs the GroundMo library (contract version 2) installed; the plugin checks it before a build.
- Translations (German) for the new UI texts and messages; README.md, CLAUDE.md.
