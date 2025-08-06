layers = QgsProject.instance().mapLayersByName("lines")

if layers:
    layer = layers[0]
    symbol = QgsSymbol.defaultSymbol(layer.geometryType())
    property_collection = QgsPropertyCollection()
    scale = """coalesce(scale_exp("id", 1, 3, 1, 10, 0.57), 0)"""
    property_collection.setProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression(scale))
    symbol.symbolLayer(0).setDataDefinedProperties(property_collection)
    #print(property_collection.property(QgsSymbolLayer.PropertyStrokeWidth))
    layer.setRenderer(QgsSingleSymbolRenderer(symbol))
    layer.triggerRepaint()
    #print("Line width set based on 'id' attribute.")
else:
    #print("Layer not found.")