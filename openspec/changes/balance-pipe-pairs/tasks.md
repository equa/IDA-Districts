## 1. Reproduce the bundle loss

- [x] 1.1 Reproduce that a line with a four-pipe bundle loses the pipes 3 and 4 when `getOrCreatePipeBundles` changes its pipes 1/2 (fake cursor), and unit tests of the pure `planPipeBundles` in test_pipe_pairs.py

## 2. Pairs and checks

- [x] 2.1 `suggestPairs` (hydraulic_balancing.py): pairs and design temperatures from the plant connection rows (k-th supply with k-th return, union over plants, contradictions and unequal counts reported)
- [x] 2.2 Query of the connection rows of the network's energy plants (`conn_type_seq` 1, `connections.type`, `temp`) for `suggestPairs`
- [x] 2.3 `checkPairs`: positive integers, no sequence twice, supply ≠ return; per pair a line with both sequences, a plant and a customer with connections s/r; count of skipped customers per pair
- [x] 2.4 Check of the result tables `line_s_mdot$s`, `line_s_temp$s` / `$r` per pair in the version schema

## 3. Balancing per pair

- [x] 3.1 `getLineData`: lines whose bundle has both sequences of the pair, fallback to the pair's design temperatures, count of lines using it
- [x] 3.2 `getCustomerLinePressure`: pair and design temperatures as parameters, flow tracing with `line_s_mdot$s`, connections s/r and the graph restricted to the pair's lines
- [x] 3.3 `getOrCreatePipeBundles` with the full `{seq: pipe_id}` of a line: unchanged sequences kept, positions of the current bundle for every sequence
- [x] 3.4 `evaluate`: loop over the pairs, merge of the new pipes per line, outcome from the merged pipes, log per pair (weak point, quota, skipped customers, temperature fallbacks)

## 4. Dialog

- [x] 4.1 Pair table in the group Network (created in dynamic_pipe_sizing.py beside the .ui: supply, return and design temperatures editable, frame, columns resizable with the mouse; + / − buttons), Qt5/Qt6-compatible enums
- [x] 4.2 Fill the table on opening and on a network change (`suggestPairs`), clear a row's temperatures when its sequences are edited
- [x] 4.3 `checkPairs` before the first simulation and the result table check after loading the results; stop with a message naming the pair or table

## 5. Iteration results

- [x] 5.1 `iterationSummary` / `saveIteration` with the list `pairs` (supply, return, temps, results per pair, skipped customers), c_lid files `_c_lid_<s>_<r>.json` / `_c_lid_sized_<s>_<r>.json`
- [x] 5.2 `loadIterations` reads a file without `pairs` as the single pair 1/2
- [x] 5.3 Iteration table: column "Pair", one row per iteration and pair, selection as (iteration, pair)
- [x] 5.4 Map: subgroup "Pair s/r" in each iteration subgroup, class bounds per pair over all iterations, `removeSizingLayers(iteration)` removes all pairs

## 6. Tests

- [x] 6.1 Unit tests of `suggestPairs`: hc_network connections → 1/3 (70/30) and 2/4 (10/18), single pair 1/2, contradiction, unequal counts
- [x] 6.2 Unit tests of `checkPairs`: sequence twice, supply = return, pair without plant, without customer, without line; skipped customers counted
- [x] 6.3 Unit tests of the merge of the pair pipes and the outcome (only one pair changes → changed; no pair changes → converged; repeat → oscillation)
- [x] 6.4 Unit tests of `loadIterations` (file without `pairs` → pair 1/2) and of the table rows per pair
- [x] 6.5 e2e tests against the project hc_network (DISTRICTS_TEST_PAIRS_PROJECT, skipped if missing): pair suggestion 1/3 and 2/4, checks with skipped heating-only customers, lines of the pair 2/4 = the 4-pipe lines
- [x] 6.6 e2e test of the result table check: missing `line_s_temp$r` stops with its name
- [x] 6.8 e2e + ida test test_hc_network_sizing.py: project from the IDA Districts sample hc_network, build, simulate, load results, dynamic pipe sizing in a child version (pairs 1/3 and 2/4 suggested, iteration files, table rows and layers per pair, heating-only customers skipped in 2/4, every line keeps its number of pipes); the sizing part moved to test_dynamic_optimization.py in the change sizing-simulation-period
- [ ] 6.7 Regression: existing tests of test_dynamic_pipe_sizing.py pass with the single pair 1/2

## 7. Translations and documentation

- [x] 7.1 tr_msg with German translation for the new messages, the column "Pair" and the subgroup "Pair {}"; translations de/en compiled
- [x] 7.2 Info text `dynamic_pipe_sizing_info` (en/de): pair table and its default, checks, per-pair balancing, required line temperatures, iteration table and map per pair, earlier runs read as pair 1/2
- [x] 7.3 Module doc of dynamic_sizing_results.py with the new file format
- [x] 7.4 README.md and CLAUDE.md: no command or file path of them changed (checked)

## 8. Validation

- [x] 8.1 From districts/, the QGIS Python runs `-m pytest -m "not ida"` and it passes, including test_static_mypy.py and test_messages.py
- [x] 8.2 `npx openspec validate --all` passes
- [x] 8.3 Commit code and artifacts, `git pull --rebase`, push to dev and watch the plugin-tests run (`gh run watch`) until both QGIS jobs pass
- [ ] 8.4 Manual run in QGIS on hc_network (with line mass flow and temperature outputs requested): pairs 1/3 and 2/4 suggested, both balanced, layers per pair
