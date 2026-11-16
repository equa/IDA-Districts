## Context

Foundation change 1 of 4 for `cost-optimization` (decision record in `openspec/changes/cost-optimization/design.md`,
D6, D8, D9).

Requested outputs are per **project**: `<project>\requestedOutputs.txt`, read by `loadRequestedOutputs`
(`utility_functions/files.py`, fallback `config/requestedOutputs_template.txt`), edited in `RequestedOutputsDialog`
(`ida_mosim_dialog.py`, `RequestedOutputs_dialog.ui`) and written into the IDA templates by
`WorkerSetRequestedOutputs.updateTemplatesOutputs` (`outputs.py`). The templates are per project too:
`<project>\customer_templates\<name>\<name>.idm`, `<project>\energy_plant_templates\...`. A requested output adds
`:VAR … :L "<file>"` entries to a component and an `OUTPUT-FILE` to the template; `load_results.py` reads
`customer_<id>\<file>.prn` into tables such as `customer_s_troom (fid, time, geom, "$troom")`. Code reads keys as
`requestedOutputs['x']`, so a file without a new key fails today.

Templates seen:
- Plugin and IDA samples: `1_simplified_consumer` … `3_…`: one `PUMP` in the building circuit (loadmodel ↔
  `hx_substation` side B), the network side is `Flowmeter2` / `PMT2mux` → `vlv_substation` → `hx_substation` side A.
- `4_simplified_consumer_hp` (`low_temperature_network`): `HP_B2B_substation` (variable `P_el_total` only), `PUMP`,
  `PUMP1`, `dhw_pump_sub` (`PUMPMCTRL`).
- Plants: `PUMP`…`PUMP3` with `PPUMP` (ideal sources, `3_waste heat source`); borehole fields without a `PUMP`.
- Load models (`lM_H_G_L`, `lM_HC_G_L_MCTRL`, `lm_h_g_t_hx`): `TRoom`, one setpoint `TSet_var` and the mode
  `HCMode_var` (heating/cooling), so degree hours of both modes follow from one setpoint.

QGIS 3.44 (Qt5) and 4.2 (Qt6): the new dialog uses `QTableWidget`, `QComboBox`, `QDoubleSpinBox`; enums through
`utility_functions/compat.py`. No DB schema change of the project tables.

## Goals / Non-Goals

**Goals:**
- Know which pumps move network water, automatically, with a visible and editable result.
- Pump electricity per pump and hour as results, for customers and plants.
- Room setpoint and mode next to the room air temperature.

**Non-Goals:**
- Costs, η calibration or the NPV (changes `network-cost-data`, `cost-optimization`).
- Unmet load of source-file customers (calculated by `cost-optimization` from the source file and `power_c`).
- Counting heat pump compressor power; `P_el_total` of a heat pump is listed only when the user adds it.

## Decisions

**D1 – Template graph** (`utility_functions/template_graph.py`). A regex reader of the template `.idm` (component
headers `:N "…" :T …`, the `CONNECTIONS` block `(("A" portA) ("B" portB) …)`). Nodes are (component, side). Only
links between **fluid ports** count (names starting with inlet, outlet, liq, term, evap, cond, or IN/OUT/HXIN/HXOUT,
never …LINK/…SIGNAL): a list of fluid names instead of a list of signal names, because a pump's `TMEASURE` linked
to a controller would otherwise join unrelated circuits. Sides by port name: `liqA…`/`liqB…` (heat exchangers),
`evap…`/`cond…` (heat pumps), `IN`/`OUT` vs. `HXIN n`/`HXOUT n` (tank and coil); all other ports one side.
*Alternative:* a list of pump names per template (no automation; rejected in the explore session).

**D2 – Network pump.** Start nodes are the network connection components of the template (`<bundle>_<seq>_Flowmeter2`,
`PMT2mux_<bundle>_<seq>_<type>_<conn>`); a `PUMP`/`PUMPMCTRL`/`PUMPCIRC` reachable from them is a network pump, with
power variable `PPUMP`. On all plugin templates and the IDA samples this finds the plant pumps, the pressure-holding
pump of `2_topup`, the secondary-network pump of `2_heat exchanger`, and in `4_simplified_consumer_hp` the decentral
`PUMP` (through the evaporator of `HP_B2B_substation`) and `PUMP1` (side A of `hx_cooling_substation`); it skips the
building-circuit pumps, `dhw_pump_sub` and the source-side pump of `3_waste heat source`. `HP_B2B` contains no pump
(only `P_el_total`), so "estimate" entries are added by the user only. Pumps in other `.idm` files of the folder
(macros) are reported, not analysed (the climate, sensor and sf macros of the templates contain none).

