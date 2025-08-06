from qgis.core import QgsAttributeEditorAction,QgsAction,QgsProject,Qgis
from plugins.utility_functions.files import *
from plugins.utility_functions.db import *

plugin_dir="""C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\"""
dictDB={'pwd' : 'p3t3r' , 'host' : 'localhost','port':'5433', 'user' : 'postgres', 'projectName' : 'test00011', 'versionName' : 'base1'}

#dictDB=getDBConnectionData(plugin_dir)
conn=dbConnect(dictDB,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)


projectConfig=loadProjectConfig(plugin_dir,dictDB['projectName'])

def setupCustomerDataSheet():
    """Setup of the customer data sheet (RMB project) including button which generates a print layout and exports a pdf"""
    
    feature_layer=QgsProject.instance().mapLayersByName('customers')[0] 
    #print(feature_layer)
    layoutName = "Customer Data Sheet"
    action_text="""from PyQt5.QtGui import QFont,QColor
from PyQt5.QtCore import *
from qgis.core import *
from PyQt5.QtGui import *
from qgis.utils import iface
import subprocess

project = QgsProject.instance()
project_path=project.readPath("./")
manager = project.layoutManager()       

layouts_list = manager.printLayouts()
for layout in layouts_list:
    if layout.name() == "{}":
        manager.removeLayout(layout)
            
#initializes default settings for blank print layout canvas
#layout.initializeDefaults()  

layout = QgsPrintLayout(project)        
layout.setName("{}")
manager.addLayout(layout)

### Add new page
page = QgsLayoutItemPage(layout)
page.setPageSize('A4', QgsLayoutItemPage.Portrait)
layout.pageCollection().addPage(page)

#This adds labels to the layout
title = QgsLayoutItemLabel(layout)
title.setText(str(round([% $x %],1))+" , "+str(round([% $y %],1))+" SRID: {}")
title.setFont(QFont("Arial", 20 ,QFont.Bold))
title.adjustSizeToText()
#title.setFixedSize(200.0,100.0)
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(140, 15), True)

#Polygon
polygon = QPolygonF()
polygon.append(QPointF(20, 25))
polygon.append(QPointF(190, 25))




""".format(layoutName,layoutName,projectConfig['srid'])

    #print(action_text)
    helpAction = QgsAction(Qgis.AttributeActionType.GenericPython, 'Create Custtomer Data Sheet', action_text, None, capture=False, shortTitle=layoutName, actionScopes={'Feature'})
    feature_layer.actions().addAction(helpAction)

    form_config = feature_layer.editFormConfig()

    rootContainer = form_config.invisibleRootContainer()
    #print(rootContainer)
    editorAction = QgsAttributeEditorAction(helpAction, rootContainer)
    rootContainer.addChildElement(editorAction)

    feature_layer.setEditFormConfig(form_config)



setupCustomerDataSheet()