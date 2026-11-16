# Handover: IDA Districts sample `dynamic_optimization` (design D12)

For the IDA Districts release that ships the extended sample. The plugin tests skip the low-temperature case until
the installed sample has it.

## Content to add to `<pathDistricts>\Samples\districts\dynamic_optimization`

1. **Customer template** `4_simplified_consumer_hp` from `low_temperature_network` (folder, `.idm`, `.idc`, macros).
   Its decentral network pumps `PUMP` (through the evaporator of `HP_B2B_substation`) and `PUMP1` (side A of
   `hx_cooling_substation`) are found by the network pump detection.
2. **Energy plant templates** `1_ideal_heat_source`, `2_borehole field`, `3_waste heat source`,
   `4_borehole field with ctrl` from `low_temperature_network`, under new template numbers next to `1_ideal_heat_source`
   and `2_topup` of the sample.
3. **A new version `lt1`** (child of `base1`, same lines and customers):
   - customers on `4_simplified_consumer_hp`;
   - plants on the borehole field and the waste heat source;
   - low-temperature plant setpoints (supply about 10–20 °C, return about 5–15 °C, connection table `connections`);
   - no central circulation pump in the plants (the decentral pumps move the water), a pressure-holding plant kept.
4. **Cost data** in `db_tables.sql` of the sample: the pipe columns `maintenance_pct`, `lifetime_a`, `p_max_bar`,
   `example` with the example values of the plugin templates (KWW 2026 Tab 36 material / 2 per pipe, 1 %/a, 40 a,
   16 bar, `example` true). The scenario tables are created by the plugin's upgrade when a version is loaded.
5. **Requested outputs** of the sample (`requestedOutputs.txt`): `ppump_ep`, `ppump_c`, `temp_lines`, `mdot_lines`,
   `qamb_lines`, `temp_ep`, `troom_c`, `power_c` switched on.

## Tests that use it

- `test/test_cost_optimization_annual.py::test_low_temperature_version` (version name: env
  `DISTRICTS_TEST_LT_VERSION`, default `lt1`).
- `test/test_network_pumps.py` reads the installed `low_temperature_network` sample already.
