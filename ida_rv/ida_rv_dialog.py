import os
from qgis.PyQt import uic, QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QDockWidget,QListWidget,QCheckBox,QSpinBox,QComboBox,QHeaderView,QWidget,QMainWindow,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit, QTableWidget,QComboBox,QTableView,QTabWidget,QRadioButton,QButtonGroup
from qgis.utils import iface

import matplotlib.pyplot as plt

from qgis.core import QgsWkbTypes,QgsProperty,QgsSymbolLayer,QgsLineSymbol,QgsSymbol,QgsGraduatedSymbolRenderer,QgsStyle,QgsTemplatedLineSymbolLayerBase,QgsMarkerSymbol,QgsSimpleMarkerSymbolLayer,QgsMarkerLineSymbolLayer,QgsRuleBasedRenderer,QgsClassificationQuantile,QgsTextFormat,QgsInterval,QgsDateTimeRange,QgsTemporalNavigationObject,QgsVectorLayerSimpleLabeling,QgsPalLayerSettings

from qgis.gui import QgsMapCanvas,QgsTemporalControllerWidget
from plugins.utility_functions.dialog import *
from plugins.utility_functions.db import *
from plugins.utility_functions.files import *
from plugins.utility_functions.topology import *
from decimal import Decimal
from qgis.PyQt import sip
from qgis.PyQt.QtGui import QFont, QColor
       

