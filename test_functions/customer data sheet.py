from qgis.core import QgsAttributeEditorAction,QgsAction,QgsProject,Qgis
from districts.utility_functions.files import *
from districts.utility_functions.db import *
from districts.utility_functions.utility import *


plugin_dir="""C:\\Users\\peter.nageler\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\districts"""

config=load_plugin_settings()
print(config)
projectConfig = loadProjectConfig(plugin_dir,config['projectName'])  

def setupCustomerDataSheet():
    """Setup of the customer data sheet (RMB project) including button which generates a print layout and exports a pdf"""
    
    feature_layer=QgsProject.instance().mapLayersByName('customers')[0] 
    print(feature_layer)
    layoutName = "Customer Data Sheet"
    action_text="""from qgis.PyQt.QtGui import QFont, QColor, QPolygonF
from qgis.PyQt.QtCore import QPointF, Qt
from qgis.core import *
from qgis.utils import iface
from qgis.core import QgsApplication

from qgis.core import (
    QgsLayoutItemTextTable,
    QgsLayoutTableColumn,
    QgsLayoutFrame,
    QgsLayoutSize,
    QgsLayoutPoint,
    QgsUnitTypes,
    QgsTextFormat,
    QgsLayoutItemPicture
)

from districts.utility_functions.plots import *
from districts.utility_functions.db import *

import subprocess
import math
import tempfile
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


# Get current project
project = QgsProject.instance()
plugin_dir = QgsApplication.qgisSettingsDirPath() + "python\\plugins\\districts"
manager = project.layoutManager()       
projectName="{}"
versionName="{}"
srid={}
config={}

conn=dbConnect(config,True)
cur=conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

# Remove existing layout with the same name
layouts_list = manager.printLayouts()
for layout in layouts_list:
    if layout.name() == "CustomerDataSheet":  # Replace with your layout name
        manager.removeLayout(layout)

# Create new print layout
layout = QgsPrintLayout(project)        
layout.setName("CustomerDataSheet")  # Replace with your layout name
manager.addLayout(layout)

# Add new page
page = QgsLayoutItemPage(layout)
page.setPageSize('A4', QgsLayoutItemPage.Portrait)
layout.pageCollection().addPage(page)

# -----------Header-----------------
#fonts
font_header_label = QFont("Arial", 18)
font_header_label.setBold(True)  # Correct way to make it bold
font_header = QFont("Arial", 18)
font_header.setItalic(True)  # Correct way to make it bold
font_table_label = QFont("Arial", 10)
font_table_label.setBold(True)
font_table = QFont("Arial", 10)

# Add header project label
label_project = QgsLayoutItemLabel(layout)
label_project.setText("Project: ")
label_project.setFont(font_header_label)
label_project.adjustSizeToText()
label_project.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
label_project.attemptResize(QgsLayoutSize(140, 15), True)

project_ = QgsLayoutItemLabel(layout)
project_.setText(projectName)
project_.setFont(font_header)
project_.setFontColor(QColor("gray"))
project_.adjustSizeToText()
project_.attemptMove(QgsLayoutPoint(60, 10, QgsUnitTypes.LayoutMillimeters))
project_.attemptResize(QgsLayoutSize(140, 15), True)


# Add header project label
label_version = QgsLayoutItemLabel(layout)
label_version.setText("Version: ")
label_version.setFont(font_header_label)
label_version.adjustSizeToText()
label_version.attemptMove(QgsLayoutPoint(20, 18, QgsUnitTypes.LayoutMillimeters))
label_version.attemptResize(QgsLayoutSize(140, 15), True)

version = QgsLayoutItemLabel(layout)
version.setText(versionName)
version.setFont(font_header)
version.setFontColor(QColor("gray"))
version.adjustSizeToText()
version.attemptMove(QgsLayoutPoint(60, 18, QgsUnitTypes.LayoutMillimeters))
version.attemptResize(QgsLayoutSize(140, 15), True)

layout.addLayoutItem(label_project)
layout.addLayoutItem(project_)
layout.addLayoutItem(label_version)
layout.addLayoutItem(version)

logo_path=plugin_dir+"/icons/IDA_Districts_Icon_QGIS.png"
if os.path.exists(logo_path):
    logo=QgsLayoutItemPicture(layout)
    logo.setMode(QgsLayoutItemPicture.FormatRaster)
    logo.setPicturePath(logo_path)
    logo.attemptMove(QgsLayoutPoint(160, 5, QgsUnitTypes.LayoutMillimeters))
    logo.attemptResize(QgsLayoutSize(*[250,250], QgsUnitTypes.LayoutPixels))
    layout.addLayoutItem(logo)

# Polygon example
polygon = QPolygonF()
polygon.append(QPointF(20, 25))
polygon.append(QPointF(190, 25))

layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)

# --------------map layers-------------------
#load buildings layer
buildings_layer=QgsProject.instance().mapLayersByName('buildings')[0]
print('---buildings----')
print([% $x %])
print(QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ))
feats = []
for building_feature in buildings_layer.getFeatures():
    if QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ).within(building_feature.geometry()):
        feats.append(building_feature)
print(feats)

layer_buildings_mem = QgsVectorLayer("Polygon?crs=epsg:"+str(srid), "buildings", "memory")
layer_buildings_data = layer_buildings_mem.dataProvider()
attr = buildings_layer.dataProvider().fields().toList()
layer_buildings_data.addAttributes(attr)
layer_buildings_mem.updateFields()
layer_buildings_data.addFeatures(feats)
project.addMapLayer(layer_buildings_mem)
root = project.layerTreeRoot()
# Move Layer
myalayer = root.findLayer(layer_buildings_mem.id())
myClone = myalayer.clone()
parent = myalayer.parent()
parent.insertChildNode(0, myClone)
parent.removeChildNode(myalayer)
#change fill color
single_symbol_renderer = layer_buildings_mem.renderer()
symbol = single_symbol_renderer.symbol()
symbol.setColor(QColor("Red"))
# more efficient than refreshing the whole canvas, which requires a redraw of ALL layers
layer_buildings_mem.triggerRepaint()
# update legend for layer
qgis.utils.iface.layerTreeView().refreshLayerSymbology(layer_buildings_mem.id())

feature_layer = project.mapLayersByName('customers')[0]
feats = []
for substation_feature in feature_layer.getFeatures():
    if QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ).within(substation_feature.geometry()):
        feats.append(substation_feature)
print(feats)
#Memory Layer erstellen und befüllen
layer_customer_mem = QgsVectorLayer("Point?crs=epsg:"+str(srid), "substation", "memory")
data_pr = layer_customer_mem.dataProvider()
data_pr.addAttributes(feature_layer.fields())
layer_customer_mem.updateFields()
data_pr.addFeatures(feats)
layer_customer_mem.setRenderer(feature_layer.renderer().clone())
project.addMapLayer(layer_customer_mem)
root = project.layerTreeRoot()

# Move Layer to top
myalayer = root.findLayer(layer_customer_mem.id())
myClone = myalayer.clone()
parent = myalayer.parent()
parent.insertChildNode(0, myClone)
parent.removeChildNode(myalayer)

osm_layers = project.mapLayersByName('OpenStreetMap')
if osm_layers:
    layer_osm = osm_layers[0]
    print("OSM layer already exists")
else:
    # Add OSM XYZ Tile layer
    url = "type=xyz&url=https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"
    layer_osm = QgsRasterLayer(url, "OpenStreetMap", "wms")  # "wms" works for XYZ in QGIS 3.40
    if not layer_osm.isValid():
        print("Failed to load OSM layer")
    else:
        project.addMapLayer(layer_osm)
        print("OSM layer added")

layer_network = project.mapLayersByName('lines')[0]
layer_ep = project.mapLayersByName('energy_plants')[0]
  
# ------------map-------------
#Map
map=QgsLayoutItemMap(layout)
map.setRect(10,10,10,10)

#Set Map Extent
#defines map extent using map coordinates
#get coordinates
map_width=500 #m
map_height=250 #m
rectangle = QgsRectangle([% $x %]-map_width/3, [% $y %]+map_height/2, [% $x %]+map_width*2/3, [% $y %]-map_height/2)
map.setExtent(rectangle)

map.attemptMove(QgsLayoutPoint(20,30,QgsUnitTypes.LayoutMillimeters))
map.attemptResize(QgsLayoutSize(170,120, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(map)

# legend
root = QgsLayerTree()
root.addLayer(layer_customer_mem)
root.addLayer(layer_ep)
root.addLayer(layer_network)
root.addLayer(layer_buildings_mem)
root.addLayer(layer_osm)

# Legenden-Objekt erstellen und hinzufügen (wie bisher)
legend = QgsLayoutItemLegend(layout)
legend.model().setRootGroup(root)
legend.setLinkedMap(map)
layout.addLayoutItem(legend)

# position and size
legend.setResizeToContents(False)
legend.attemptResize(QgsLayoutSize(50, 110, QgsUnitTypes.LayoutMillimeters))
legend.attemptMove(QgsLayoutPoint(138, 35, QgsUnitTypes.LayoutMillimeters))

#Add scale bar    
scale=QgsLayoutItemScaleBar(layout)
scale.setStyle('Single Box')
scale.setFont(QFont("Arial",15))
scale.setFontColor(QColor("Black"))
scale.setBackgroundEnabled(True)
scale.setFillColor(QColor("Black"))
scale.applyDefaultSize(QgsUnitTypes.DistanceMeters)
scale.setMapUnitsPerScaleBarUnit(1)
scale.setNumberOfSegments(2)
scale.setUnitsPerSegment(50)
scale.setUnitLabel("m")
scale.setLinkedMap(map)
layout.addLayoutItem(scale)
scale.attemptMove(QgsLayoutPoint(22,135,QgsUnitTypes.LayoutMillimeters))
scale.attemptResize(QgsLayoutSize(50,8, QgsUnitTypes.LayoutMillimeters))

#north arrow 
north=QgsLayoutItemPicture(layout)
north.setMode(QgsLayoutItemPicture.FormatSVG)
north.setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
north.attemptMove(QgsLayoutPoint(25, 35, QgsUnitTypes.LayoutMillimeters))
north.attemptResize(QgsLayoutSize(*[150,150], QgsUnitTypes.LayoutPixels))
layout.addLayoutItem(north)

map.setLayers([layer_customer_mem,layer_ep,layer_network,layer_buildings_mem,layer_osm])
  
#title.setText(str(round([% $x %],1)) + " , " + str(round([% $y %],1)) + " SRID: 4326")  # Replace SRID if needed

#------------attribute table--------------
print('------------attribute table--------------')
# --- 1. DATEN VORBEREITEN ---
layer = layer_customer_mem
fields = layer.fields()
feat = next(layer.getFeatures())

# Geometrie-Daten extrahieren (entspricht [% $x %] etc.)
geom = feat.geometry()
point = geom.asPoint()
pos_str = f"{{round(point.x(), 1)}} , {{round(point.y(), 1)}}"
srid_str = str(layer.crs().postgisSrid())

# Alle anzuzeigenden Daten in einer Liste sammeln (Tupel aus Name, Wert)
display_list = []
for field in fields:
    display_list.append((field.name(), str(feat[field.name()])))

# Position und SRID hinzufügen
display_list.append(("Position", pos_str))
display_list.append(("SRID", srid_str))

num_entries = len(display_list)

# Bestimme Layout-Modus: 4 Spalten wenn mehr als 4 Einträge
columns_count = 4 if num_entries > 4 else 2
table_data = []

if columns_count == 4:
    # Berechne Zeilenanzahl für 2-Block-Layout
    rows_needed = math.ceil(num_entries / 2)
    for i in range(rows_needed):
        row = []
        # Linker Block
        name_l, val_l = display_list[i]
        row.extend([name_l, val_l])
        
        # Rechter Block
        idx_right = i + rows_needed
        if idx_right < num_entries:
            name_r, val_r = display_list[idx_right]
            row.extend([name_r, val_r])
        else:
            row.extend(["", ""]) # Padding
        table_data.append(row)
else:
    # Einfaches 2-Spalten Layout
    for name, val in display_list:
        table_data.append([name, val])

# --- 2. TABELLE INITIALISIEREN ---
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)

# --- 3. SPALTEN (HEADER) DEFINIEREN ---
header_labels = ["Attribut", "Wert"] * (columns_count // 2)
cols = []
for label in header_labels:
    col = QgsLayoutTableColumn()
    col.setHeading(label)
    col.setWidth(40 if columns_count == 4 else 50) 
    cols.append(col)
table.setColumns(cols)

# --- 4. STYLING ---
table.setGridStrokeWidth(0.000001) 
table.setGridColor(QColor("White"))

# Content Text Format
content_text_format = QgsTextFormat()
content_text_format.setFont(font_table) 
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)

# Header Text Format
header_text_format = QgsTextFormat()
header_text_format.setFont(font_table_label)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)

# Daten in die Tabelle schreiben
table.setContents(table_data)

# --- 5. FRAME ERSTELLEN & REGISTRIEREN ---
frame = QgsLayoutFrame(layout, table)
frame.setId("AttributTabelle")
layout.addLayoutItem(frame)
table.addFrame(frame)

# --- 6. GEOMETRIE & POSITIONIERUNG ---
table.refreshAttributes()
needed_table_height = table.totalHeight() + 1.5
width = 170 if columns_count == 4 else 100

frame.attemptResize(QgsLayoutSize(width, max(10, needed_table_height), QgsUnitTypes.LayoutMillimeters))
frame.attemptMove(QgsLayoutPoint(20, 155, QgsUnitTypes.LayoutMillimeters))

# --- 7. FINALE OPTIMIERUNG ---
frame.setZValue(999) 
layout.setSelectedItem(frame)
layout.refresh()

#----simulation_results diagram-----------
print([%id%])
filenames=matplotlibPowerPlots(plugin_dir,config,cur,[%id%],feature_type='customer',show_plot=False,save_plot=True)
print(filenames)
if filenames:
    # Polygon example
    polygon = QPolygonF()
    polygon.append(QPointF(20, needed_table_height+155))
    polygon.append(QPointF(190, needed_table_height+155))

    layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
    layout.addLayoutItem(layoutItemPolygon)# Polygon example
    
    # Add title simulation results
    label_simulation_results = QgsLayoutItemLabel(layout)
    label_simulation_results.setText("Simulation results")
    label_simulation_results.setFont(font_header_label)
    label_simulation_results.adjustSizeToText()
    label_simulation_results.attemptMove(QgsLayoutPoint(20, needed_table_height+157, QgsUnitTypes.LayoutMillimeters))
    label_simulation_results.attemptResize(QgsLayoutSize(140, 15), True)
    layout.addLayoutItem(label_simulation_results)

layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)
picture_height=0
for filename in filenames:
    #Create a layout picture item
    picture = QgsLayoutItemPicture(layout)
    # Set the image file path
    picture.setPicturePath(filename+'.svg')
    svg_width_mm, svg_height_mm = get_svg_size(filename+'.svg')
    picture.attemptMove(QgsLayoutPoint(20, needed_table_height+165+picture_height))  # position in mm

    # Set size from SVG
    if svg_width_mm and svg_height_mm:
        scale = 0.8
        if needed_table_height+165+picture_height+svg_height_mm * scale >297:
        # Create a new page
            new_page = QgsLayoutItemPage(layout)

            # Optional: set size and orientation (default is A4 Portrait)
            new_page.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
            layout.pageCollection().addPage(new_page)
        picture.attemptResize(QgsLayoutSize(svg_width_mm*scale, svg_height_mm*scale))
        picture_height+=svg_height_mm * scale+5
    else:
        # fallback size
        picture.attemptResize(QgsLayoutSize(80, 50))
        picture_height+=55
    #Set position and size (optional)

    #Add picture to layout
    layout.addLayoutItem(picture)

temp_folder = tempfile.gettempdir()+'\\\\'
createDir(temp_folder,'ida_districts')
export_path=temp_folder+'ida_districts\\\\'
export_path=export_path.replace('/',"\\\\")
print(export_path)
if os.path.exists(export_path):
    export_path+='customer_'+str([%id%])+'_report.pdf'
    print(export_path)
    export = QgsLayoutExporter(layout)
    export.exportToPdf(export_path, QgsLayoutExporter.PdfExportSettings())

    subprocess.Popen([export_path],shell=True)
    
#Redo changes
project.removeMapLayer(layer_customer_mem)
project.removeMapLayer(layer_buildings_mem)
""".format(config['projectName'],config['versionName'],projectConfig['srid'],config)

    print(action_text)
    helpAction = QgsAction(Qgis.AttributeActionType.GenericPython, 'Create Custtomer Data Sheet', action_text, None, capture=False, shortTitle=layoutName, actionScopes={'Feature'})
    feature_layer.actions().addAction(helpAction)

    form_config = feature_layer.editFormConfig()

    rootContainer = form_config.invisibleRootContainer()
    print(rootContainer)
    editorAction = QgsAttributeEditorAction(helpAction, rootContainer)
    rootContainer.addChildElement(editorAction)

    feature_layer.setEditFormConfig(form_config)


setupCustomerDataSheet()