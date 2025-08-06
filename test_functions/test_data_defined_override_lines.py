# Get the layer by name
temp_layer = QgsProject.instance().mapLayersByName('lines')[0]

num_classes = 4
#print(num_classes)
ramp_name = 'Reds'
#print(ramp_name)
classification_method = QgsClassificationEqualInterval()

# change format settings as necessary
format = QgsRendererRangeLabelFormat()
format.setFormat("%1 - %2")
format.setPrecision(2)
format.setTrimTrailingZeroes(True)
#print(format)
default_style = QgsStyle().defaultStyle()
color_ramp = default_style.colorRamp(ramp_name)

renderer = QgsGraduatedSymbolRenderer()
renderer.setClassAttribute("id")
renderer.setClassificationMethod(classification_method)
renderer.setLabelFormat(format)
renderer.updateClasses(temp_layer, num_classes)
renderer.updateColorRamp(color_ramp)
symbol=QgsSymbol.defaultSymbol(temp_layer.geometryType())
symbol.setWidth(2)
            
renderer.updateSymbols(symbol)

# Create a scale expression
scale = """coalesce(scale_exp("id", 1, 5, 1, 10, 0.57), 0)"""
#print(scale)

# Set the data-defined property for size on the base symbol layer
symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression(scale))
renderer.updateSymbols(symbol)
# # Define the ranges for the graduated renderer
# range1 = QgsRendererRange(0, 10, base_symbol.clone(), "0-10")  # Adjust values as needed
# range2 = QgsRendererRange(11, 20, base_symbol.clone(), "11-20")  # Adjust values as needed
# range3 = QgsRendererRange(21, 30, base_symbol.clone(), "21-30")  # Adjust values as needed

# # Add ranges to the renderer
# renderer.addClass(range1)
# renderer.addClass(range2)
# renderer.addClass(range3)

# Set the renderer to the layer
temp_layer.setRenderer(renderer)

# Refresh the layer to apply changes
temp_layer.triggerRepaint()