class ShowOnMapDialog(QMainWindow):
    def __init__(self,cur,dictDB,plugin_dir):     
        """Initialize GUI for path reports"""
        super().__init__()
        
        self.dictDB=dictDB
        self.plugin_dir=plugin_dir
        self.cur=cur
        self.type=''
        self.feature=''
        self.color_table_name=''
        self.size_table_name=''
        self.function_items=['Max','Min','Values','Hourly average','Daily average','Monthly average','Average','Sum','Last value','First value']
        self.time_values=['Values','Hourly average','Daily average','Monthly average']
        self.colorramps=['Magma','Blues','Cividis','Greens','Greys','Mako','RdGy','Reds','Rocket','Spectral','Turbo','Viridis']
        self.colormodes=['Equal Count','Equal Interval']
        self.process_running=False
        
        self.setWindowTitle("Show data on map")   
        widget=QWidget()

        #radio buttons Measurement data/Simulation data
        layout_rbtn_dataGroup = QHBoxLayout()
        self.group_dataGroup=QButtonGroup(widget)
        self.rbtn_simData = QRadioButton('Simulation data')
        self.rbtn_simData.setChecked(True)
        self.rbtn_mDatap = QRadioButton('Measurement data')
        #self.rbtn_mDatap.toggled.connect(self.dataGroupChanged)
        self.group_dataGroup.buttonClicked.connect(self.dataGroupChanged)

        layout_rbtn_dataGroup.addWidget(self.rbtn_simData)             
        layout_rbtn_dataGroup.addWidget(self.rbtn_mDatap)
        self.group_dataGroup.addButton(self.rbtn_simData)  
        self.group_dataGroup.addButton(self.rbtn_mDatap)      
        
        #radio buttons features
        layout_rbtn_feature = QHBoxLayout()
        self.group_feature=QButtonGroup(widget)
        self.rbtn_customers = QRadioButton('Customers')
        self.rbtn_customers.setChecked(True)
        self.rbtn_plants = QRadioButton('Energy plants')
        self.rbtn_lines = QRadioButton('Lines')
           
        layout_rbtn_feature.addWidget(self.rbtn_customers)
        layout_rbtn_feature.addWidget(self.rbtn_plants)  
        layout_rbtn_feature.addWidget(self.rbtn_lines)  
        self.group_feature.addButton(self.rbtn_customers)      
        self.group_feature.addButton(self.rbtn_plants)      
        self.group_feature.addButton(self.rbtn_lines)  
        self.group_feature.buttonClicked.connect(self.featureGroupChanged)
        
        layout_lineSegVis = QHBoxLayout()
        self.label_lineSegVis=QLabel('Line segment length for visualization, m')
        self.label_lineSegVis.setHidden(True)
        self.lineSegVis=QSpinBox()
        self.lineSegVis.setHidden(True)
        self.lineSegVis.setValue(int(loadModellingSettings(self.plugin_dir,self.dictDB)['fd_meterPerNode']))
        self.lineSegVis.setMinimum(0) 
        self.lineSegVis.setMaximum(1000) 
        layout_lineSegVis.addWidget(self.label_lineSegVis)
        layout_lineSegVis.addWidget(self.lineSegVis)
        
        
        #----Use Color ramp for GraduatedSymbolRenderer----
        layout_varColor = QVBoxLayout()
        self.checkbox_varColor=QCheckBox('Color')
        self.checkbox_varColor.stateChanged.connect(self.colorStateChanged)
        layout_varColor.addWidget(self.checkbox_varColor)
        
        #---radio buttons var/par selection---
        #--var--
        layout_colorVarSelection = QHBoxLayout()
        self.group_colorVarSelection=QButtonGroup(widget)
        self.rbtn_colorVar = QRadioButton('Variable')
        self.rbtn_colorVar.setChecked(True)
        self.rbtn_colorVar.setStyleSheet("padding-left: 30")
        self.rbtn_colorVar.setHidden(True)

        
        #variable selection
        self.color_var = QComboBox()
        self.color_var.currentTextChanged.connect(lambda signal: self.color_varChanged(signal))
        self.color_var.setHidden(True)
        #Select a function
        self.color_function = QComboBox()
        self.color_function.addItems(self.function_items)
        self.color_function.currentTextChanged.connect(lambda signal: self.color_function_Changed(signal))
        self.color_function.setHidden(True)
        
        #--par--
        self.rbtn_colorPar = QRadioButton('Parameter')
        self.rbtn_colorPar.setHidden(True)
        #parameter selection
        self.color_par = QComboBox()
        self.color_par.setHidden(True)
           
        layout_colorVarSelection.addWidget(self.rbtn_colorVar)
        layout_colorVarSelection.addWidget(self.color_var)
        layout_colorVarSelection.addWidget(self.color_function)
        layout_colorVarSelection.addWidget(self.rbtn_colorPar)  
        layout_colorVarSelection.addWidget(self.color_par)  
        self.group_colorVarSelection.addButton(self.rbtn_colorVar)      
        self.group_colorVarSelection.addButton(self.rbtn_colorPar)      
        self.group_colorVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varColor.addLayout(layout_colorVarSelection)      

        #additional color settings
        layout_additional_colorSettings=QHBoxLayout()

        layout_label_additional_colorSettings=QVBoxLayout()
        self.label_colorramp =QLabel('Color ramp')
        self.label_colorramp.setHidden(True)
        self.label_colorramp.setStyleSheet("padding-left: 30")
        self.label_color_classes =QLabel('Classes')
        self.label_color_classes.setStyleSheet("padding-left: 30")
        self.label_color_classes.setHidden(True)
        self.label_color_mode =QLabel('Mode')
        self.label_color_mode.setStyleSheet("padding-left: 30")
        self.label_color_mode.setHidden(True)
        self.label_color_label =QLabel('Label')
        self.label_color_label.setStyleSheet("padding-left: 30")
        self.label_color_label.setHidden(True)
        layout_label_additional_colorSettings.addWidget(self.label_colorramp)
        layout_label_additional_colorSettings.addWidget(self.label_color_classes)
        layout_label_additional_colorSettings.addWidget(self.label_color_mode)
        layout_label_additional_colorSettings.addWidget(self.label_color_label)

        layout_values_additional_colorSettings=QVBoxLayout()
        self.colorramp =QComboBox()
        self.colorramp.setHidden(True)
        self.colorramp.addItems(self.colorramps)
        self.color_classes =QSpinBox()
        self.color_classes.setHidden(True)
        self.color_classes.setValue(10)
        self.color_classes.setMinimum(1) 
        self.colormode =QComboBox()
        self.colormode.setHidden(True)
        self.colormode.addItems(self.colormodes)        
        self.colorlabel =QCheckBox()
        self.colorlabel.setHidden(True)
        layout_values_additional_colorSettings.addWidget(self.colorramp)
        layout_values_additional_colorSettings.addWidget(self.color_classes)
        layout_values_additional_colorSettings.addWidget(self.colormode)
        layout_values_additional_colorSettings.addWidget(self.colorlabel)
        
        layout_additional_colorSettings.addLayout(layout_label_additional_colorSettings)
        layout_additional_colorSettings.addLayout(layout_values_additional_colorSettings)
        layout_varColor.addLayout(layout_additional_colorSettings)

        #----Use Size for GraduatedSymbolRenderer----
        layout_varSize = QVBoxLayout()
        self.checkbox_varSize=QCheckBox('Size')
        self.checkbox_varSize.stateChanged.connect(self.sizeStateChanged)
        layout_varSize.addWidget(self.checkbox_varSize)
        
        #---radio buttons var/par selection---
        #--var--
        layout_sizeVarSelection = QHBoxLayout()
        self.group_sizeVarSelection=QButtonGroup(widget)
        self.rbtn_sizeVar = QRadioButton('Variable')
        self.rbtn_sizeVar.setChecked(True)
        self.rbtn_sizeVar.setStyleSheet("padding-left: 30")
        self.rbtn_sizeVar.setHidden(True)

        
        #variable selection
        self.size_var = QComboBox()
        self.size_var.currentTextChanged.connect(lambda signal: self.size_varChanged(signal))
        self.size_var.setHidden(True)
        #Select a function
        self.size_function = QComboBox()
        self.size_function.addItems(self.function_items)
        self.size_function.setHidden(True)
        self.size_function.currentTextChanged.connect(lambda signal: self.size_function_Changed(signal))

        
        #--par--
        self.rbtn_sizePar = QRadioButton('Parameter')
        self.rbtn_sizePar.setHidden(True)
        #parameter selection
        self.size_par = QComboBox()
        self.size_par.setHidden(True)
           
        layout_sizeVarSelection.addWidget(self.rbtn_sizeVar)
        layout_sizeVarSelection.addWidget(self.size_var)
        layout_sizeVarSelection.addWidget(self.size_function)
        layout_sizeVarSelection.addWidget(self.rbtn_sizePar)  
        layout_sizeVarSelection.addWidget(self.size_par)  
        self.group_sizeVarSelection.addButton(self.rbtn_sizeVar)      
        self.group_sizeVarSelection.addButton(self.rbtn_sizePar)      
        self.group_sizeVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varSize.addLayout(layout_sizeVarSelection)      

        #additional size settings
        layout_additional_sizeSettings=QHBoxLayout()

        layout_label_additional_sizeSettings=QVBoxLayout()
        self.label_size_symbolMax =QLabel('Symbol size max')
        self.label_size_symbolMax.setHidden(True)
        self.label_size_symbolMax.setStyleSheet("padding-left: 30")
        self.label_size_symbolMin =QLabel('Symbol size min')
        self.label_size_symbolMin.setHidden(True)
        self.label_size_symbolMin.setStyleSheet("padding-left: 30")

        layout_label_additional_sizeSettings.addWidget(self.label_size_symbolMax)
        layout_label_additional_sizeSettings.addWidget(self.label_size_symbolMin)


        layout_values_additional_sizeSettings=QVBoxLayout()
        self.size_symbolMax=QLineEdit('10')
        self.size_symbolMax.setHidden(True)
        self.size_symbolMin=QLineEdit('1')
        self.size_symbolMin.setHidden(True)
        layout_values_additional_sizeSettings.addWidget(self.size_symbolMax)
        layout_values_additional_sizeSettings.addWidget(self.size_symbolMin)
        
        layout_additional_sizeSettings.addLayout(layout_label_additional_sizeSettings)
        layout_additional_sizeSettings.addLayout(layout_values_additional_sizeSettings)
        layout_varSize.addLayout(layout_additional_sizeSettings)

        #----Use Rotation for GraduatedSymbolRenderer----
        layout_varRotation = QVBoxLayout()
        self.checkbox_varRotation=QCheckBox('Rotation')
        self.checkbox_varRotation.stateChanged.connect(self.rotationStateChanged)
        layout_varRotation.addWidget(self.checkbox_varRotation)
        
        #---radio buttons var/par selection---
        #--var--
        layout_rotationVarSelection = QHBoxLayout()
        self.group_rotationVarSelection=QButtonGroup(widget)
        self.rbtn_rotationVar = QRadioButton('Variable')
        self.rbtn_rotationVar.setChecked(True)
        self.rbtn_rotationVar.setStyleSheet("padding-left: 30")
        self.rbtn_rotationVar.setHidden(True)
        
        #variable selection
        self.rotation_var = QComboBox()
        self.rotation_var.currentTextChanged.connect(lambda signal: self.rotation_varChanged(signal))
        self.rotation_var.setHidden(True)
        #Select a function
        self.rotation_function = QComboBox()
        self.rotation_function.addItems(self.function_items)
        self.rotation_function.setHidden(True)
        self.rotation_function.currentTextChanged.connect(lambda signal: self.rotation_function_Changed(signal))

        
        #--par--
        self.rbtn_rotationPar = QRadioButton('Parameter')
        self.rbtn_rotationPar.setHidden(True)
        #parameter selection
        self.rotation_par = QComboBox()
        self.rotation_par.setHidden(True)
           
        layout_rotationVarSelection.addWidget(self.rbtn_rotationVar)
        layout_rotationVarSelection.addWidget(self.rotation_var)
        layout_rotationVarSelection.addWidget(self.rotation_function)
        layout_rotationVarSelection.addWidget(self.rbtn_rotationPar)  
        layout_rotationVarSelection.addWidget(self.rotation_par)  
        self.group_rotationVarSelection.addButton(self.rbtn_rotationVar)      
        self.group_rotationVarSelection.addButton(self.rbtn_rotationPar)      
        self.group_rotationVarSelection.buttonClicked.connect(self.varSelectionGroupChanged)
        layout_varRotation.addLayout(layout_rotationVarSelection)      

        #additional rotation settings
        layout_additional_rotationSettings=QHBoxLayout()

        layout_label_additional_rotationSettings=QVBoxLayout()
        self.label_rotation_symbolMax =QLabel('Rotation at max value, °')
        self.label_rotation_symbolMax.setHidden(True)
        self.label_rotation_symbolMax.setStyleSheet("padding-left: 30")
        self.label_rotation_symbolMin =QLabel('Rotation at min value, °')
        self.label_rotation_symbolMin.setHidden(True)
        self.label_rotation_symbolMin.setStyleSheet("padding-left: 30")

        layout_label_additional_rotationSettings.addWidget(self.label_rotation_symbolMax)
        layout_label_additional_rotationSettings.addWidget(self.label_rotation_symbolMin)


        layout_values_additional_rotationSettings=QVBoxLayout()
        self.rotation_symbolMax =QSpinBox()
        self.rotation_symbolMax.setHidden(True)
        self.rotation_symbolMax.setMinimum(0) 
        self.rotation_symbolMax.setMaximum(360) 
        self.rotation_symbolMax.setValue(350)
        self.rotation_symbolMin =QSpinBox()
        self.rotation_symbolMin.setHidden(True)
        self.rotation_symbolMin.setMinimum(0) 
        self.rotation_symbolMin.setMaximum(360) 
        self.rotation_symbolMin.setValue(0)
        
        layout_values_additional_rotationSettings.addWidget(self.rotation_symbolMax)
        layout_values_additional_rotationSettings.addWidget(self.rotation_symbolMin)
        
        layout_additional_rotationSettings.addLayout(layout_label_additional_rotationSettings)
        layout_additional_rotationSettings.addLayout(layout_values_additional_rotationSettings)
        layout_varRotation.addLayout(layout_additional_rotationSettings)
        
        #Layer name
        layout_layer_name=QHBoxLayout()
        label_layer_name=QLabel('Layer name')
        layout_layer_name.addWidget(label_layer_name)
        self.layer_name=QLineEdit()
        layout_layer_name.addWidget(self.layer_name)
        
        #time vor variables
        layout_timeSettings=QHBoxLayout()

        layout_label_timeSettings=QVBoxLayout()
        self.label_starttime =QLabel('Start date')
        self.label_starttime.setHidden(True)
        self.label_endtime =QLabel('End date')
        self.label_endtime.setHidden(True)
        layout_label_timeSettings.addWidget(self.label_starttime)
        layout_label_timeSettings.addWidget(self.label_endtime)
        
        layout_value_timeSettings=QVBoxLayout()
        self.starttime=QLineEdit(str(QtCore.QDate.currentDate().year())+'-01-01 00:00:00')
        self.starttime.setHidden(True)
        self.endtime=QLineEdit(str(QtCore.QDate.currentDate().year())+'-01-02 00:00:00')
        self.endtime.setHidden(True)
        layout_value_timeSettings.addWidget(self.starttime)
        layout_value_timeSettings.addWidget(self.endtime)
        
        layout_timeSettings.addLayout(layout_label_timeSettings)
        layout_timeSettings.addLayout(layout_value_timeSettings)

        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_showOnMap=QPushButton("Show on map")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_showOnMap)
        layout_btn.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_rbtn_dataGroup)
        layout.addLayout(layout_rbtn_feature)      
        layout.addLayout(layout_lineSegVis)      
        layout.addLayout(layout_varColor)      
        layout.addLayout(layout_varSize)      
        layout.addLayout(layout_varRotation)      
        layout.addLayout(layout_layer_name)
        layout.addLayout(layout_timeSettings)
        layout.addLayout(layout_btn)
        layout.addWidget(self.progress)
        layout.addStretch()
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)

    def update_finished(self, message, worker):
        """
        Called in main thread when worker finished.
        Signature: (message: str, worker: WorkerShowOnMap)
        """
        print("=== update_finished START ===", message)

        # convenience
        layer = worker.temp_layer

        # 0) make sure layer exists
        if layer is None:
            print("No layer returned from worker.")
            self.process_running = False
            return

        # 1) Ensure no edit session is open
        if layer.isEditable():
            try:
                layer.commitChanges()
                print("Committed pending edits.")
            except Exception as e:
                print("Commit error:", e)
                layer.rollBack()

        if self.colorlabel.isChecked():
            # Construct the expression for one decimal place formatting
            label_expression = f"format_number(\"{'color_' + worker.vars['color']['name'].split('$')[0]}\", 1)"

            # --- Label Settings ---
            palyr = QgsPalLayerSettings()
            palyr.enabled = True
            palyr.fieldName = label_expression 
            
            # Ensure QGIS knows this is an expression, not just a field name
            palyr.isExpression = True 
            
            # Configure placement using modern enums
            if layer.geometryType() == QgsWkbTypes.PointGeometry:
                palyr.placement = Qgis.LabelPlacement.OverPoint
            elif layer.geometryType() == QgsWkbTypes.LineGeometry:
                palyr.placement = Qgis.LabelPlacement.Line
            else: # Polygon
                palyr.placement = Qgis.LabelPlacement.AroundPoint
                # For polygons, sometimes 'centroid' placement is more reliable
                # palyr.placement = Qgis.LabelPlacement.PointOnSurface 

            # Customize text formatting (using points or millimeters is more reliable than map units)
            palyr.textColor = QColor(0, 0, 0)
            palyr.fontSizeInMapUnits = False # Use millimeters (False) or points (True and adjust unit)
            palyr.fontSize = 10 # 10 mm/points size
            palyr.fontFamily = "Arial"
            
            # Optional: Enable showing all labels, even colliding ones, for debugging
            palyr.limitLabelMapUnits = False
            palyr.scaleMax = 0
            palyr.scaleMin = 0
            palyr.displayAllLabels = True # Force display for troubleshooting


            # --- Apply Settings ---
            layer_settings = QgsVectorLayerSimpleLabeling(palyr)
            layer.setLabeling(layer_settings)
            layer.setLabelsEnabled(True)
            
            # --- Refresh Map Canvas ---
            # Trigger a repaint to force QGIS to re-render the labels immediately
            layer.triggerRepaint() 
            iface.mapCanvas().refresh()
            print(f"Labels enabled for layer '{layer.name()}' using expression: {label_expression}")


        # ===== BUILD RENDERER (in main thread!) =====
        print("Building renderer in main thread...")
        renderer = None

        if worker.vars['color']['mode']:
            # target field name used for graduated renderer
            target_field = 'color_' + worker.vars['color']['name'].split('$')[0]
            print("Renderer target field:", target_field)
            
            

            if worker.vars['color']['name'].split('$')[0] == 'mdot':
                # --- mdot: rule-based renderer with arrows (positive / negative)
                attr = "color_mdot"
                arrow_size = 3
                num_classes = int(self.color_classes.text())
                classification_mode = self.colormode.currentText()
                color_ramp_name = self.colorramp.currentText()

                style_mgr = QgsStyle().defaultStyle()
                ramp = style_mgr.colorRamp(color_ramp_name)
                if ramp is None:
                    raise ValueError(f"Color ramp '{color_ramp_name}' not found in QGIS Style Manager")

                # compute vals (absolute) and bounds
                vals = [abs(f[attr]) for f in layer.getFeatures() if f[attr] is not None]
                if not vals:
                    # fallback: set single-class renderer
                    print("No values for attr", attr, " -> single symbol")
                    renderer = QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(layer.geometryType()))
                else:
                    vmin, vmax = min(vals), max(vals)
                    if vmin == vmax:
                        # degenerate case -> single class
                        bounds = [vmin, vmax]
                        num_classes = 1
                    else:
                        if classification_mode == 'Equal Count':
                            percentiles = np.linspace(0, 100, num_classes + 1)
                            bounds = np.percentile(vals, percentiles).tolist()
                        else:
                            step = (vmax - vmin) / num_classes
                            bounds = [vmin + i * step for i in range(num_classes + 1)]

                    root_rule = QgsRuleBasedRenderer.Rule(None)

                    for i_cls in range(num_classes):
                        lower = bounds[i_cls]
                        upper = bounds[i_cls + 1]
                        frac = i_cls / (num_classes - 1) if num_classes > 1 else 0.0
                        color = ramp.color(frac)

                        # Positive flows
                        expr_pos = f'("{attr}" >= {lower} AND "{attr}" < {upper} AND "{attr}" > 0)'
                        line_sym_pos = QgsLineSymbol.createSimple({'color': color.name(), 'width': '0.7'})

                        marker_line_pos = QgsMarkerLineSymbolLayer()
                        # try to use newer API if available
                        if hasattr(marker_line_pos, "setPlacementType"):
                            marker_line_pos.setPlacementType(QgsTemplatedLineSymbolLayerBase.CentralPoint)
                        else:
                            marker_line_pos.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                        # rotate according to line direction
                        marker_line_pos.setDataDefinedProperty(QgsSymbolLayer.PropertyAngle, QgsProperty.fromValue(True))

                        arrow_layer_pos = QgsSimpleMarkerSymbolLayer(
                            shape=QgsSimpleMarkerSymbolLayer.Triangle,
                            color=color,
                            size=arrow_size
                        )
                        arrow_layer_pos.setAngle(90)  # rightward
                        arrow_marker_pos = QgsMarkerSymbol()
                        arrow_marker_pos.changeSymbolLayer(0, arrow_layer_pos)
                        marker_line_pos.setSubSymbol(arrow_marker_pos)
                        line_sym_pos.appendSymbolLayer(marker_line_pos)

                        rule_pos = QgsRuleBasedRenderer.Rule(line_sym_pos)
                        rule_pos.setFilterExpression(expr_pos)
                        rule_pos.setLabel(f"{lower:.2f} – {upper:.2f}")
                        root_rule.appendChild(rule_pos)

                        # Negative flows
                        expr_neg = f'("{attr}" >= -{upper} AND "{attr}" < -{lower} AND "{attr}" < 0)'
                        line_sym_neg = QgsLineSymbol.createSimple({'color': color.name(), 'width': '0.7'})

                        marker_line_neg = QgsMarkerLineSymbolLayer()
                        if hasattr(marker_line_neg, "setPlacementType"):
                            marker_line_neg.setPlacementType(QgsTemplatedLineSymbolLayerBase.CentralPoint)
                        else:
                            marker_line_neg.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                        marker_line_neg.setDataDefinedProperty(QgsSymbolLayer.PropertyAngle, QgsProperty.fromValue(True))

                        arrow_layer_neg = QgsSimpleMarkerSymbolLayer(
                            shape=QgsSimpleMarkerSymbolLayer.Triangle,
                            color=color,
                            size=arrow_size
                        )
                        arrow_layer_neg.setAngle(270)  # leftward
                        arrow_marker_neg = QgsMarkerSymbol()
                        arrow_marker_neg.changeSymbolLayer(0, arrow_layer_neg)
                        marker_line_neg.setSubSymbol(arrow_marker_neg)
                        line_sym_neg.appendSymbolLayer(marker_line_neg)

                        rule_neg = QgsRuleBasedRenderer.Rule(line_sym_neg)
                        rule_neg.setFilterExpression(expr_neg)
                        rule_neg.setLabel("")  # hidden
                        root_rule.appendChild(rule_neg)

                    renderer = QgsRuleBasedRenderer(root_rule)

            else:
                # --- Graduated renderer branch ---
                if self.colormode.currentText() == 'Equal Count':
                    classification_method = QgsClassificationQuantile()
                else:
                    classification_method = QgsClassificationEqualInterval()
                classification_method.setLabelPrecision(1)
                classification_method.setLabelTrimTrailingZeroes(True)

                default_style = QgsStyle().defaultStyle()
                color_ramp = default_style.colorRamp(self.colorramp.currentText())

                renderer = QgsGraduatedSymbolRenderer()
                renderer.setClassAttribute(target_field)
                renderer.setClassificationMethod(classification_method)
                renderer.updateClasses(layer, int(self.color_classes.text()))
                renderer.updateColorRamp(color_ramp)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                if self.feature == 'line':
                    symbol.setWidth(2)
                else:
                    symbol.setSize(4)
                renderer.updateSymbols(symbol)

        else:
            # no color mode -> single symbol
            renderer = QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(layer.geometryType()))

        # ===== SIZE / ROTATION data-defined properties (apply to marker symbol) =====
        # Note: we need to modify a symbol for the renderer. For rule-based renderer, modify
        # top-level symbol in case of single-symbol rules; for graduated renderer we update symbols.
        try:
            if worker.vars['size']['mode'] or worker.vars['rotation']['mode']:
                print("Applying size/rotation DDPs...")
                # create a base symbol to apply changes to
                base_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                style = {}
                if self.checkbox_varRotation.isChecked():
                    style['name'] = 'arrow'
                else:
                    style['name'] = 'point'
                style['color'] = 'black'
                symbolLayer = QgsFilledMarkerSymbolLayer.create(style)
                base_symbol.changeSymbolLayer(0, symbolLayer)

                # size scale
                if worker.vars['size']['mode']:
                    if worker.vars['size']['mode'] == 'var':
                        min_value = getMinTimeTableValue(worker.vars['size']['var_function'], worker.cur, self.dictDB, worker.vars['size']['table_name'], worker.vars['size']['name'].split('$')[0], worker.vars['time']['starttime'], worker.vars['time']['endtime'])
                        max_value = getMaxTimeTableValue(worker.vars['size']['var_function'], worker.cur, self.dictDB, worker.vars['size']['table_name'], worker.vars['size']['name'].split('$')[0], worker.vars['time']['starttime'], worker.vars['time']['endtime'])
                    else:
                        min_value = getMinTableValue(worker.cur, self.dictDB, worker.vars['size']['table_name'], worker.vars['size']['name'])
                        max_value = getMaxTableValue(worker.cur, self.dictDB, worker.vars['size']['table_name'], worker.vars['size']['name'])

                    scale_expr = """coalesce(scale_exp("{}", {}, {}, {}, {}, 0.57), 0)""".format(
                        'size_' + worker.vars['size']['name'].split('$')[0],
                        min_value, max_value,
                        float(self.size_symbolMin.text()), float(self.size_symbolMax.text())
                    )
                    # property for size or stroke width
                    prop = QgsSymbolLayer.PropertyStrokeWidth if self.feature == 'line' else QgsSymbolLayer.PropertySize
                    base_symbol.symbolLayer(0).setDataDefinedProperty(prop, QgsProperty.fromExpression(scale_expr))

                # rotation
                if worker.vars['rotation']['mode']:
                    if worker.vars['rotation']['mode'] == 'var':
                        min_value = getMinTimeTableValue(worker.vars['rotation']['var_function'], worker.cur, self.dictDB, worker.vars['rotation']['table_name'], worker.vars['rotation']['name'].split('$')[0], worker.vars['time']['starttime'], worker.vars['time']['endtime'])
                        max_value = getMaxTimeTableValue(worker.vars['rotation']['var_function'], worker.cur, self.dictDB, worker.vars['rotation']['table_name'], worker.vars['rotation']['name'].split('$')[0], worker.vars['time']['starttime'], worker.vars['time']['endtime'])
                    else:
                        min_value = getMinTableValue(worker.cur, self.dictDB, worker.vars['rotation']['table_name'], worker.vars['rotation']['name'])
                        max_value = getMaxTableValue(worker.cur, self.dictDB, worker.vars['rotation']['table_name'], worker.vars['rotation']['name'])

                    rotation_expr = """coalesce(scale_exp("{}", {}, {}, {}, {}, 0.57), 0)""".format(
                        'rotation_' + worker.vars['rotation']['name'].split('$')[0],
                        min_value, max_value,
                        float(self.rotation_symbolMin.text()), float(self.rotation_symbolMax.text())
                    )
                    base_symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyAngle, QgsProperty.fromExpression(rotation_expr))

                # apply the base symbol to renderer
                try:
                    renderer.updateSymbols(base_symbol)
                except Exception:
                    renderer.setSymbol(base_symbol)

        except Exception as e:
            print("Error applying size/rotation:", e)

        # ===== APPLY RENDERER (after labeling) =====
        try:
            print("Applying renderer to layer...")
            layer.setRenderer(renderer)
        except Exception as e:
            print("Error setting renderer:", e)

        # ===== ADD TO PROJECT =====
        print("Adding layer to project...")
        QgsProject.instance().addMapLayer(layer)

        # ===== FINAL REFRESH =====
        layer.triggerRepaint()
        try:
            iface.layerTreeView().refreshLayerSymbology(layer.id())
        except Exception:
            pass
        iface.mapCanvas().refresh()

        # ===== TEMPORAL CONTROLLER (if applicable) =====
        if worker.first_time_var:
            print("Configuring temporal controller...")
            # set temporal properties on the layer
            temp_prop = layer.temporalProperties()
            temp_prop.setIsActive(True)
            temp_prop.setStartField('time')
            temp_prop.setEndField('time')
            temp_prop.setLimitMode(Qgis.VectorTemporalLimitMode.IncludeBeginIncludeEnd)
            temp_prop.setMode(Qgis.VectorTemporalMode(2))

            temporalController = iface.mapCanvas().temporalController()
            temporalNavigationObject = sip.cast(temporalController, QgsTemporalNavigationObject)

            temporalNavigationObject.setNavigationMode(Qgis.TemporalNavigationMode.Animated)
            temporalNavigationObject.setFramesPerSecond(2)
            temporalNavigationObject.setTemporalExtents(
                QgsDateTimeRange(
                    getDatetimeFromString(worker.vars['time']['starttime']),
                    getDatetimeFromString(worker.vars['time']['endtime'])
                )
            )
            temporalNavigationObject.setLooping(True)
            temporalNavigationObject.setAnimationState(Qgis.AnimationState.Forward)

            interval = QgsInterval()
            dt = worker.vars['time']['dt']
            if dt == 'hour':
                interval.setHours(1)
            elif dt == 'day':
                interval.setDays(1)
            elif dt == 'month':
                interval.setMonths(1)
            else:
                try:
                    interval.setHours(float(dt))
                except Exception:
                    interval.setHours(1)

            temporalNavigationObject.setFrameDuration(interval)
            iface.mapCanvas().refresh()

        print("=== update_finished END ===")
        self.process_running = False

        
    def colorStateChanged(self,s):
        if Qt.Checked==s:
            print('checked')
            self.rbtn_colorVar.setHidden(False)
            self.color_var.setHidden(False)
            self.color_function.setHidden(False)
            self.rbtn_colorPar.setHidden(False)
            self.color_par.setHidden(False)
            self.label_colorramp.setHidden(False)
            self.label_color_classes.setHidden(False)
            self.label_color_mode.setHidden(False)
            self.label_color_label.setHidden(False)
            self.colorramp.setHidden(False)
            self.color_classes.setHidden(False)
            self.colormode.setHidden(False)
            self.colorlabel.setHidden(False)
                
        else:
            print('unckecked')
            self.rbtn_colorVar.setHidden(True)
            self.color_var.setHidden(True)
            self.color_function.setHidden(True)
            self.color_par.setHidden(True)
            self.rbtn_colorPar.setHidden(True)
            self.label_colorramp.setHidden(True)
            self.label_color_classes.setHidden(True)
            self.label_color_mode.setHidden(True)
            self.label_color_label.setHidden(True)
            self.colorramp.setHidden(True)
            self.color_classes.setHidden(True)
            self.colormode.setHidden(True)
            self.colorlabel.setHidden(True)
        self.varSelectionGroupChanged(False)

    def varSelectionGroupChanged(self,radioButton):
        print('radio var/par changed')
        if self.rbtn_colorVar.isChecked() and self.checkbox_varColor.isChecked() or self.rbtn_sizeVar.isChecked() and self.checkbox_varSize.isChecked() or self.rbtn_rotationVar.isChecked() and self.checkbox_varRotation.isChecked():
            if self.label_endtime.isHidden():
                self.label_endtime.setHidden(False)
                self.label_starttime.setHidden(False)
                self.starttime.setHidden(False)
                self.endtime.setHidden(False)
        else:
            if not self.label_endtime.isHidden():
                self.label_endtime.setHidden(True)
                self.label_starttime.setHidden(True)
                self.starttime.setHidden(True)
                self.endtime.setHidden(True)

    def sizeStateChanged(self,s):
        if Qt.Checked==s:
            print('checked')
            self.rbtn_sizeVar.setHidden(False)
            self.size_var.setHidden(False)
            self.size_function.setHidden(False)
            self.rbtn_sizePar.setHidden(False)
            self.size_par.setHidden(False)
            self.label_size_symbolMax.setHidden(False)
            self.label_size_symbolMin.setHidden(False)
            self.size_symbolMax.setHidden(False)
            self.size_symbolMin.setHidden(False)

        else:
            print('unckecked')
            self.rbtn_sizeVar.setHidden(True)
            self.size_var.setHidden(True)
            self.size_function.setHidden(True)
            self.rbtn_sizePar.setHidden(True)
            self.size_par.setHidden(True)
            self.label_size_symbolMax.setHidden(True)
            self.label_size_symbolMin.setHidden(True)
            self.size_symbolMax.setHidden(True)
            self.size_symbolMin.setHidden(True)
        self.varSelectionGroupChanged(False)

    def rotationStateChanged(self,s):
        if Qt.Checked==s:
            print('checked')
            self.rbtn_rotationVar.setHidden(False)
            self.rotation_var.setHidden(False)
            self.rotation_function.setHidden(False)
            self.rbtn_rotationPar.setHidden(False)
            self.rotation_par.setHidden(False)
            self.label_rotation_symbolMax.setHidden(False)
            self.label_rotation_symbolMin.setHidden(False)
            self.rotation_symbolMax.setHidden(False)
            self.rotation_symbolMin.setHidden(False)

        else:
            print('unckecked')
            self.rbtn_rotationVar.setHidden(True)
            self.rotation_var.setHidden(True)
            self.rotation_function.setHidden(True)
            self.rbtn_rotationPar.setHidden(True)
            self.rotation_par.setHidden(True)
            self.label_rotation_symbolMax.setHidden(True)
            self.label_rotation_symbolMin.setHidden(True)
            self.rotation_symbolMax.setHidden(True)
            self.rotation_symbolMin.setHidden(True)
        self.varSelectionGroupChanged(False)
            
    def hideRotationWidgets(self):
        self.rbtn_rotationVar.setHidden(True)
        self.rotation_var.setHidden(True)
        self.rotation_function.setHidden(True)
        self.rbtn_rotationPar.setHidden(True)
        self.rotation_par.setHidden(True)
        self.label_rotation_symbolMax.setHidden(True)
        self.label_rotation_symbolMin.setHidden(True)
        self.rotation_symbolMax.setHidden(True)
        self.rotation_symbolMin.setHidden(True)
            
    def displayRotationWidgets(self):
        self.rbtn_rotationVar.setHidden(False)
        self.rotation_var.setHidden(False)
        self.rotation_function.setHidden(False)
        self.rbtn_rotationPar.setHidden(False)
        self.rotation_par.setHidden(False)
        self.label_rotation_symbolMax.setHidden(False)
        self.label_rotation_symbolMin.setHidden(False)
        self.rotation_symbolMax.setHidden(False)
        self.rotation_symbolMin.setHidden(False)

    def hideSizeWidgets(self):
        self.rbtn_sizeVar.setHidden(True)
        self.size_var.setHidden(True)
        self.size_function.setHidden(True)
        self.rbtn_sizePar.setHidden(True)
        self.size_par.setHidden(True)
        self.label_size_symbolMax.setHidden(True)
        self.label_size_symbolMin.setHidden(True)
        self.size_symbolMax.setHidden(True)
        self.size_symbolMin.setHidden(True)
            
    def displaySizeWidgets(self):
        self.rbtn_sizeVar.setHidden(False)
        self.size_var.setHidden(False)
        self.size_function.setHidden(False)
        self.rbtn_sizePar.setHidden(False)
        self.size_par.setHidden(False)
        self.label_size_symbolMax.setHidden(False)
        self.label_size_symbolMin.setHidden(False)
        self.size_symbolMax.setHidden(False)
        self.size_symbolMin.setHidden(False)
            
    def hideRotationLayout(self):
        self.checkbox_varRotation.setHidden(True)
        self.hideRotationWidgets()

    def hideSizeLayout(self):
        self.checkbox_varSize.setHidden(True)
        self.checkbox_varSize.setChecked(False)
        self.hideSizeWidgets()

    def displayRotationLayout(self):
        self.checkbox_varRotation.setHidden(False)
        if self.checkbox_varRotation.isChecked():
            self.displayRotationWidgets()
    
    def displaySizeLayout(self):
        self.checkbox_varSize.setHidden(False)
        if self.checkbox_varSize.isChecked():
            self.displaySizeWidgets()
        
    def color_function_Changed(self,s):
        if s in self.time_values:
            if self.size_function.currentText() in self.time_values:
                self.size_function.setCurrentText(s) 
            if self.rotation_function.currentText() in self.time_values:
                self.rotation_function.setCurrentText(s) 
    
    def size_function_Changed(self,s):
        if s in self.time_values:
            if self.color_function.currentText() in self.time_values:
                self.color_function.setCurrentText(s) 
            if self.rotation_function.currentText() in self.time_values:
                self.rotation_function.setCurrentText(s) 
            
    def rotation_function_Changed(self,s):
        if s in self.time_values:
            if self.size_function.currentText() in self.time_values:
                self.size_function.setCurrentText(s) 
            if self.color_function.currentText() in self.time_values:
                self.color_function.setCurrentText(s) 
        
    def color_varChanged(self,s):
        self.color_function.clear()
        self.color_function.addItems(self.function_items)
        if s.split('$')[0]=='p':
            self.color_function.addItem('specific dp')
                
        if s.split('$')[0]=='mdot' and self.rbtn_lines.isChecked():
            self.hideSizeLayout()
        else:
            self.displaySizeLayout()
            
        self.color_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.dictDB['versionName'],self.color_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')
            
    def size_varChanged(self,s):
        self.size_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.dictDB['versionName'],self.size_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')
            
    def rotation_varChanged(self,s):
        self.rotation_table_name=self.feature+'_'+self.type+'_'+s
        sql="""SELECT min(time), max(time) FROM "{}".{};""".format(self.dictDB['versionName'],self.rotation_table_name)
        try:
            self.cur.execute(sql)
            time=self.cur.fetchone()
            try:
                current_min_time=getDatetimeFromString(self.label_starttime.text().split('min value=')[1][:-1])
                current_max_time=getDatetimeFromString(self.label_endtime.text().split('max value=')[1][:-1])
                if current_min_time>time['min']:
                    self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                    self.starttime.setText(str(time['min']))
                if current_max_time<time['min']:
                    self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                    self.endtime.setText(str(time['max']))
            except:
                self.label_starttime.setText('Start time, h (min value='+str(time['min'])+')')
                self.starttime.setText(str(time['min']))
                self.label_endtime.setText('End time, h (max value='+str(time['max'])+')')
                self.endtime.setText(str(time['max']))
        except:
            self.label_starttime.setText('Start time, h')
            self.label_endtime.setText('End time, h')

    def dataGroupChanged(self,radioButto):
        self.featureGroupChanged(False)

    def featureGroupChanged(self,radioButto):
        self.color_var.clear()
        self.color_par.clear()
        self.size_var.clear()
        self.size_par.clear()
        self.rotation_var.clear()
        self.rotation_par.clear()
        if self.rbtn_mDatap.isChecked():
            print('Measurement data')
            self.type='m'
        elif self.rbtn_simData.isChecked():
            self.type='s'
        if self.rbtn_customers.isChecked():
            print('Customers')
            self.feature='customer'
            vars=getResultVars(self.cur,self.dictDB,self.feature,self.type)
            pars=getTableAttr(self.cur,self.dictDB,self.feature)
            print(vars)
            self.displayRotationLayout()
            self.label_lineSegVis.setHidden(True)
            self.lineSegVis.setHidden(True)
            self.displaySizeLayout()
        elif self.rbtn_plants.isChecked():
            print('Energy plants')
            self.feature='energy_plant'
            vars=getResultVars(self.cur,self.dictDB,self.feature,self.type)
            pars=getTableAttr(self.cur,self.dictDB,self.feature)
            self.displayRotationLayout()
            self.label_lineSegVis.setHidden(True)
            self.lineSegVis.setHidden(True)
            self.displaySizeLayout()
        elif self.rbtn_lines.isChecked():
            print('Lines')
            self.feature='line'
            vars=getResultVars(self.cur,self.dictDB,self.feature,self.type)
            pars=getTableAttr(self.cur,self.dictDB,self.feature)
            self.label_lineSegVis.setHidden(False)
            self.lineSegVis.setHidden(False)
            #hide rotation
            self.hideRotationLayout()
            self.checkbox_varRotation.setChecked(False)
            
        self.color_var.addItems(vars)
        self.color_par.addItems(pars)
        self.size_var.addItems(vars)
        self.size_par.addItems(pars)
        self.rotation_var.addItems(vars)
        self.rotation_par.addItems(pars)
        
