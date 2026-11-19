## Context

The cost optimization (change cost-optimization) sizes the pipes of one version: per iteration a cost model of the
simulated weeks proposes one-size changes, the version is simulated again and valued with the NPV of the scenario
(change plant-energy-costs: energy per carrier, marginal plant). A child version is a schema copy (`pg_dump`), so its
lines keep their IDs; `public.versionhandling.id_base` names the parent. Each version has its own climate file (table
`climate`; the project's climate-macro.idm holds only the version built last, fixed in representative-periods 2.7).
Decision session of 2026-11-18, T1–T8. Runs on QGIS 3.44 and 4.2; the stage table uses the widgets of
`utility_functions/compat.py`, no Qt5/Qt6 difference beyond them.

## Goals / Non-Goals

**Goals:**
- Size the pipes of a network built in stages for all its stages, valued with the timing of each stage.
- Keep the single-version optimization unchanged when the stage table has one row.

**Non-Goals:**
- Changing the network topology between stages by the optimization (lines are added by the user's stage versions).
- Different representative weeks per stage (T7: one set, weights per stage).
- Removing lines or customers in a later stage (a stage only adds).

## Decisions

**D1 – Stages are versions in a table (T1, T5).** The dialog gets a table "Stages": version and start year per row,
stage 1 in year 0, start years increasing. The plugin checks, with a message per problem, that each stage is a
descendant of the previous one (`id_base` chain) and that every line ID of a stage exists in the later stages. One row
is today's run. *Alternatives:* the version chain of the loaded version (may contain non-stage versions); one version
with an "in operation from year" per feature (a large change of the model build).

**D2 – Coupled ΔNPV (T2, T3).** The cost model is built per stage (its flows, temperatures, pumps, weights). A change of
line l is valued in every stage s containing l: ΔNPV(l) = ΔI(l) discounted to the start of its first stage + Σ_s
Δoperating_s(l) · F_s, F_s the present-value factor of stage s's years. The peak-flow and p_max limits use the maximum
over the stages. A protected line is protected in all stages.

**D3 – NPV by stage years (T6).** Operating costs (pump energy, plant and customer energy, losses, penalties) of stage
s are valued with Σ_{t in stage s} L_g(t)/(1+i)^t. An item's purchase years start at the start year of the stage it
first appears in (replacements and residual value from there). Pumps: stage 1's peak at year 0, an increase of the peak
in a later stage bought at its start year. The NPV terms carry the stage and the years.

**D4 – Iterations over all stages (T4, T8).** An iteration writes the step into every stage version (or its child
version, the dialog's choice "new child version" / "override" applied to all stages), builds and simulates every stage,
and evaluates the summed NPV. 'Set pipes' of an iteration sets all stages. The iteration files hold the state per
stage.

**D5 – Periods and climates (T7).** One set of weeks, chosen on stage 1's climate; the opposite extreme week is added
when a stage has a cooling pair. Each stage simulates the weeks with its own climate file; its weights and coverage are
computed from its climate and saved in its `periods.json`; a stage above the coverage warning is named.

**D6 – Report.** The report lists the stages (versions, years, climates), the NPV per stage and in total, and the terms
with their years.

**D7 – Lines matched by geometry (2026-11-19).** The pipe laying of a network extension in a child version rewrites
all its lines (`TRUNCATE` and insert): lines get new IDs and are split where new customers connect, so matching by ID
fails for the normal workflow. Each line of a later stage is assigned to the line of the previous stage it lies on
(its length covered to 99 % within 0.5 m), back to the stage the line first appears in (its root). The stage check
requires every line of a stage to be covered by lines of the next stage. At the start of a run the segments get the
pipes of their root; a step changes a root and all its segments, the ΔNPV summed over them; the state of each stage is
saved per iteration (the IDs differ) and restores it.

**D8 – Version handling triggers (2026-11-19).** The loaded version's tables have the triggers of the version
handling (`SQL_scripts.txt`): inserts, updates, deletes and truncates are copied by ID into all its descendants
(`get_version_hierarchy`). In the override mode stage 1 is loaded and stage 2 is its descendant, so a pipe written into a
stage-1 line would be copied into the stage-2 line of the same ID, which after a pipe laying may be another line. The
run writes the pipes of each stage explicitly, with the trigger `column_update_trigger` of the written table disabled
during the write (copies made with pg_dump may carry the triggers as well). Re-laying stage 1 after stage 2 exists
truncates stage 2's lines (version handling as before); the stage check reports it.

## Risks / Trade-offs

- [Run time grows with the stages] → the weeks are shared; the parallel weeks run per stage; the annual option stays
  available.
- [A stage version edited after its children were made: line IDs may clash] → the stage check compares the line IDs
  and geometries of the earlier stage in the later ones and refuses a mismatch.
- [The cost model of a late stage dominates the ΔNPV of early lines] → intended: the reason for coupling; the report
  shows the ΔNPV per stage.

## Migration Plan

No schema change. Existing runs (one version) are a stage table with one row; their iteration files stay readable.

## Open Questions

None.
