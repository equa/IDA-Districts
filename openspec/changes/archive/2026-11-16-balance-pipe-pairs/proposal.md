## Why

The dynamic pipe sizing assumes one circuit with supply = pipe sequence 1 and return = sequence 2 (flow tracing on
`line_s_mdot$1`, connections 1/2, line data of the sequences 1 and 2). Networks with several circuits in one trench
do not fit: in the project `hc_network` the heating circuit is the pair 1/3 on all 85 lines and the cooling circuit
the pair 2/4 on 32 of them, so today's run takes the cooling supply as the heating return and the 53 two-pipe lines
have no sequence 2 at all. In addition, a changed line loses every pipe outside 1/2, because the new pipe bundle is
built from the sized sequences only.

## What Changes

- The dialog gets a table of supply/return sequence pairs. It is filled, when the dialog opens and when the
  network changes, from the connections of the network's energy plants: the k-th supply connection with the k-th
  return connection, with their design temperatures. Sequences and temperatures are editable and not saved.
- Each pair is balanced as a separate circuit: its own flow tracing, critical time, weak point, target and pipe
  sizing, on the lines whose bundle has both sequences of the pair, with the customers and plants that have both
  connections of the pair.
- Checks before the first simulation: no sequence twice, supply ≠ return; the run stops if a pair has no energy
  plant or no customer with its connections; customers without them are skipped for that pair (logged).
- **BREAKING**: the run stops when the line temperature results (`line_s_temp$s` / `$r`) of a pair are missing;
  single lines without a value use the pair's design temperatures (logged). Today 70/40 °C are used silently.
- A changed line gets a pipe bundle with the new pipes of all its pairs and the unchanged pipes of all other
  sequences (fixes the loss of the pipes outside 1/2).
- Convergence and oscillation are decided over all pairs together.
- **BREAKING** (file format): the iteration file `dynamic_sizing_iter<n>.json` holds the results per pair;
  files of earlier runs are read as the single pair 1/2.
- The iteration table has one row per iteration and pair (column "Pair"); on the map each iteration subgroup has
  one subgroup per pair with the customer, line and new-pipe layers.
- A network with a single pair 1/2 behaves as before, apart from the temperature check.

## Capabilities

### New Capabilities
- `pipe-pair-balancing`: the pair table and its default from the plant connections, the checks before and during
  the run, the per-pair flow tracing and sizing, the temperature rules and the pipe bundles of changed lines.
- `sizing-iteration-results`: the iteration file per pair (and the reading of older files), the iteration table
  per iteration and pair and the map layers per iteration and pair.

### Modified Capabilities
<!-- none: openspec/specs/ has no spec of the pipe sizing yet -->

## Impact

- `districts/dynamic_pipe_sizing.py` / `.ui`: pair table, checks, loop over the pairs in the evaluation step,
  merged pipes, iteration table with the column "Pair".
- `districts/utility_functions/hydraulic_balancing.py`: `getLineData`, `getCustomerLinePressure`,
  `getOrCreatePipeBundles` per pair / with all sequences.
- `districts/utility_functions/flow_tracing.py`: callers pass the pair (the functions already take the sequences);
  graph restricted to the lines of the pair.
- `districts/utility_functions/dynamic_sizing_results.py`: file format, table rows and layers per pair.
- Translations (messages, info text `dynamic_pipe_sizing_info`, de/en compiled); tests in `districts/test`.
- No change to the project DB schema.
