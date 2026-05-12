from qgis.PyQt.QtCore import QCoreApplication

def tr(context,key):
    return QCoreApplication.translate(context, key)
    
def _register_translation_keys():
    #general
    tr("description")
    
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
    
    #templates
    tr("empty_project")
    tr("heating_network")
    tr("db_default_values")
    
    #descriptions
    tr("description_importPRNData")
    tr("description_importLineFeature")
    tr("description_importFeaturePoint")
    
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
    
    #feature mapping dialog
    tr("title_feature_model_parameter_mapping")
    tr('info_feature_parm_mapping')
    tr('mapping_expression')
    tr('mapping_direction')
    tr('parameter_name')
    tr('model_name')
    tr('macro_name')

    
    
    
    
    