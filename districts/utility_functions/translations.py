from qgis.PyQt.QtCore import QCoreApplication

def tr(context,key):
    return QCoreApplication.translate(context, key)
    
def _register_translation_keys():
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
    tr("energy_plant")
    tr("supervisory")
    
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
    
    