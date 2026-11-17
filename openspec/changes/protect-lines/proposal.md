## Why

The dynamic pipe sizing may change the pipes of every line of a pair. Existing or already built sections, or
lines with planned reserve capacity, must keep their pipes; today the only way is to fix them by hand after
every run.

## What Changes

- The group "Hydraulic balancing of the customers" of the dynamic pipe sizing dialog gets a list "Protected
  lines" of line IDs, with the buttons "+" (empty editable entry), "−" (remove the selected entries) and
  "Add selected lines" (the selected features of the version's `lines` layer).
- A protected line keeps its pipes in every pair and every iteration: no pre-sizing, no enlargement for the
  max. specific pressure loss, no reduction in the balancing. Its pressure loss still counts for the
  customers it supplies.
- A protected line whose pipes exceed the max. specific pressure loss is reported in the log per pair.
- The list is saved per version in the version folder (`dynamic_sizing_protected_lines.json`) at the start
  and read when the dialog opens; a child version gets it with the copied version folder.
- At the start, an entry that is not a positive integer stops the run with a message naming it; IDs that are
  no line of the selected network are logged and ignored.
- The iteration file marks the protected lines and states their number per pair; the log states it as well.

## Capabilities

### New Capabilities
- `protected-lines`: protected line list of the dynamic pipe sizing — editing, saving per version, checks,
  and keeping the pipes of the protected lines in the sizing and balancing.

### Modified Capabilities
<!-- none: the pair balancing and the iteration results keep their requirements; the protection is added on top -->

## Impact

- `districts/dynamic_pipe_sizing.py` (list widget and buttons, parameters, check, save/load, log),
  `districts/dynamic_pipe_sizing.ui` unchanged (widgets added in code like the pair table).
- `districts/utility_functions/hydraulic_balancing.py`: `optimizePipeDiameters` gets a `protected` set.
- `districts/utility_functions/dynamic_sizing_results.py`: `pairSummary` marks protected lines.
- Translations (de/en), info text `dynamic_pipe_sizing_info`.
- No DB schema change, no upgrade step.