class IDADistrictsPathReportsDialog(QMainWindow):
    def __init__(self,cur,dictDB):     
        """Initialize GUI for path reports"""
        super().__init__()
        self.setWindowTitle("Path reports")   
        widget=QWidget()
        self.cur=cur
        self.dictDB=dictDB
        self.title=None
        self.lids=None
        self.weak_point=None
        self.path=None
        self.line_data=None

        #set quantity 
        #title
        label_titel =QLabel('Quantity')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Temp/pressure
        layout_rbtn_quantity = QHBoxLayout()
        group_quantity=QButtonGroup(widget)
        self.rbtn_pathTemp = QRadioButton('Temperature')
        self.rbtn_pathPressure = QRadioButton('Pressure')
        self.rbtn_pathPressure.setChecked(True)
           
        layout_rbtn_quantity.addWidget(self.rbtn_pathPressure)  
        layout_rbtn_quantity.addWidget(self.rbtn_pathTemp)
        group_quantity.addButton(self.rbtn_pathTemp)      
        group_quantity.addButton(self.rbtn_pathPressure)      
        
        quantity_info=QLabel('Info: Please select Pressure distribution/temperature in nodes, Substation pressure/Substation connection temperatures and Plant pressure/Plant connection temperatures before simulation in order to generate path reports.')
        
        layout_quantity = QVBoxLayout()
        layout_quantity.addWidget(label_titel)
        layout_quantity.addLayout(layout_rbtn_quantity)
        layout_quantity.addWidget(quantity_info)
        
        #Date 
        #title
        label_titel =QLabel('Date')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Date/Max value
        layout_rbtn_date = QHBoxLayout()
        self.rbtn_maxValue = QRadioButton('Max value')
        self.rbtn_maxValue.setChecked(True)
        self.rbtn_Date = QRadioButton('Date (yyyy-MM-dd HH:mm:ss)')
           
        layout_rbtn_date.addWidget(self.rbtn_maxValue)
        layout_rbtn_date.addWidget(self.rbtn_Date) 
        group_date=QButtonGroup(widget)
        group_date.addButton(self.rbtn_maxValue)      
        group_date.addButton(self.rbtn_Date)  

        self.date_input = QLineEdit()

        layout_date = QVBoxLayout()
        layout_date.addWidget(label_titel)
        layout_date.addLayout(layout_rbtn_date)        
        layout_date.addWidget(self.date_input)        
        
        #Path 
        #title
        label_titel =QLabel('Path')
        font=label_titel.font()
        font.setPointSize(15)
        label_titel.setFont(font)
        #radio buttons Line ID/Weak point
        layout_rbtn_path = QHBoxLayout()
        self.rbtn_weakPoint = QRadioButton('Weak point (customers)')
        self.rbtn_weakPoint.setChecked(True)
        self.rbtn_lineIds = QRadioButton('Line ID`s')
        self.rbtn_customer = QRadioButton('Customer ID`s')
        self.rbtn_energy_plant = QRadioButton('Energy plant ID`s')
           
        layout_rbtn_path.addWidget(self.rbtn_weakPoint) 
        layout_rbtn_path.addWidget(self.rbtn_lineIds)
        layout_rbtn_path.addWidget(self.rbtn_customer) 
        layout_rbtn_path.addWidget(self.rbtn_energy_plant) 
        self.group_path=QButtonGroup(widget)
        self.group_path.addButton(self.rbtn_weakPoint,1)  
        self.group_path.addButton(self.rbtn_lineIds,2)      
        self.group_path.addButton(self.rbtn_customer,3)  
        self.group_path.addButton(self.rbtn_energy_plant,4)  
        self.group_path.buttonClicked[int].connect(self.on_group_path_clicked)
        
        
        self.listWidget_ids= QListWidget()
        self.listWidget_ids.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        layout_network_settings=QHBoxLayout()
        #labels
        layout_network_settings_labels=QVBoxLayout()
        label_network =QLabel('Network')
        layout_network_settings_labels.addWidget(label_network)
        label_main_plant =QLabel('Plant')
        layout_network_settings_labels.addWidget(label_main_plant)
        label_conntype =QLabel('Connection type')
        layout_network_settings_labels.addWidget(label_conntype)
        label_sup_sequences =QLabel('Supply sequence')
        layout_network_settings_labels.addWidget(label_sup_sequences)
        label_ret_sequences =QLabel('Return sequence')
        layout_network_settings_labels.addWidget(label_ret_sequences)
        label_conntype =QLabel('Feature connection bundle type')
        layout_network_settings_labels.addWidget(label_conntype)
        label_conntype =QLabel('Feature connection type')
        layout_network_settings_labels.addWidget(label_conntype)
        self.dp_recalc =QCheckBox('Recalculate supply pressure value with dp min, bar')
        layout_network_settings_labels.addWidget(self.dp_recalc)
        
        #input
        layout_network_settings_values=QVBoxLayout()
        self.network = QComboBox()
        self.network.currentTextChanged.connect(self.network_changed)
        layout_network_settings_values.addWidget(self.network)
        self.main_plant = QComboBox()
        self.main_plant.currentTextChanged.connect(self.main_plant_changed)
        layout_network_settings_values.addWidget(self.main_plant)
        self.conn_type = QComboBox()
        self.conn_type.currentTextChanged.connect(self.conn_type_changed)
        layout_network_settings_values.addWidget(self.conn_type)
        self.sup_sequence =QComboBox()
        layout_network_settings_values.addWidget(self.sup_sequence)
        self.ret_sequence =QComboBox()
        layout_network_settings_values.addWidget(self.ret_sequence)
        self.f_conn_bundle_type = QComboBox()
        layout_network_settings_values.addWidget(self.f_conn_bundle_type)
        self.f_conn_bundle_type.currentTextChanged.connect(self.f_conn_bundle_type_changed)
        self.f_conn_type = QComboBox()
        layout_network_settings_values.addWidget(self.f_conn_type)
        self.dp_min_recalc = QLineEdit()
        layout_network_settings_values.addWidget(self.dp_min_recalc)
        
        layout_network_settings.addLayout(layout_network_settings_labels)
        layout_network_settings.addLayout(layout_network_settings_values)
        
        #buttons
        layout_btn_list = QHBoxLayout()
        self.btn_addID=QPushButton("Add ID")
        self.btn_addSelectedIDs=QPushButton("Add selected ID`s from map")
        self.btn_deleteIDs=QPushButton("Delete ID`s")
        layout_btn_list.addWidget(self.btn_addID)
        layout_btn_list.addWidget(self.btn_addSelectedIDs)
        layout_btn_list.addWidget(self.btn_deleteIDs)
        
        layout_path = QVBoxLayout()
        layout_path.addWidget(label_titel)
        layout_path.addLayout(layout_rbtn_path)  
        layout_path.addWidget(self.listWidget_ids)
        layout_path.addLayout(layout_network_settings)
        layout_path.addLayout(layout_btn_list)

        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_ok)
        layout_btn.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_quantity)
        layout.addLayout(layout_date)      
        layout.addLayout(layout_path)      
        layout.addLayout(layout_btn)
        layout.addWidget(self.progress)
        layout.addStretch()
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
        f_conn_types = getConnBundlesByType(self.cur,self.dictDB,'customer')
        self.f_conn_bundle_type.addItems(f_conn_types)

    def add_combo_items(self, combo, new_items):
        print('add combo:'+str(new_items))

        # Add missing items
        for item in new_items:
            if combo.findText(item) == -1:
                combo.addItem(item)
 
    def on_group_path_clicked(self,id):
        print('on_group_path_clicked: '+str(id))

        self.f_conn_bundle_type.clear()
        f_conn_types = getConnBundlesByType(self.cur,self.dictDB,'customer' if id in (1,2,3) else 'energy_plant')
        self.add_combo_items(self.f_conn_bundle_type,f_conn_types)
        if id==2:
            f_conn_types = getConnBundlesByType(self.cur,self.dictDB,'energy_plant')
            self.add_combo_items(self.f_conn_bundle_type,f_conn_types)
    
    def f_conn_bundle_type_changed(self,s):
        print('f_conn_bundle_type changed: '+str(s))
        if self.f_conn_bundle_type.currentText():
            self.f_conn_type.clear() 
            self.f_conn_type.addItems(getConnTypesByConnBundleType(self.cur,self.dictDB,self.f_conn_bundle_type.currentText()))    
        
    def network_changed(self,s):
        print(s)
        epids=getPlantIds(self.cur,self.dictDB,network=s)
        print(epids)
        self.main_plant.clear()
        self.main_plant.addItems(epids)

    def main_plant_changed(self,s):
        print(s)
        conn_types=getConnTypesByFeature(self.cur,self.dictDB,'energy_plant',s)
        print(conn_types)
        self.conn_type.clear()
        self.conn_type.addItems(conn_types)
        
    def conn_type_changed(self,s):
        print(s)
        sequences=getConnSequencesByConnType(self.cur,s)
        print(sequences)
        self.sup_sequence.clear()
        self.sup_sequence.addItems(sequences)
        self.ret_sequence.clear()
        self.ret_sequence.addItems(sequences)
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def update_finished(self,message):
        if str(message)=='finished':
            self.showplot()
            #select lids in lines
            lines_layer=QgsProject.instance().mapLayersByName('lines')   
            if lines_layer:             
                lines_layer[0].selectByExpression("id in {}".format(tuple([lid[0] for lid in self.lids])))
            
        self.process_running=False
        
    def showplot(self):
        print('show plot')
        if self.dp_recalc.isChecked() and self.rbtn_pathPressure.isChecked():
            print(self.dp_min_recalc.text())
            ddp=self.weak_point['sup_f'] - self.weak_point['ret_f']-Decimal(self.dp_min_recalc.text())*100000
        else:
            ddp=0
        print(ddp)

        print(self.weak_point)
        print(self.line_data)
        quantity_data_sup=[self.weak_point['sup_ep']-ddp]+[lid['var1']-ddp for lid in self.line_data]+[self.weak_point['sup_f']-ddp]
        quantity_data_ret=[self.weak_point['ret_ep']]+[lid['var2'] for lid in self.line_data]+[self.weak_point['ret_f']]
        height=[self.weak_point['height_ep']]+[lid['height_j'] for lid in self.line_data]+[self.weak_point['height_f']]

        print(height)
        print(quantity_data_sup)
        print(quantity_data_ret)
        print(self.path)
        
        SMALL_SIZE = 15
        MEDIUM_SIZE = 20
        BIGGER_SIZE = 25

        plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
        plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
        plt.rc('figure', titlesize=MEDIUM_SIZE)  # fontsize of the figure title
        plt.rc('figure', figsize=(30.0, 20.0))  # fontsize of the figure title
        
        fig, (ax1, ax2) = plt.subplots(2, 1)
        fig.suptitle(self.title)
        ax1.plot(self.path, quantity_data_sup, linewidth=4.0)
        ax1.plot(self.path, quantity_data_ret, linewidth=4.0)
        ax1.grid(True)
        
        #ax1.set_xlabel('Length, m')
        ax1.set_xlabel('Trasse, m')
        if self.rbtn_pathPressure.isChecked():
            #ax1.set_ylabel('Pressure, Pa')
            ax1.set_ylabel('Druck, Pa')
        else:
            #ax1.set_ylabel('Temperature, °C')
            ax1.set_ylabel('Temperatur, °C')
            
        ax2.plot(self.path, height,linewidth=3.0)    
        #ax2.set_xlabel('Length, m')
        ax2.set_xlabel('Trasse, m')
        #ax2.set_ylabel('Height level, m')
        ax2.set_ylabel('Höhenprofil, m')
        ax2.grid(True)
        
        manager = plt.get_current_fig_manager()
        manager.window.showMaximized()
        plt.show() 
        
