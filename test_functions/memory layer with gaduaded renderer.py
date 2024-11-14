def validatedDefaultSymbol(geometryType):
    symbol = QgsSymbol.defaultSymbol(geometryType)
    if symbol is None:
        if geometryType == Qgis.Point:
            symbol = QgsMarkerSymbol()
        elif geometryType == Qgis.Line:
            symbol = QgsLineSymbol()
        elif geometryType == Qgis.Polygon:
            symbol = QgsFillSymbol()
    return symbol

def makeSymbologyForRange(layer, min, max, title, color):
    symbol = validatedDefaultSymbol(layer.geometryType())
    symbol.setColor(color)
    range = QgsRendererRange(min, max, symbol, title)
    return range

def applySymbologyFixedDivisions(layer, field):
    rangeList = []
    rangeList.append( makeSymbologyForRange(layer, 0, 30, '0-30', 
QColor("Green") ) )
    rangeList.append( makeSymbologyForRange(layer, 30.1, 60, '30-60',  
QColor("Purple") ) )
    renderer = QgsGraduatedSymbolRenderer(field, rangeList)
    renderer.setMode(QgsGraduatedSymbolRenderer.Custom)
    layer.setRenderer(renderer)
    

feature='customer'

sLayerName = "{}s".format(feature)
sLayer = QgsProject.instance().mapLayersByName(sLayerName)[0]

# make new memory layer
temp_layer = QgsVectorLayer("PointZ?crs=epsg:31259&field=id:integer&field=value:double", "load", "memory")
temp_layer.startEditing()

for sfeat in sLayer.getFeatures():
    # make new feature
    feat = QgsFeature(temp_layer.fields())
    feat["id"] = sfeat.id()
    feat.setGeometry(sfeat.geometry())
    feat["value"] = sfeat.id()

        
    # add the feature to the table
    temp_layer.addFeature(feat)

temp_layer.commitChanges()

target_field = 'value'

num_classes = 5
ramp_name = 'Spectral'
classification_method = QgsClassificationEqualInterval()

# change format settings as necessary
format = QgsRendererRangeLabelFormat()
format.setFormat("%1 - %2")
format.setPrecision(2)
format.setTrimTrailingZeroes(True)

default_style = QgsStyle().defaultStyle()
color_ramp = default_style.colorRamp(ramp_name)

renderer = QgsGraduatedSymbolRenderer()
renderer.setClassAttribute(target_field)
renderer.setClassificationMethod(classification_method)
renderer.setLabelFormat(format)
renderer.updateClasses(temp_layer, num_classes)
renderer.updateColorRamp(color_ramp)


symbol=QgsSymbol.defaultSymbol(temp_layer.geometryType())

style={}
style['name']='arrow' #point
style['color']='black'
symbolLayer = QgsFilledMarkerSymbolLayer.create(style)

symbol.changeSymbolLayer(0, symbolLayer)
symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertySize,QgsProperty.fromExpression("""coalesce(scale_exp("value", 1, 60, 1, 10, 0.57), 0)"""))
symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyAngle,QgsProperty.fromExpression("""coalesce(scale_exp("value", 1, 60, 0, 350, 0.57), 0)"""))
renderer.updateSymbols(symbol)


temp_layer.setRenderer(renderer)

#applySymbologyFixedDivisions(temp_layer, target_field)


QgsProject.instance().addMapLayer(temp_layer)