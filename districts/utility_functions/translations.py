from qgis.PyQt.QtCore import QCoreApplication

def tr(context,key):
    return QCoreApplication.translate(context, key)
    
def _register_translation_keys():
    #project
    
    
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