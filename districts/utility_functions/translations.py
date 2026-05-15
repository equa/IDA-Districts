from qgis.PyQt.QtCore import QCoreApplication

def tr(context,key):
    return QCoreApplication.translate(context, key)
    
def _register_translation_keys():
    #general
    tr("description")
    tr("invoked_features")
    tr("prn_results")
    tr("db_results")
    tr("select_directory")
    tr("select_file")
    tr("variables")
    tr("alias")
    tr("sequence")
    tr("name")
    tr("networks")
    tr("templates")
    tr("ids")
    
    #project
    tr("project")
    tr("version")
    
    #apply functions
    tr("min")
    tr("max")
    tr("average")
    tr("add")
    tr("same_signal")
    tr("individual_signals")
    
    #feature types
    tr("customer")
    tr("line")
    tr("energy_plant")
    tr("customers")
    tr("lines")
    tr("junctions")
    tr("energy_plants")
    tr("supervisory")
    tr("buildings")
    tr("streets")
    
    #pipe ambient
    tr("ambient_air")
    tr("ground")
    tr("duct")

    #sensor target
    tr("custom")
    tr("hcmode")

    #measure
    tr("temperature")
    tr("pressure")
    tr("mass_flow")
    tr("power")
    tr("custom")

    #prefered_conn_dir
    tr("supply")
    tr("return")
    tr("Zone_sup_hot")
    tr("Zone_rtn_hot")
    tr("Zone_sup_cold")
    tr("Zone_ret_cold")
    tr("AHU_sup_hot")
    tr("AHU_rtn_hot")
    tr("AHU_sup_cold")
    tr("AHU_rtn_cold")
    
    #dropdown 
    tr("check_all_items")
    
    #kpi
    tr("tsup_mean_ep")
    tr("tsup_max_ep")
    tr("tsup_min_ep")
    tr("tret_mean_ep")
    tr("tret_max_ep")
    tr("tret_min_ep")
    tr("qsup_heat_ep")
    tr("qsup_cold_ep")
    tr("qsup_ep")
    
    tr("tsup_mean_c")
    tr("tsup_max_c")
    tr("tsup_min_c")
    tr("tret_mean_c")
    tr("tret_max_c")
    tr("tret_min_c")
    tr("qsup_heat_c")
    tr("qsup_cold_c")
    tr("qsup_c")
    
    tr("qamb")
    tr("volume")
    
    tr("qsup_heat_spec_c")
    tr("qsup_cold_spec_c")
    tr("qsup_spec_c")

    tr("qsup_heat_density_c")
    tr("qsup_cold_density_c")
    tr("qsup_density_c")

    tr("qsup_heat_linedensity_c")
    tr("qsup_cold_linedensity_c")
    tr("qsup_linedensity_c")
    
    tr("eff_width")
    
    #tables
    tr("unit")
    tr("value")
    tr("kpi")
    tr("length")
    tr("innerdiameter")
    tr("pipe")
    tr("costs")
    
    #headers
    tr("pipe_info_titel")
    tr("network")
    tr("map_plots")
    
    #fields 
    tr("id")
    tr("template")
    tr("network")
    tr("submodel")
    tr("load_w")
    tr("gfa_m2")
    tr("type")
    tr("pipe_bundle_type_id")
    tr("zeta")
    tr("n_connections")
    tr("length_m")
    tr("costs_eur7m")
    tr("b_id")
    tr("z_id")
    tr("substation_id")
    tr("z_bh_m")
    tr("z_height_m")
    
    #groups
    tr("general")
    tr("physical_data")
    tr("simulation_data")
    tr("meta_data")
    
    #layer categories
    tr("unkown")
    #junctions
    tr("cross")
    tr("end_cap")
    tr("reducer")
    tr("tee")
    tr("y_connector")
    #lines
    tr("service_pipe")
    tr("distribution_pipe")
    tr("transmission_pipe")
    tr("station_pipe")
    tr("customer_pipe")
    #customers
    tr("simplified_consumer")
    tr("simplified_consumer_2sup_2ret")
    tr("simplified_consumer_2sup_1ret")
    tr("simplified_consumer_hp")
    #energy_plants
    tr("ideal_heat_source")
    tr("ideal_cooling_source")
    tr("ideal_heat_cooling_source_2sup_2ret")
    tr("ideal_heat_cooling_source_2sup_1ret")
    
    #buttons
    tr("set_load_attribute")
    tr("set_gfa_attribute")
    tr("customer_data_sheet")
    tr("disconnect")
    tr("import")
    tr("cancel")
    tr("create")
    tr("ok")
    tr("add_btn")
    tr("delete")
    tr("save")
    tr("reject")
    tr("start")
    tr("pause_resume")
    tr("stop")
    tr("connect")
    
    #templates
    tr("empty_project")
    tr("heating_network")
    tr("db_default_values")
    tr("low_temperature_network")
    
    #descriptions
    tr("description_importPRNData")
    tr("description_importLineFeature")
    tr("description_importFeaturePoint")
    
    #pipe sizing dialog
    tr("pipe_sizing")
    tr("select_considered_pipes")
    tr("supply_temperature")
    tr("return_temperature")
    tr("load_column")
    tr("consider_the_simultaneity_of_energy_consumption")
    tr("lines_energy_demand")
    tr("sizing_according_to_customers_energy_demand_and_shortest_path_from_customer_to_main_energy_plant")
    tr("main_energy_plant")
    tr("kinematic_viscosity")
    tr("ambient_mapping")
    tr("dp_specific")
    tr("liquid_circuits")
    tr("select_considerable_pipes_per_sequence")

    #pipe laying algroithm dialog
    tr("pipe_laying_algorithm")
    tr("generate_heating_network")
    tr("lines_template")
    tr("type_settings_for_heating_and_cooling")
    tr("extend_existing_network")
    tr("amortization_period")
    tr("cold_costs")
    tr("Cold_loss")
    tr("consider_trench_and_pipe_costs")
    tr("line_type")
    tr("minimum_cooling_load")
    tr("minimum_cold_demand")
    tr("minimum_linear_cold_density")
    tr("minimum_supply_temperature")
    tr("constraints")
    tr("generate_cooling_network")
    tr("heat_costs")
    tr("heat_loss")
    tr("minimum_heating_load")
    tr("minimum_heat_demand")
    tr("minimum_linear_heat_density")
    tr("maximum_supply_temperature")
    tr("keep_unconnected_customers")

    #topology dialog
    tr("snapping_tolerance")
    tr("redraw_submodel_polygon")
    tr("delete_unconnected_customers")
    tr("delete_unconnected_lines")
    tr("connect_unconnected_plants_to_network")
    tr("connect_unconnected_customers_to_network")
    tr("customer_template")
    tr("add_customers_to_unconnected_network_ends")
    tr("delete_unconnected_network_ends")
    tr("override_templates")
    tr("keep_templates")
    tr("generate_topology")

    #add child version dialogs
    tr("add_child_version")
    tr("child_version_name")

    #rename version dialogs
    tr("rename_version")
    tr("new_version_name")

    #pipe bundle editor dialogs
    tr("generate_pipe_bundles")
    tr("pipe_constructions")
    tr("horizontal_distance")
    tr("depth")
    tr("no_parallel_pipes")
    tr("no_layers")
    tr("description_pipe_bundle_editor")
    tr("fields_of_layer")
    tr("add_pipe_bundle_field_to_layer")
    tr("pipe_bundle_editor")
    tr("extend_pipe_bundles")
    tr("truncate_existing_pipe_bundles_and_their_constructions")
    tr("ambient_mapping")
    tr("pipe_bundle_attributes")

    #save as version dialogs
    tr("save_project_version_as")
    tr("project_version_name")

    #import dialogs
    tr("import_plants_or_customers_from_layer")
    tr("import_network_topology_from_layer")
    tr("network_layer")
    tr("point_layer")
    tr("extend_topology")
    tr("truncate_existing_topology")
    tr("layer_fields")
    tr("line_fields")
    tr("feature_fields")
    tr("expression")
    tr("fields")
    tr("map_layer_fields")
    tr("pipe_bundle_type_editor")
    tr("truncate_existing_layer")
    tr("extend_layer")
    
    #feature mapping dialog
    tr("title_feature_model_parameter_mapping")
    tr('info_feature_parm_mapping')
    tr('mapping_expression')
    tr('mapping_direction')
    tr('parameter_name')
    tr('model_name')
    tr('macro_name')
    
    #delete version dialog
    tr('delete_version')
    tr('ask_delete_version')

    #import project dialog
    tr('import_districts_project_directory')

    #export project dialog
    tr('export_project_settings')
    tr('export')

    #add base version dialog
    tr('add_base_version')
    tr('ask_delete_version')

    #delete project dialog
    tr('delete_project')
    tr('ask_delete_project')
    
    #create new project dialog
    tr('new_districts_project')
    tr('project_name')

    #project config dialog
    tr('coordinate_system_srid')
    tr('project_configuration_settings')

    #osm dialog
    tr("drop_old_features")
    tr("osm_streets")
    tr("osm_buildings")

    #connection types dialog
    tr("connection_types")
    tr("connection_type_id")
    tr("connection_type_connections")

    #connection bundles dialog
    tr("connection_bundles")
    tr("connection_bundle_id")

    #pipe bundle dialog
    tr("pipe_bundle")
    tr("pipe_bundle_id")
    tr("investment_costs")
    tr("operating_costs")
    tr("x_coord")
    tr("y_coord")
    tr("ambient")
    tr("bundle_type_conns")
    tr("bundle_pipes")

    #pipes dialog
    tr("pipes")
    tr("pipe_id")
    tr("pipe_construction_id")
    tr("absolute_roughness")
    tr("inner_diameter")
    tr("pipe_costs")

    #defaults dialog
    tr("defaults_layer_lines")
    tr("defaults_layer_customers")
    tr("defaults_layer_energy_plants")

    #construction dialog
    tr("constructions")
    tr("construction_id")
    tr("thickness")
    tr("pipe_layers")

    #materials dialog
    tr("material")
    tr("materials")
    tr("material_id")
    tr("thermal_conductivity")
    tr("specific_heat")
    tr("density")

    #elevation dialog
    tr("elevation_data")

    #connections dialog
    tr("connections")
    tr("connection_id")
    tr("massflow_set_asboundary_condition")
    tr("design_temperature")
    tr("design_pressure")
    tr("design_massflow")

    #import measurement data dialog
    tr("import_measurement_data_into_DB")
    tr("data_interpolation_s")
    tr("delete_data_selected_variables")
    tr("delete_data_selected_variables_present_feature_id")
    tr("data_source")
    
    #messages
    tr('no_db_connection')
    tr('no_project_selected')
    tr('no_version_selected')
    tr('no_version_loaded')
    tr('no_layer_selected')
    tr('no_item_selected')
    tr('please_enter_number_table_row')
    tr('file_not_found')
    
    #status
    tr('version_loaded')
    tr('project_loaded')
    tr('db_connected')
    tr('db_disconnected')
    tr('settings_saved')
    tr('version_deleted')
    tr('import_completed')
    tr('connections_saved_successfully')
    tr('connection_types_saved_successfully')
    tr('connection_bundles_saved_successfully')
    tr('materials_saved_successfully')
    tr('constructions_saved_successfully')
    tr('pipes_saved_successfully')
    tr('pipe_bundles_saved_successfully')
    tr('data_saved_successfully')
    
    

    
    
    
    
    