class IDADistrictsResultVisualizationDialog(QMainWindow):
    def __init__(self):     
        """Initialize GUI for result visualization"""
        super().__init__()
        self.setWindowTitle("Result Visualization")   
        
        #buttons     
        self.btn_network_report=QPushButton("Network report")
        self.btn_path_reports=QPushButton("Path reports")
        self.btn_plotLoadProfiles=QPushButton("Plot feature load profiles")
        self.btn_importMeasurements=QPushButton("Import measurement data")
        self.btn_showDataOnMap=QPushButton("Show data on map")
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addWidget(self.btn_network_report)
        layout.addWidget(self.btn_path_reports)
        layout.addWidget(self.btn_plotLoadProfiles)
        layout.addWidget(self.btn_importMeasurements)
        layout.addWidget(self.btn_showDataOnMap)
        layout.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
class PlotLoadProfilesDialog(QMainWindow):
    def __init__(self):     
        """Initialize GUI for plotting load profiles"""
        super().__init__()
        self.setWindowTitle("Plot features load profiles")   
        
        #Select network with checkable combobox
        layout_network=QHBoxLayout()
        label_network =QLabel("Network")
        layout_network.addWidget(label_network)
        self.combo_networks = CheckableComboBox()
        layout_network.addWidget(self.combo_networks)       
        
        #Select feature type by radio button 
        layout_rbtn_feature_type = QHBoxLayout()
        self.rbtn_customer = QRadioButton('Customers')
        self.rbtn_customer.setChecked(True)
        self.rbtn_energy_plant = QRadioButton('Energy plants')
           
        layout_rbtn_feature_type.addWidget(self.rbtn_customer)
        layout_rbtn_feature_type.addWidget(self.rbtn_energy_plant)
        
        #Feature ID`s list
        self.listWidget_ids= QListWidget()
        self.listWidget_ids.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_plot=QPushButton("Plot selected features data")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_plot)
        layout_btn.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_network)
        layout.addLayout(layout_rbtn_feature_type)
        layout.addWidget(self.listWidget_ids)
        layout.addLayout(layout_btn)
        layout.addStretch()
        
        widget=QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
