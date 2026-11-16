## ADDED Requirements

### Requirement: Setpoint and mode with the room air temperature
When the room air temperature of customers (`troom_c`) is requested, writing the outputs SHALL add the setpoint `TSet_var` and the mode `HCMode_var` of the load models (`lM_H_G_L`, `lM_HC_G_L_MCTRL`, `lm_h_g_t_hx`) that have these variables to the output file `TRoom`, and loading the results SHALL store them in the tables `customer_s_tset` (`$tset`) and `customer_s_hcmode` (`$hcmode`), shaped like `customer_s_troom`. Writing the outputs again SHALL NOT duplicate the output file `TRoom`. When `troom_c` is cleared, they SHALL be removed with `TRoom`.

#### Scenario: Room temperature requested
- **WHEN** a customer with the template `1_simplified_consumer` is simulated in January with `troom_c`
- **THEN** `customer_s_troom`, `customer_s_tset` and `customer_s_hcmode` have rows of the same time steps, `$tset` 21 and `$hcmode` 1

#### Scenario: Results of an earlier simulation
- **WHEN** results whose `TRoom` file has only the room temperature are loaded
- **THEN** `customer_s_troom` has its rows, and `customer_s_tset` and `customer_s_hcmode` have none
