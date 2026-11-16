## Context

One iteration of the dynamic pipe sizing (`DynamicPipeSizingDialog.evaluate`) runs
`getCustomerLinePressure` (flow tracing + line data) and `optimizePipeDiameters` once, for the hard-wired pair
supply 1 / return 2:

- `flow_tracing.getCustomerLineMdot(line_mdot_table='line_s_mdot$1')`, `getFeatureConnTables(sup_seq=1, ret_seq=2)`
- `hydraulic_balancing.getLineData(sequences=(1, 2), default_temps=(70.0, 40.0))`
- `getOrCreatePipeBundles` builds a changed line's bundle from the sized sequences only.

The project `hc_network` (version `base1`, network 1) shows the real layout:

| lines | sequences | circuits |
|---|---|---|
| 53 (1640 m) | 1, 3 | heating |
| 32 (1260 m) | 1, 2, 3, 4 | heating + cooling |

Plant (template 2) and 14 customers (template 2) have the connections 1: supply 70 °C, 2: supply 10 °C,
3: return 30 °C, 4: return 18 °C; 30 customers (template 1) have 1: supply 70 °C, 3: return 30 °C.
`public.connections.type` is 1 = supply, 2 = return, `temp` the design temperature. The connection sequences equal
the pipe sequences.

The change must run on QGIS 3.44 (Qt5) and 4.2 (Qt6). The new widget is a `QTableWidget` in the existing dialog;
enum accesses use the scoped form (`QHeaderView.ResizeMode.Stretch`, `Qt.ItemFlag.ItemIsEditable`), which both
PyQt5 and PyQt6 accept, or `utility_functions/compat.py` where it already has a name. No DB schema change, so no
upgrade in `upgrade.py`.

## Goals / Non-Goals

**Goals:**
- Balance every supply/return pair of a network as its own circuit in the same iteration loop.
- Default pairs that are right for `hc_network` and for a plain 1/2 network without user input.
- Keep every pipe of a bundle that the sizing did not change.
- Results per pair in the iteration file, the iteration table and on the map.

**Non-Goals:**
- The pipe diameter layer of the iterations (follow-up change `show-iteration-pipe-diameters`).
- Pairs over other connection type sequences than `conn_type_seq` 1, or connection sequences that differ from the
  pipe sequences.
- Saving the pair table; coupling between circuits (e.g. a common return).

## Decisions

**D1 – Pair table filled from the plant connections, not saved.** On opening and on a network change the
dialog reads the connections (`conn_type_seq` 1) of the templates of the network's energy plants, in `conn_seq`
order, and pairs the k-th supply (`type` 1) with the k-th return (`type` 2). Union over the plants; a sequence
paired differently by two plants, or unequal numbers of supplies and returns, is logged and those connections
give no pair. Columns: supply, return, design temperatures supply/return (all editable; the temperatures are
filled from the connections, editing the sequences of a row clears them because they belong to the suggested
connections; empty → fallback 70/40 °C). The table has a frame and its columns can be resized with the mouse.
The pairs used are written into every iteration file.
*Alternatives:* pairs from the bundles of the lines (cannot tell supply from return); saved in the plugin settings
or the version (project-dependent, can go stale; the dialog saves no other field either).

**D2 – Pair (s, r) maps 1:1 to sequences.** Line results `line_s_mdot$s`, `line_s_temp$s` / `$r`; connections
`conn_seq` s / r of `conn_type_seq` 1 of customers and plants (`getFeatureConnTables(sup_seq=s, ret_seq=r)`).
A line belongs to the pair if its bundle has both s and r.

**D3 – One evaluation per pair, one decision per iteration.** `evaluate` loops over the pairs:
`getCustomerLinePressure(..., pair=(s, r), design_temps=...)` → `optimizePipeDiameters` → per-pair result. The
flow tracing graph (`getNetworkGraph`) is restricted to the lines of the pair, so lines without the pair's pipes
neither carry flow nor connect customers. Each pair has its own critical time, weak point and target. The new
pipes of all pairs are merged per line: `{seq: pipe}` of the current bundle, overwritten by each pair's new
pipes. `changed`, the oscillation state and the outcome are computed from the merged pipes, so the iteration
converges only when no pair changes anything.
*Alternative:* separate iterations per pair (one simulation each) – doubles the simulations although one
simulation already contains every circuit.