class ImportMeasuremntsDialog(QMainWindow):
    def __init__(self):     
        """Initialize GUI for plotting load profiles"""
        super().__init__()
        self.setWindowTitle("Import measurement data into DB")   
        widget=QWidget()
                
        layout_data_source=QHBoxLayout()
        label_source =QLabel("Data source")
        layout_data_source.addWidget(label_source) 
        
        self.lineEditSourceName =QLineEdit("")
        layout_data_source.addWidget(self.lineEditSourceName)
        self.btn_source=QPushButton("...")
        layout_data_source.addWidget(self.btn_source)
        
        self.tableVars = QTableWidget(0,5)  
        self.tableVars.setHorizontalHeaderLabels(['Variables','Belongs to','Alias','min','max'])     
        
        #interpolate timestep
        layout_interpolation=QVBoxLayout()
        self.checkbox_timestep=QCheckBox('data interpolation, s')
        self.checkbox_timestep.stateChanged.connect(self.interpolation_dt_state)
        layout_interpolation.addWidget(self.checkbox_timestep)
        self.interpolation_dt=QLineEdit('')
        self.interpolation_dt.setHidden(True)
        layout_interpolation.addWidget(self.interpolation_dt)

        #delete existing data
        self.delete_existing_data=QCheckBox('Delete data of selected variables')
        self.delete_existingID_data=QCheckBox('Delete data of selected variables with present feature ID')
        
        #buttons     
        layout_btn=QHBoxLayout()
        self.btn_import=QPushButton("Import")
        self.btn_cancel=QPushButton("Cancel")
        layout_btn.addWidget(self.btn_import)
        layout_btn.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout = QVBoxLayout()
        layout.addLayout(layout_data_source)
        layout.addWidget(self.tableVars)
        layout.addLayout(layout_interpolation)
        layout.addWidget(self.delete_existing_data)
        layout.addWidget(self.delete_existingID_data)
        layout.addLayout(layout_btn)
        layout.addStretch()
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)
        
    def interpolation_dt_state(self,s):
        if Qt.Checked==s:
            self.interpolation_dt.setHidden(False)
        else:
            self.interpolation_dt.setHidden(True)


        
