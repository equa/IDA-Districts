## Why

The cost optimization (change `cost-optimization`, design D6, D8, D9) needs the electricity of the pumps that move
network water, per pump and per hour, and the room setpoints of the load models. Neither is an output today:
`power_c`/`power_ep` are thermal powers, nobody requests `PPUMP` of the IDA `PUMP`, and only `TRoom` of the load
models is written. Which pumps move network water is not known either: the customer templates have pumps in the
building circuit, while the low-temperature sample's heat pump customer has decentral pumps that push network water
through the evaporator.

## What Changes

- Automatic detection of the **network pumps** in the IDA templates of energy plants and customers: a pump
  component in the flow path between the template's network connections, with no heat exchanger in between.
- A dialog **Network pumps** (from the requested outputs dialog) lists the found entries per template (template,
  component, power variable) and lets the user add and remove entries, including components that contain a pump.
  An entry without a power variable of its own is marked "estimate": its pump power is calculated from the
  connection's mass flow and pressure difference and an efficiency η of the entry.
- New requested outputs **pump power of customers** (`ppump_c`) and **pump power of energy plants**
  (`ppump_ep`): the power variable of every listed entry, hourly, loaded into a result table per feature type
  with one row per pump and time step.
- The room setpoint (`TSet_var`) and the heating/cooling mode (`HCMode_var`) of the load models are written with
  the room air temperature output and loaded into `customer_s_tset` and `customer_s_hcmode`.
- Requested outputs files of existing projects without the new keys are read with the new outputs switched off.

## Capabilities

### New Capabilities
- `network-pump-detection`: detection of network pumps in plant and customer templates, the editable list and
  where it is saved.
- `pump-power-outputs`: the requested outputs `ppump_c`/`ppump_ep`, their output files, result tables and the
  estimate of entries without a power variable.
- `room-setpoint-output`: setpoint and heating/cooling mode of the load models with the room air temperature.

### Modified Capabilities
<!-- none: the requested outputs have no spec yet -->

## Impact

- `districts/outputs.py` (`updateTemplatesOutputs`, output files in the templates), `RequestedOutputs_dialog.ui`
  and `ida_mosim_dialog.py`, `ida_mosim.py` (`checkSimOutputs`), `config/requestedOutputs_template.txt`,
  `templates/*/requestedOutputs.txt`, `utility_functions/files.py` (`loadRequestedOutputs` with defaults).
- `districts/load_results.py`: tables `customer_s_ppump`, `energy_plant_s_ppump`, columns of `customer_s_troom`.
- New module for the template graph and pump detection (pure Python on the `.idm` files), new dialog.
- Translations, unit tests on the `.idm` files of the plugin templates and the installed IDA samples
  (`low_temperature_network`), an e2e test with IDA.
- No DB schema change of the project tables; result tables are created per run as today.
