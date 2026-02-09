from qgis.core import QgsAttributeEditorAction,QgsAction,QgsProject,Qgis

def setupCustomerDataSheet():
    """Setup of the customer data sheet (RMB project) including button which generates a print layout and exports a pdf"""
    feature_layer=QgsProject.instance().mapLayersByName('customers')[0] 

    layoutName = "Customer Data Sheet"
    action_text="""from qgis.PyQt.QtGui import QFont,QColor
from qgis.PyQt.QtCore import *
from qgis.core import *
from qgis.PyQt.QtGui import *
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
title.setText("[%Strasse%] [%"Address Nr"%], [%"Plz."%] [%Ort%]")
title.setFont(QFont("Arial", 20 ,QFont.Bold))
title.adjustSizeToText()
#title.setFixedSize(200.0,100.0)
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(140, 15), True)

logo_path=project_path+"/images/Logo_Werke am Zürichsee.jpg"
if os.path.exists(logo_path):
    logo=QgsLayoutItemPicture(layout)
    logo.setMode(QgsLayoutItemPicture.FormatRaster)
    logo.setPicturePath(logo_path)
    logo.attemptMove(QgsLayoutPoint(160, 5, QgsUnitTypes.LayoutMillimeters))
    logo.attemptResize(QgsLayoutSize(*[500,250], QgsUnitTypes.LayoutPixels))
    layout.addLayoutItem(logo)

#Polygon
polygon = QPolygonF()
polygon.append(QPointF(20, 25))
polygon.append(QPointF(190, 25))

layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)

#Layers
srid=2056

building_layer=QgsProject.instance().mapLayersByName('Kunden')
if building_layer:
    building_layer=building_layer[0]
    
print([% $x %])
print(QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ))
feats = []
for building_feature in building_layer.getFeatures():
    if QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ).within(building_feature.geometry()):
        feats.append(building_feature)

print(feats)
layer_buildings_mem = QgsVectorLayer("Polygon?crs=epsg:"+str(srid), "Kunde", "memory")
layer_buildings_data = layer_buildings_mem.dataProvider()
attr = building_layer.dataProvider().fields().toList()
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

feature_layer = project.mapLayersByName('140000 KON FW Zollikon Gemeindebauten 230613_pn')[0]
feats = [feat for feat in feature_layer.getFeatures()]
layer_customer_mem = QgsVectorLayer("Point?crs=epsg:"+str(srid), "duplicated_customer_layer", "memory")
layer_customer_data = layer_customer_mem.dataProvider()
attr = feature_layer.dataProvider().fields().toList()
layer_customer_data.addAttributes(attr)
layer_customer_mem.updateFields()
layer_customer_data.addFeatures(feats)
project.addMapLayer(layer_customer_mem)
# Move Layer
myalayer = root.findLayer(layer_customer_mem.id())
myClone = myalayer.clone()
parent = myalayer.parent()
parent.insertChildNode(0, myClone)
parent.removeChildNode(myalayer)

layer_osm = project.mapLayersByName('OpenStreetMap')
if layer_osm:
    layer_osm=layer_osm[0]
    print('osm')

layer_network = project.mapLayersByName('Netz')
if layer_network:
    layer_network=layer_network[0]
    print('layer_network')

#No symbol for customer layer    
null_renderer = QgsNullSymbolRenderer()
layer_customer_mem.setRenderer(null_renderer)
layer_customer_mem.triggerRepaint() # update map canvas

#Add labels.
layer_settings = QgsPalLayerSettings()
layer_settings.fieldName = "Nr."
layer_settings.isExpression = True

layer_settings.placement = layer_settings.placement=QgsPalLayerSettings.OverPoint
layer_settings.xOffset = 0
layer_settings.yOffset = 0.0
layer_settings.enabled = True

text_format = QgsTextFormat()
text_format.setFont(QFont("Arial Black", 10))
layer_settings.setFormat(text_format)

labeling = QgsVectorLayerSimpleLabeling(layer_settings)
layer_customer_mem.setLabelsEnabled(True)
layer_customer_mem.setLabeling(labeling)
layer_customer_mem.triggerRepaint()

#Map
map=QgsLayoutItemMap(layout)
map.setRect(10,10,10,10)

#Set Map Extent
#defines map extent using map coordinates
#get coordinates
map_width=500 #m
map_height=250 #m
rectangle = QgsRectangle([% $x %]-map_width/2, [% $y %]+map_height/2, [% $x %]+map_width/2, [% $y %]-map_height/2)
map.setExtent(rectangle)

map.attemptMove(QgsLayoutPoint(20,30,QgsUnitTypes.LayoutMillimeters))
map.attemptResize(QgsLayoutSize(180,90, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(map)

#legend
root = QgsLayerTree()
root.addLayer(layer_buildings_mem)
#root.addLayer(layer_customer_mem)
root.addLayer(layer_osm)
root.addLayer(layer_network)

legend = QgsLayoutItemLegend(layout)
legend.model().setRootGroup(root)
legend.setLinkedMap(map)
layout.addLayoutItem(legend)
legend.attemptMove(QgsLayoutPoint(165,35,QgsUnitTypes.LayoutMillimeters))

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
scale.attemptMove(QgsLayoutPoint(22,105,QgsUnitTypes.LayoutMillimeters))
scale.attemptResize(QgsLayoutSize(50,8, QgsUnitTypes.LayoutMillimeters))

#north arrow 
north=QgsLayoutItemPicture(layout)
north.setMode(QgsLayoutItemPicture.FormatSVG)
north.setPicturePath(project_path+"/images/NorthArrow_04.svg")
north.attemptMove(QgsLayoutPoint(25, 35, QgsUnitTypes.LayoutMillimeters))
north.attemptResize(QgsLayoutSize(*[150,150], QgsUnitTypes.LayoutPixels))
layout.addLayoutItem(north)

map.setLayers([layer_buildings_mem,layer_customer_mem,layer_network,layer_osm])

#Table 1
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("Gebäude")
cols[0].setWidth(29)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['Eigentümer'],['Object-Nr.']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(45, 20), True)
frame.attemptMove(QgsLayoutPoint(20, 125, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)


#Table 2
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("[%"Nr."%]")
cols[0].setWidth(59)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Grey"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Grey"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['[%"Eigentümer"%]'],['[%"Gebäude Nr."%]']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(45, 20), True)
frame.attemptMove(QgsLayoutPoint(50, 125, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#Table 3
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("Verwaltung")
cols[0].setWidth(44)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['Vertragspartner'],[]])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(45, 20), True)
frame.attemptMove(QgsLayoutPoint(110, 125, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#Table 4
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("xy")
cols[0].setWidth(44)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Grey"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Grey"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['xy'],[]])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(45, 20), True)
frame.attemptMove(QgsLayoutPoint(155, 125, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#This adds labels to the layout
title = QgsLayoutItemLabel(layout)
title.setText("Anschluss Wärme")
title.setFont(QFont("Arial", 10 ,QFont.Bold))
title.adjustSizeToText()
#title.setFixedSize(200.0,100.0)
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(20, 144, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(140, 15), True)

#Polygon
polygon = QPolygonF()
polygon.append(QPointF(20, 149))
polygon.append(QPointF(190, 149))
layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)

#Table 1
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("Anschlussleistung abonniert")
cols[0].setWidth(72)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['Wärmeverbrauch erwartet'],['Volllaststunden erwartet'],[],['Systemtemperatur Verbund'],['Maximale Vorlauf'],['Maximale Rücklauf'],[],['Systemtemperatur Kunde'],['Vorlauf'],['Rücklauf']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(75, 63), True)
frame.attemptMove(QgsLayoutPoint(20, 150, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)


#Table 2
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("[%"Wärmeleistung Simulation, kW"%]")
cols[0].setWidth(52)
cols[0].setHAlignment(Qt.AlignRight)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Grey"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Grey"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['[%"Wärmeenergiebedarf Simulation kWh/a"%]'],['[%"Volllaststunden Simulation, h/a"%]'],[],[],['xy'],['xy'],[],[],['[%"max. VL-Te"%]'],['[%"max. RL-Te"%]']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(55, 63), True)
frame.attemptMove(QgsLayoutPoint(95, 150, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#Table 3
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("kW")
cols[0].setWidth(27)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['kWh/a'],['h/a'],[],[],['°C'],['°C'],[],[],['°C'],['°C']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(30, 63), True)
frame.attemptMove(QgsLayoutPoint(150, 150, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#This adds labels to the layout
title = QgsLayoutItemLabel(layout)
title.setText("Netztopologie")
title.setFont(QFont("Arial", 10 ,QFont.Bold))
title.adjustSizeToText()
#title.setFixedSize(200.0,100.0)
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(20, 214, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(140, 15), True)

#Polygon
polygon = QPolygonF()
polygon.append(QPointF(20, 219))
polygon.append(QPointF(190, 219))
layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)

#Table 1
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading(("☑" if "[%"Anergienetz"%]"!="" else "☐" ) + " Anergienetz")
cols[0].setWidth(59)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['Anschlussvariante'],['Strang-Nr.'],['Anschlussleitung']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(59, 40), True)
frame.attemptMove(QgsLayoutPoint(20, 221, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)


#Table 2
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading(("☑" if "[%"FW Sportplatz"%]" !="" else "☐" ) + " Fernwärme Sportplatz")
cols[0].setWidth(59)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['☐ Schema 1'],['xy'],['DN xy']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(59, 60), True)
frame.attemptMove(QgsLayoutPoint(80, 221, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#Table 3
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading(("☑" if "[%"FW Fohrbach"%]" !="" else "☐" )+" Fernwärme Fohrbach")
cols[0].setWidth(59)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['☐ Schema 2'],[],[]])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(60, 40), True)
frame.attemptMove(QgsLayoutPoint(140, 221, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#This adds labels to the layout
title = QgsLayoutItemLabel(layout)
title.setText("Preismodell")
title.setFont(QFont("Arial", 10 ,QFont.Bold))
title.adjustSizeToText()
#title.setFixedSize(200.0,100.0)
layout.addLayoutItem(title)
title.attemptMove(QgsLayoutPoint(20, 246, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(140, 15), True)

#Polygon
polygon = QPolygonF()
polygon.append(QPointF(20, 251))
polygon.append(QPointF(190, 251))
layoutItemPolygon = QgsLayoutItemPolygon(polygon, layout)
layout.addLayoutItem(layoutItemPolygon)

#Table 1
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("Anschlussgebühr")
cols[0].setWidth(72)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['Leistungspreis'],['Netznutzungspreis'],['Energiepreis Basis']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(75, 63), True)
frame.attemptMove(QgsLayoutPoint(20, 252, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)


#Table 2
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("100")
cols[0].setWidth(52)
cols[0].setHAlignment(Qt.AlignRight)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Grey"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Grey"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['70'],['7.0'],['7.0']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(55, 63), True)
frame.attemptMove(QgsLayoutPoint(95, 252, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

#Table 3
table = QgsLayoutItemTextTable(layout)
layout.addMultiFrame(table)
# Add columns       
cols = [QgsLayoutTableColumn()]
cols[0].setHeading("CHF/kW")
cols[0].setWidth(27)
table.setColumns(cols)
#style
table.setGridStrokeWidth(0.000001) # 0.1 mm
table.setGridColor(QColor("White"))
# content text
content_text_format = QgsTextFormat()
content_text_format.setSize(10)
content_text_format.setColor(QColor("Black"))
table.setContentTextFormat(content_text_format)
# header text
header_text_format = QgsTextFormat()
header_text_format.setSize(10)
header_text_format.setColor(QColor("Black"))
table.setHeaderTextFormat(header_text_format)
# Add rows
table.setContents([['CHF/kW'],['Rp/kW'],['Rp/kW']])
# Base class for frame items, which form a layout multiframe item.
frame = QgsLayoutFrame(layout, table)
frame.attemptResize(QgsLayoutSize(30, 63), True)
frame.attemptMove(QgsLayoutPoint(150, 252, QgsUnitTypes.LayoutMillimeters))   #allows moving text box
table.addFrame(frame)

export_path=project_path.replace('/',"\\")+"\\Kundenblätter\\"
print(export_path)
if os.path.exists(export_path.replace('\\\\','\\')):
    export_path+="Kundenblatt_[%"Eigentümer"%]_[%"Nr."%].pdf"
    print(export_path)
    layoutmanager = project.layoutManager()
    layout_item = layoutmanager.layoutByName("{}")
    export = QgsLayoutExporter(layout_item)
    export.exportToPdf(export_path, QgsLayoutExporter.PdfExportSettings())

    subprocess.Popen([export_path.replace('\\\\','\\')],shell=True)


#Redo changes
project.removeMapLayer(layer_customer_mem)
project.removeMapLayer(layer_buildings_mem)

#iface.openLayoutDesigner(layout)

""".format(layoutName,layoutName,layoutName)


    helpAction = QgsAction(Qgis.AttributeActionType.GenericPython, 'Create Custtomer Data Sheet', action_text, None, capture=False, shortTitle=layoutName, actionScopes={'Feature'})
    feature_layer.actions().addAction(helpAction)

    form_config = feature_layer.editFormConfig()

    rootContainer = form_config.invisibleRootContainer()
    print(rootContainer)
    editorAction = QgsAttributeEditorAction(helpAction, rootContainer)
    rootContainer.addChildElement(editorAction)

    feature_layer.setEditFormConfig(form_config)