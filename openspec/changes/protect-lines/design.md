## Context

`optimizePipeDiameters` (`utility_functions/hydraulic_balancing.py`) changes the pipes of a line in three
places: the pre-sizing to `dp_spez_setpoint` (`presizePipes`), the enlargement of lines above `dp_spez_max`
(also `presizePipes`) and the stepwise reduction of the balancing. It already keeps the lines of the weak point
customer out of the reduction (`lids_weak`). It is called once per pair and iteration from
`DynamicPipeSizingRun.evaluatePair`; the merged pipes of all pairs are written to the lines.

The load-results dialog has the pattern of an ID list (`ida_rv.py`: `addID`, `addSelectedIDs` with an editable
`QListWidget` and the selected features of the `lines` layer). The dynamic pipe sizing dialog adds its own
widgets in code (pair table, periods), the `.ui` file stays unchanged.

`createChildVersion` copies the version folder (`copyVersionFiles`), so a file there follows a child version.

QGIS 3.44 (Qt5) and 4.2 (Qt6): `QListWidget`, `QPushButton` and the editable item flag through
`dialog.qt_item_flag`, as in `ida_rv.py`. No DB schema change, no `upgrade.py` step.

## Goals / Non-Goals

**Goals:**
- Lines chosen by ID or on the map keep their pipes in every pair and iteration of the dynamic pipe sizing.
- The list survives the reference run, the sizing in a child version and closing the dialog after a start.

**Non-Goals:**
- Protecting a line for one pair only, or allowing only enlargements (decided: a protected line keeps all
  its pipes).
- A `protected` attribute on the lines in the DB or a map layer of the protected lines.
- Protection in other sizing tools (static pipe sizing).

## Decisions

**D1 – Protection inside `optimizePipeDiameters`.** New argument `protected` (set of line IDs, default empty).
The protected lines are removed from the lines passed to both `presizePipes` calls and are skipped in the
reduction loop like `lids_weak`. Their `dp_spez` and length stay in the customers' `dp`, so the balancing of the
other lines accounts for them. The result gets `'protected'` (protected lines of the pair) and
`'protected_over_max'` (protected lines whose peak specific pressure loss exceeds `dp_spez_max`).
*Alternative:* resetting the protected lines in `mergePairPipes` after the sizing – the customers' estimated dp
would then be wrong, and the balancing would rely on reductions that are undone.

**D2 – List widget in the balancing group.** A `QListWidget` `list_protectedLines` with editable entries and the
buttons "+", "−" and "Add selected lines", inserted into `formLayout_balancing` with the label "Protected lines".
"Add selected lines" takes the selected features of the active layer if it is the `lines` layer, otherwise of
the project's layer named `lines` (translated name as in `ida_rv.py`); IDs already in the list are not added
again; without a lines layer or selection a message bar info is shown.

**D3 – Saved per version as JSON.** `versions/<version>/dynamic_sizing_protected_lines.json` holds
`{"lines": [ids]}`. It is read in `fillCombos` (missing or unreadable file → empty list, the error in the QGIS
log) and written in `start` after the checks, before a child version is created, so the copy carries it. Only
valid integers are written.
*Alternative:* a DB column `lines.protected` – visible on the map, but a schema change with an upgrade step and
a side effect on other tools.

**D4 – Checks at the start.** An entry that is not a positive integer stops the start with a message naming the
entries (translated). IDs that are no line of the selected network are written to the log once and dropped
from the run's `protected` set; they stay in the list and the file (they can belong to another network of the
version).

**D5 – Reporting.** Per pair the log states the number of protected lines of the pair and, if any, the IDs of
protected lines above `dp_spez_max`. `pairSummary` gets `'n_protected'` and the line rows `'protected': true`;
older iteration files without these keys are read as 0 / false.

## Risks / Trade-offs

- [A protected line is undersized and limits the customers behind it] → logged per pair with the line IDs
  (D5); the user decides.
- [All lines of a customer protected: the customer cannot be balanced] → it is blocked like any customer
  without a feasible line and lowers the quota; visible in the iteration table.
- [Line IDs change when the network is rebuilt from scratch] → IDs not in the network are logged (D4).
- [The list is lost when the dialog is closed without a start] → accepted; it is saved at every start.

## Open Questions

None.
