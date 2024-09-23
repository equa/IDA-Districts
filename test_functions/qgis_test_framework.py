from plugins.utility_functions.files import *
from plugins.utility_functions.sensor_signals import *
from plugins.utility_functions.topology import *
import psycopg2.extras
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'cosim_test1', 'versionName' : 'b'}
#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
print(cur)
sensor_data=getSensorData(cur,dictDB)
print(sensor_data)
dfg

def setupVersionForm_light():  
    """ setup form for version layers"""
    for vlayerName in ['dhc_lines','dhc_devices','dhc_junctions','dhc_customers','dhc_energy_plants','dhc_structure_boundarys','dhc_structure_junctions','dhc_structure_lines']:
        vlayer=QgsProject.instance().mapLayersByName(vlayerName)[0] 
        fields=vlayer.fields()
        fc = vlayer.editFormConfig()
        fc.clearTabs()
        fc.setLayout(QgsEditFormConfig.TabLayout)
        if vlayerName=='dhc_devices':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['asl_m'],
                            [],[]]
        elif vlayerName=='dhc_junctions':
            attrNamesTabs= [['assetgroup','submodel'],
                            ['asl_m','n_connections'],
                            [],[]]
        elif vlayerName=='dhc_lines':
            attrNamesTabs= [['assetgroup','assettype','pipe_bundle_type_id','network','submodel'],
                            ['length','nominaltemperature','maximumtemperature','nominaloppressure','maximumoppressure'],
                            [],[]]
        elif vlayerName=='dhc_customers':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['dhw_id','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            ['sim_model',["Model 2","FloorArea","TSetC"]],
#                           []]    
                            ['owner','building_nr','street','street_nr','zip','location','usage','energy_carrier','qdot_heat_kw','heat_kwh7a','full_load_hours_h7a','Tsup_max_deg','Tret_max_deg','connection','connection_since']]
        elif vlayerName=='dhc_energy_plants':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['main_plant','heat_e_kwh','heat_p_kw','tsup_h_deg','cool_e_kwh','cool_p_kw','tsup_c_deg','asl_m'],
                            [],[]]
        elif vlayerName=='dhc_structure_boundarys':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            ['f_vexp_m'],
                            [],[]]
        elif vlayerName=='dhc_structure_junctions':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            [],
                            [],[]]
        elif vlayerName=='dhc_structure_lines':
            attrNamesTabs= [['assetgroup','assettype','submodel'],
                            [],
                            [],[]]
        for tab,attrNamesTab in zip(['General','Physical data','Simulation data','Metadata'],attrNamesTabs):
            if attrNamesTab:
                c = QgsAttributeEditorContainer(tab, fc.invisibleRootContainer())
                c.setIsGroupBox(False) # a tab
                for attrName in attrNamesTab:
                    #print (attrName)
                    if type(attrName) is list:
                        fc.addTab(c)
                        c1 = QgsAttributeEditorContainer(attrName[0], c)
                        c1.setIsGroupBox(False) # a tab
                        
                        field_idx = fields.indexOf(attrName[1])
                        c1.addChildElement(QgsAttributeEditorField(attrName[1], field_idx, c1))
                        field_idx = fields.indexOf(attrName[2])
                        c1.addChildElement(QgsAttributeEditorField(attrName[2], field_idx, c1))
                        fc.addTab(c1)
                    else:    
                        field_idx = fields.indexOf(attrName)
                        c.addChildElement(QgsAttributeEditorField(attrName, field_idx, c))
                fc.addTab(c)
        vlayer.setEditFormConfig(fc)


setupVersionForm_light()