**D3 – Pump list.** Entries: feature type (customer / energy plant), template, component, kind (variable /
estimate), power variable, η (estimate only), source (found / added). The dialog **Network pumps**, opened from the
requested outputs dialog, runs the detection on the project's templates, shows the entries, and lets the user add
(component from a combo of the template's components, variable from its variables) and remove entries; removed
found entries are remembered so a new detection does not bring them back. An entry whose component no longer exists in the template is shown greyed with a warning and
skipped when outputs are written. Saved in the project as `<project>\networkPumps.json`, next to the templates
and `requestedOutputs.txt`: the list describes the project's templates and the outputs written into them, so it is
the same for every version.
*Alternative:* per version (T8 of the explore session) – the outputs in the project's templates can follow only one
list, so the last version setting outputs would win.

**D4 – Outputs.** Keys `ppump_c` and `ppump_ep` (checkboxes next to the thermal power). When set,
`updateTemplatesOutputs` adds `:L "PumpPower"` with `:AS "<component>"` to the power variable of each variable entry
of the template (a missing variable is added, e.g. the pressure-holding `PUMP` of `2_topup` lists only `PUMPON`) and
an `OUTPUT-FILE "PumpPower"`; a component no longer listed loses its output; when cleared, all are removed. While
`ppump_*` is set, OK writes the templates again even if unchanged (the pump list may have changed); the output files
are not duplicated. Estimate entries need no IDA output: `load_results.py` calculates per time step
P = ṁ/ρ · max(0, p_out − p_in + Δp_int) / η from the connection files (`mdot_<conn>`, `p_<conn>`; ṁ > 0 flows out of
the feature, so the inflow connection is p_in) and Δp_int (default 20 kPa) and η (default 0.5) of the entry, and
stores it in the same table with kind `estimate`. `mdot_*`/`p_*` of the feature type are switched on with `ppump_*`
when it has an estimate entry. A changed Δp_int or η takes effect when the results are loaded again.
*Alternative:* estimating only in the cost model of `cost-optimization` (empty pump tables for decentral networks,
a second code path). Tables `customer_s_ppump` and
`energy_plant_s_ppump` (fid, pump, kind, time, geom, "$ppump" [W]), one row per pump and time step.
*Alternative:* one column per pump (columns differ between templates; rejected).

**D5 – Setpoint.** With `troom_c`, the load model writes `TSet_var` and `HCMode_var` (if it has them) into the
`TRoom` file as well (`:AS "tset"`, `"hcmode"`); they are loaded into `customer_s_tset` and `customer_s_hcmode`,
shaped like `customer_s_troom` (one table per variable as for the heat balance, the troom layer unchanged); the
`TRoom` columns are read by header, so files of earlier runs still load. While `troom_c` is set, OK writes the
customer templates again, so existing projects get the setpoint without clearing the output. No key of its own: the setpoint is only meaningful with the room
temperature. In the templates `TSet` comes from a thermostat on the schedule `hc_mode` (1 = heating → LOLIMIT 21 °C,
−1 = cooling → HILIMIT 26 °C), so the hourly pair (TSet, HCMode) is enough for the degree hours of
`cost-optimization`: they count only when heating or cooling is needed and not reached – heating mode
max(0, TSet − TRoom), cooling mode max(0, TRoom − TSet), any other mode 0; a room temperature between the heating and
the cooling setpoint counts nothing. The degree hours are calculated in `cost-optimization`, not here.
*Alternatives:* a key `tset_c` (two checkboxes, two files to join); a degree-hour KPI at loading (duplicates the
penalty of `cost-optimization` with its tolerance band and reference run).

**D6 – Old projects.** `loadRequestedOutputs` merges the file over the template's keys, so missing keys are
`False`; `checkSimOutputs` compares with `.get`. A project without `networkPumps.json` runs the detection when the
dialog opens or when `ppump_*` is first written. No `upgrade.py` step: no DB table changes.

## Risks / Trade-offs

- [Unknown port names hide a path] → a pump is then not found; the list is shown and editable, unit tests on every
  template of the plugin and the installed IDA samples.
- [A pump inside a macro file] → reported with a warning naming file and pump; it can be added by hand.
- [Estimate entries depend on η, Δp_int and the `p_*` results] → set per entry, `p_*`/`mdot_*` switched on with the
  setting, rows marked kind `estimate`; `cost-optimization` recalibrates η_eff from the measured pumps.
- [Templates edited in IDA after detection] → the list is checked against the templates whenever outputs are set.

## Open Questions

1. ~~Where is the pump list saved~~ → in the project (D3).
2. ~~Setpoint and mode~~ → part of `troom_c` (D5).
3. ~~Estimate entries~~ → calculated at loading into the pump tables (D4).

No open question remains.