**D4 – Bundles keep every sequence.** `getOrCreatePipeBundles` receives the merged full `{seq: pipe_id}` of a
line (D3), searches an existing bundle with exactly these pipes and otherwise creates one with the positions
(x, y, ambient) of the original bundle for every sequence. A twin pipe casing stays with its pipes because the
casing belongs to the pipe (`pipes.casing_construction_id`).

**D5 – Checks.** Before the first simulation (topology and templates only): pair sequences are positive
integers, none used twice, supply ≠ return; per pair at least one line with both sequences, one energy plant and
one customer of the network with connections s and r – otherwise stop with a message naming the pair. Customers
without the connections are skipped for that pair and counted in the log. After loading the results of every
iteration, before the flow tracing: `line_s_mdot$s` and `line_s_temp$s` / `$r` must exist in the version schema,
otherwise stop ("request the line outputs ..."). Single lines without a temperature value use the pair's design
temperatures (70/40 °C if the row has none); the log names the number per pair.

**D6 – Iteration file per pair.**
```
{'iteration', 'started', 'outcome', 'n_changed',
 'pairs': [{'supply': s, 'return': r, 'temps': [t_s, t_r],
            'time', 'cid_weak', 'epid_weak', 'dp_net_weak', 'cid_target', 'dp_target', 'quota', 'spread_sized',
            'n_presized', 'n_balancing_steps', 'n_changed', 'n_customers_skipped',
            'customers': {...as today}, 'lines': {lid: {..., 'pipe', 'pipe_new' of the supply sequence s}}}]}
```
`loadIterations` normalises a file without `pairs` (earlier runs) to one pair 1/2 with its top-level fields,
which is how those runs were computed. c_lid files per pair: `dynamic_sizing_iter<n>_c_lid_<s>_<r>.json` and
`..._c_lid_sized_<s>_<r>.json` (the delete pattern `dynamic_sizing_iter*_c_lid*.json` still matches).

**D7 – Table and map per iteration and pair.** The iteration table gets the column "Pair" (`s/r`) after
"Iteration" and one row per pair; the outcome is repeated in each row of an iteration. Selecting rows shows the
selected (iteration, pair) combinations. Layer tree: *Dynamic pipe sizing* → *Iteration n* → *Pair s/r* → the
three layers of today. The custom property of a layer becomes `"<n>"` plus a second property with the pair, so
`removeSizingLayers(iteration)` still removes a whole iteration. The class bounds are computed per pair over all
iterations, because heating and cooling have different dp and mass flow ranges.

## Risks / Trade-offs

- [The k-th supply / k-th return rule gives wrong pairs for an unusual connection order] → the table is editable,
  the design temperatures shown make a wrong pair visible (e.g. 70 → 18 °C), contradictions are logged.
- [Runs that work today without temperature outputs stop] → clear message naming the missing tables; stated as
  BREAKING in the proposal and in the info text (prerequisites).
- [Flow tracing on a graph restricted to the pair's lines can split the network into parts without a plant] →
  customers in such a part get no dp_net and are skipped for the pair with a log line, as today for customers
  without a supplying plant.
- [Two flow tracings per iteration double that part of the run time] → small against the simulation; the log
  shows the step per pair.
- [Old iteration files are shown as pair 1/2 although a project like `hc_network` was computed wrongly] → they are
  deleted by the next run; the info text says that runs before this version used the pair 1/2.
- [A pair without connections in some customers is balanced on fewer customers than expected] → the count of
  skipped customers per pair is in the log and in the iteration file.

## Migration Plan

No data migration: the pair table is not saved and the DB schema does not change. Iteration files of earlier runs
are read as pair 1/2 (D6). Rollback: revert the commit; iteration files written in the new format are then not
readable by the old code and are deleted by its next run.

## Open Questions

None.
