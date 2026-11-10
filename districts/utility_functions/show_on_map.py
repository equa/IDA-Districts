from .translations import tr, tr_msg
from qgis.utils import iface
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication,Qt,QThreadPool
from qgis.core import QgsMessageLog, QgsInterval, QgsDateTimeRange, QgsTemporalNavigationObject, QgsVectorLayerSimpleLabeling, QgsWkbTypes, QgsPalLayerSettings, QgsTemplatedLineSymbolLayerBase, QgsMarkerSymbol, QgsSimpleMarkerSymbolLayer, QgsMarkerLineSymbolLayer, QgsRuleBasedRenderer, QgsLineSymbol, QgsClassificationQuantile, QgsGeometry, QgsVectorLayer, QgsFeature, QgsClassificationEqualInterval, QgsRendererRangeLabelFormat, QgsStyle, QgsGraduatedSymbolRenderer, QgsSingleSymbolRenderer, QgsSymbol, QgsFilledMarkerSymbolLayer, QgsSymbolLayer, QgsProperty, Qgis
from qgis.PyQt.QtWidgets import QShortcut,QListWidgetItem,QFileDialog,QStackedWidget,QListView,QLineEdit,QDialog,QTableWidgetItem
from qgis.PyQt.QtGui import QFont, QColor

import numpy as np
from qgis.PyQt.QtCore import QRunnable, pyqtSlot
from qgis.core import QgsProject
from .compat import MessageCritical, sip
from .db import (
    dbConnect, getAvergageByMode, getMaxTableValue, getMaxTimeTableValue, getMinTableValue,
    getMinTimeTableValue,
)
from .files import loadProjectConfig
from .utility import getDatetimeFromString
from .workers import closesOwnConnection, APISignals2, runInMainThread

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import psycopg2.extras
import traceback
import uuid

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsDataSourceUri, QgsFeatureRequest, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsClassificationMethod
from .debug_log import dprint, debug_enabled

# 'show data on map' results are stored in indexed tables temp.result_vis_<id> of the project DB and loaded as PostGIS layers
# (a memory layer evaluates the temporal filter and the renderer expressions for all time steps in every frame);
# the tables are dropped when the project or a version is loaded the next time
RESULT_VIS_SCHEMA='temp'
RESULT_VIS_PREFIX='result_vis_'
RESULT_VIS_PROPERTY='districts_result_vis'


def removeResultVisLayers():
    """Remove the 'show data on map' PostGIS result layers from the QGIS project (before their tables are dropped)"""
    project=QgsProject.instance()
    for layer in list(project.mapLayers().values()):
        if layer.customProperty(RESULT_VIS_PROPERTY):
            project.removeMapLayer(layer.id())


def dropResultVisTables(cur):
    """Remove the result layers and drop all temp.result_vis_* tables of the project DB (cur: autocommit cursor of the project DB)"""
    removeResultVisLayers()
    if not cur:
        return
    try:
        cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema=%s AND table_name LIKE %s""",
            (RESULT_VIS_SCHEMA, RESULT_VIS_PREFIX.replace('_','\\_')+'%'))
        tables=[(row['table_name'] if isinstance(row,dict) else row[0]) for row in cur.fetchall()]
        if not tables:
            return
        # do not wait forever if another session (e.g. a second QGIS) still reads a table
        cur.execute("SET lock_timeout = '5s'")
        try:
            for table in tables:
                try:
                    cur.execute('DROP TABLE IF EXISTS "{}"."{}"'.format(RESULT_VIS_SCHEMA, table))
                except psycopg2.Error:
                    QgsMessageLog.logMessage(traceback.format_exc(), "Districts", MessageCritical)
        finally:
            cur.execute("RESET lock_timeout")
    except Exception:
        QgsMessageLog.logMessage(traceback.format_exc(), "Districts", MessageCritical)


def createResultVisTable(cur,config,vars,select_sql,feature):
    """Store the result of select_sql (columns fid, geom (geometry), [time], color/size/rotation) in a new indexed
    table temp.result_vis_<id> with the field names of the map layer (id, time, color_<var>, ...); returns the table name"""
    srid=int(loadProjectConfig(config)['srid'])
    geom_type='LineStringZ' if feature=='line' else 'PointZ'
    table=RESULT_VIS_PREFIX+uuid.uuid4().hex[:12]
    columns=['row_number() OVER ()::integer AS gid','s.fid::integer AS id']
    if vars['time']['first_time_var']:
        columns.append('s.time::timestamp AS time')
    columns.append('ST_SetSRID(ST_Force3D(s.geom),{srid})::geometry({geom_type},{srid}) AS geom'.format(srid=srid,geom_type=geom_type))
    for type in ['color','size','rotation']:
        if vars[type]['mode']:
            columns.append('s.{}::float8 AS "{}_{}"'.format(type,type,vars[type]['name'].split('$')[0]))
    sql="""CREATE SCHEMA IF NOT EXISTS "{schema}";
CREATE UNLOGGED TABLE "{schema}"."{table}" AS
SELECT {columns}
    FROM ({select}) s;
ALTER TABLE "{schema}"."{table}" ADD PRIMARY KEY (gid);
{time_index}CREATE INDEX ON "{schema}"."{table}" USING gist (geom);
ANALYZE "{schema}"."{table}";""".format(schema=RESULT_VIS_SCHEMA,table=table,columns=',\n    '.join(columns), # nosec B608
        select=select_sql.strip().rstrip(';'),
        time_index='CREATE INDEX ON "{}"."{}" (time);\n'.format(RESULT_VIS_SCHEMA,table) if vars['time']['first_time_var'] else '')
    cur.execute(sql)
    return table


def showOnMapPostgisLayer(config,table,feature,layer_name):
    """PostGIS layer of a temp.result_vis_* table (create it in the main thread)"""
    auth_cfg = QgsAuthMethodConfig()
    QgsApplication.authManager().loadAuthenticationConfig(config["auth_id"], auth_cfg, True)
    uri = QgsDataSourceUri()
    uri.setConnection(config['host'], config['port'], config['projectName'], auth_cfg.config("username"), auth_cfg.config("password"))
    uri.setDataSource(RESULT_VIS_SCHEMA, table, 'geom', '', 'gid')
    uri.setSrid(str(loadProjectConfig(config)['srid']))
    uri.setWkbType(Qgis.WkbType.LineStringZ if feature=='line' else Qgis.WkbType.PointZ)
    layer = QgsVectorLayer(uri.uri(False), layer_name, "postgres")
    if not layer.isValid():
        raise RuntimeError('Result layer {}.{} could not be loaded'.format(RESULT_VIS_SCHEMA,table))
    layer.setReadOnly(True)
    layer.setCustomProperty(RESULT_VIS_PROPERTY, table)
    return layer


def mdotArrowSymbol(color,arrow_size,attr):
    """Line with an arrow at the center pointing in the flow direction (sign of attr), no arrow without flow"""
    symbol = QgsLineSymbol.createSimple({'color': color.name(), 'width': '0.7'})
    marker_line = QgsMarkerLineSymbolLayer()
    if hasattr(marker_line, "setPlacements"):
        marker_line.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
    else:
        marker_line.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
    marker_line.setRotateSymbols(True)  # rotate according to the line direction
    marker_line.setDataDefinedProperty(QgsSymbolLayer.Property.LayerEnabled, QgsProperty.fromExpression(f'"{attr}" <> 0'))
    arrow = QgsSimpleMarkerSymbolLayer(shape=QgsSimpleMarkerSymbolLayer.Triangle, color=color, size=arrow_size)
    arrow.setAngle(90)
    arrow.setDataDefinedProperty(QgsSymbolLayer.Property.Angle, QgsProperty.fromExpression(f'if("{attr}" < 0, 270, 90)'))
    arrow_marker = QgsMarkerSymbol()
    arrow_marker.changeSymbolLayer(0, arrow)
    marker_line.setSubSymbol(arrow_marker)
    symbol.appendSymbolLayer(marker_line)
    return symbol


# position of a class for its label (scoped enum in QGIS 4)
CLASS_POSITION=getattr(QgsClassificationMethod,'ClassPosition',QgsClassificationMethod)

def resultVisClassBounds(cur,layer,expr,num_classes):
    """min, the linear percentiles i/num_classes and max of expr (= QgsClassificationQuantile, numpy.percentile) computed in the DB
    for the layer of a temp.result_vis_* table: reading all features in the main thread took seconds for millions of rows
    (e.g. 4 s for 1.4 million rows, 0.3 s in the DB). None if the layer has no result table, [] if there are no values"""
    table=layer.customProperty(RESULT_VIS_PROPERTY)
    if not table or cur is None or num_classes<1:
        return None
    fractions=[i/num_classes for i in range(num_classes+1)]
    cur.execute('SELECT percentile_cont(%s::float8[]) WITHIN GROUP (ORDER BY {e}) AS bounds FROM "{s}"."{t}" WHERE {e} IS NOT NULL;'.format( # nosec B608
        e=expr,s=RESULT_VIS_SCHEMA,t=table),(fractions,))
    row=cur.fetchone()
    bounds=row['bounds'] if isinstance(row,dict) else row[0]
    return [float(i) for i in bounds] if bounds else []

def renderMapPlot(layer,data,cur,config,first_time_var=None,colorlabel=None,color_classes=None,colormode=None,colorramp=None,feature=None,varRotation=None,size_symbolMin=None,size_symbolMax=None,rotation_symbolMin=None,rotation_symbolMax=None,networkReportDlg=None):
    dprint(data)
    if colorlabel:
        # Construct the expression for one decimal place formatting
        label_expression = f"format_number(\"{'color_' + data['color']['name'].split('$')[0]}\", 1)"

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
        if debug_enabled(): dprint(f"Labels enabled for layer '{layer.name()}' using expression: {label_expression}")


    # ===== BUILD RENDERER (in main thread!) =====
    dprint("Building renderer in main thread...")
    renderer = None
    mdot_arrows = False

    if data['color']['mode']:
        # target field name used for graduated renderer
        target_field = 'color_' + data['color']['name'].split('$')[0]
        dprint("Renderer target field:", target_field)
        if data['color']['name'].split('$')[0] == 'mdot' and feature=='line':
            # --- mdot: rule-based renderer with arrows (positive / negative)
            attr = "color_mdot"
            arrow_size = 3
            num_classes = int(color_classes)
            classification_mode = colormode
            color_ramp_name = colorramp

            style_mgr = QgsStyle().defaultStyle()
            ramp = style_mgr.colorRamp(color_ramp_name)
            if ramp is None:
                raise ValueError(f"Color ramp '{color_ramp_name}' not found in QGIS Style Manager")

            # class bounds of abs(mdot): in the DB for result tables, else from the features (memory layer)
            quantiles = resultVisClassBounds(cur, layer, 'abs("{}")'.format(attr), num_classes)
            if quantiles is None:
                request = QgsFeatureRequest().setFlags(Qgis.FeatureRequestFlag.NoGeometry).setSubsetOfAttributes([attr], layer.fields())
                vals = [abs(f[attr]) for f in layer.getFeatures(request) if f[attr] is not None]
                quantiles = np.percentile(vals, np.linspace(0, 100, num_classes + 1)).tolist() if vals else []
            if not quantiles:
                # fallback: set single-class renderer
                dprint("No values for attr", attr, " -> single symbol")
                renderer = QgsSingleSymbolRenderer(QgsSymbol.defaultSymbol(layer.geometryType()))
            else:
                vmin, vmax = quantiles[0], quantiles[-1]
                if vmin == vmax:
                    # degenerate case -> single class
                    bounds = [vmin, vmax]
                    num_classes = 1
                else:
                    if classification_mode == 'Equal Count':
                        bounds = quantiles
                    else:
                        step = (vmax - vmin) / num_classes
                        bounds = [vmin + i * step for i in range(num_classes + 1)]

                # one graduated class per value range of abs(mdot), the arrow direction is data-defined
                # (rule-based +/- rules: a memory layer evaluated 2 filter expressions per class for the features
                # of all time steps in every frame of the temporal controller)
                ranges = []
                for i_cls in range(num_classes):
                    lower = bounds[i_cls]
                    upper = bounds[i_cls + 1]
                    frac = i_cls / (num_classes - 1) if num_classes > 1 else 0.0
                    ranges.append(QgsRendererRange(lower, upper, mdotArrowSymbol(ramp.color(frac), arrow_size, attr), f"{lower:.3g} – {upper:.3g}"))
                renderer = QgsGraduatedSymbolRenderer(f'abs("{attr}")', ranges)
                mdot_arrows = True

        else:
            # --- Graduated renderer branch ---
            if colormode == 'Equal Count':
                classification_method = QgsClassificationQuantile()
            else:
                classification_method = QgsClassificationEqualInterval()
            classification_method.setLabelPrecision(1)
            classification_method.setLabelTrimTrailingZeroes(True)

            default_style = QgsStyle().defaultStyle()
            color_ramp = default_style.colorRamp(colorramp)

            renderer = QgsGraduatedSymbolRenderer()
            renderer.setClassAttribute(target_field)
            renderer.setClassificationMethod(classification_method)
            # Equal Count of a result table: bounds computed in the DB (updateClasses reads all values in the main thread)
            bounds = resultVisClassBounds(cur, layer, '"{}"'.format(target_field), int(color_classes)) if colormode == 'Equal Count' else None
            if bounds:
                for i_cls in range(len(bounds) - 1):
                    position = CLASS_POSITION.LowerBound if i_cls == 0 else (CLASS_POSITION.UpperBound if i_cls == len(bounds) - 2 else CLASS_POSITION.Inner)
                    renderer.addClassRange(QgsRendererRange(bounds[i_cls], bounds[i_cls + 1], QgsSymbol.defaultSymbol(layer.geometryType()),
                        classification_method.labelForRange(bounds[i_cls], bounds[i_cls + 1], position)))
            else:
                renderer.updateClasses(layer, int(color_classes))
            renderer.updateColorRamp(color_ramp)
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if feature == 'line':
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
        if data['size']['mode'] or data['rotation']['mode']:
            dprint("Applying size/rotation DDPs...")
            # create a base symbol to apply changes to
            base_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            style = {}
            if varRotation:
                style['name'] = 'arrow'
            else:
                style['name'] = 'point'
            style['color'] = 'black'
            symbolLayer = QgsFilledMarkerSymbolLayer.create(style)
            base_symbol.changeSymbolLayer(0, symbolLayer)

            # size scale
            if data['size']['mode']:
                if data['size']['mode'] == 'var':
                    min_value = getMinTimeTableValue(data['size']['var_function'], cur, config, data['size']['table_name'], data['size']['name'].split('$')[0], data['time']['starttime'], data['time']['endtime'])
                    max_value = getMaxTimeTableValue(data['size']['var_function'], cur, config, data['size']['table_name'], data['size']['name'].split('$')[0], data['time']['starttime'], data['time']['endtime'])
                else:
                    min_value = getMinTableValue(cur, config['versionName'], data['size']['table_name'], data['size']['name'])
                    max_value = getMaxTableValue(cur, config['versionName'], data['size']['table_name'], data['size']['name'])

                scale_expr = """coalesce(scale_exp("{}", {}, {}, {}, {}, 0.57), 0)""".format(
                    'size_' + data['size']['name'].split('$')[0],
                    min_value, max_value,
                    float(size_symbolMin), float(size_symbolMax)
                )
                # property for size or stroke width
                prop = QgsSymbolLayer.PropertyStrokeWidth if feature == 'line' else QgsSymbolLayer.PropertySize
                base_symbol.symbolLayer(0).setDataDefinedProperty(prop, QgsProperty.fromExpression(scale_expr))

            # rotation
            if data['rotation']['mode']:
                if data['rotation']['mode'] == 'var':
                    min_value = getMinTimeTableValue(data['rotation']['var_function'], cur, config, data['rotation']['table_name'], data['rotation']['name'].split('$')[0], data['time']['starttime'], data['time']['endtime'])
                    max_value = getMaxTimeTableValue(data['rotation']['var_function'], cur, config, data['rotation']['table_name'], data['rotation']['name'].split('$')[0], data['time']['starttime'], data['time']['endtime'])
                else:
                    min_value = getMinTableValue(cur, config['versionName'], data['rotation']['table_name'], data['rotation']['name'])
                    max_value = getMaxTableValue(cur, config['versionName'], data['rotation']['table_name'], data['rotation']['name'])

                rotation_expr = """coalesce(scale_exp("{}", {}, {}, {}, {}, 0.57), 0)""".format(
                    'rotation_' + data['rotation']['name'].split('$')[0],
                    min_value, max_value,
                    float(rotation_symbolMin), float(rotation_symbolMax)
                )
                base_symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyAngle, QgsProperty.fromExpression(rotation_expr))

            # apply the base symbol to renderer
            if mdot_arrows:
                # keep the arrow symbols: only the line width of each class is data-defined
                if data['size']['mode']:
                    for i_range, range_ in enumerate(renderer.ranges()):
                        symbol = range_.symbol().clone()
                        symbol.symbolLayer(0).setDataDefinedProperty(prop, QgsProperty.fromExpression(scale_expr))
                        renderer.updateRangeSymbol(i_range, symbol)
            else:
                try:
                    renderer.updateSymbols(base_symbol)
                except Exception:
                    renderer.setSymbol(base_symbol)

    except Exception:
        QgsMessageLog.logMessage(
            traceback.format_exc(),
            "Districts",
            MessageCritical
        )

    # ===== APPLY RENDERER (after labeling) =====
    try:
        dprint("Applying renderer to layer...")
        layer.setRenderer(renderer)
    except Exception:
        QgsMessageLog.logMessage(
            traceback.format_exc(),
            "Districts",
            MessageCritical
        )

    # ===== ADD TO PROJECT =====
    dprint("Adding layer to project...")
    QgsProject.instance().addMapLayer(layer)    
    
    # ===== TEMPORAL CONTROLLER (if applicable) =====
    if first_time_var:
        dprint("Configuring temporal controller...")
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
                getDatetimeFromString(data['time']['starttime']),
                getDatetimeFromString(data['time']['endtime'])
            )
        )
        temporalNavigationObject.setLooping(True)
        temporalNavigationObject.setAnimationState(Qgis.AnimationState.Forward)

        interval = QgsInterval()
        dt = data['time']['dt']
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
        
    # ===== FINAL REFRESH =====
    layer.triggerRepaint()
    try:
        iface.layerTreeView().refreshLayerSymbology(layer.id())
    except Exception:
        QgsMessageLog.logMessage(
            traceback.format_exc(),
            "Districts",
            MessageCritical
        )
    iface.mapCanvas().refresh()
    
def showOnMapMemoryLayer(vars,config,plugin_dir,feature,layer_name):   
    dprint('showOnMapMemoryLayer')
    column_names=[vars[var]['name'].split('$')[0] for var in vars if var not in ['time','data'] and vars[var]['mode']]
    column_types=[var for var in vars if var not in ['time','data'] and vars[var]['mode']]
    dprint(column_names)
    dprint(column_types)
    
    # make new memory layer
    temp_layer = QgsVectorLayer("{}?crs=epsg:{}&field=id:integer&{}{}".format(
        'LineStringZ' if feature=='line' else 'PointZ',
        loadProjectConfig(config)['srid'],
        'field=time:datetime&' if vars['time']['first_time_var'] else '',
        '&'.join(['field={}:numeric'.format(type+'_'+name) for type,name in zip(column_types,column_names)])),layer_name, "memory")
    temp_layer.startEditing()
    dprint('temp_layer generated')

    #make new features
    for i in vars['data']:
        feat = QgsFeature(temp_layer.fields())
        feat["id"] = i['fid']
        if vars['time']['first_time_var']:
            feat["time"] = str(i['time'])
        feat.setGeometry(QgsGeometry.fromWkt(i['geom']))
        for type,name in zip(column_types,column_names):
            feat[type+'_'+name]=float(i[type])
        temp_layer.addFeature(feat)
    dprint('features added')
    
    return temp_layer

class WorkerShowOnMap(QRunnable):
    """Worker thread
    Inherits from QRunnable to handle worker thread setup, signals and wrap-up."""
    def __init__(self,*args,**kwargs):
        super().__init__()
        self.args=args
        dprint('WorkerShowOnMap')
        dprint(kwargs)
        self.signals=APISignals2()
        self.dlg_main=kwargs['dlg_main']
        self.config=kwargs['config']
        self.dlg=kwargs['dlg']
        if self.dlg:
            self.dlg.process_running=True
        self.vars=kwargs['vars']
        self.feature= kwargs['feature']
        self.layer_name= kwargs['layer_name']
        self.lineSegVisLength= kwargs['lineSegVis']
        self.enable= kwargs['enable']
        self.networkReportDlg= kwargs['networkReportDlg']
        self.conn=""
        self.cur=""
        self.plugin_dir=kwargs['plugin_dir']
        self.simData=kwargs['simData']
        self.vis_table=None
        self.time_values=['Values','Hourly average','Daily average','Monthly average']
        self.conn = dbConnect(self.config,True)
        self.vars=None
        self.progress_value=0
        self.progress_text=None
        self.steps=[]
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

    # weights: shares of the duration measured with 198 lines/280 segments of 50 m/7200 time steps (segment table 7 s,
    # data 5 s, styling 0.6 s, the rest < 0.1 s)
    STEP_WEIGHTS={'drop':1,'segmentize':1,'color_seg':35,'size_seg':35,'data':30,'dt':1,'layer':2,'render':5}

    def setProgress(self,value,text=None):
        """emit the progress (never backwards, max. 99 until finished) and the status text"""
        value=int(max(self.progress_value,min(99,value)))
        if value!=self.progress_value:
            self.progress_value=value
            self.signals.progress.emit(value)
        if text is not None and text!=self.progress_text:
            self.progress_text=text
            self.signals.status.emit(text)

    def planSteps(self,vars):
        """steps which are run for the selected variables (the progress values are distributed by STEP_WEIGHTS)"""
        def segVar(type):
            return vars[type]['mode']=='var' and vars[type]['name'].split('$')[0] in ('temp','p')
        steps=['drop']
        if self.simData and self.feature=='line' and (segVar('color') or segVar('size')):
            steps.append('segmentize')
            if vars['color']['mode']=='var' and vars['color']['var_function']!='specific_dp':
                steps.append('color_seg')
            if vars['size']['mode']=='var' and vars['color']['name']!=vars['size']['name']:
                steps.append('size_seg')
        steps.append('data')
        if any(vars[type]['var_function'] in self.time_values for type in ['color','size','rotation']):
            steps.append('dt')
        if not self.networkReportDlg:
            steps+=['layer','render']
        self.steps=steps

    def setStep(self,step,text):
        """progress at the start of a planned step and its status text, e.g. 'step 2/5: splitting the lines into segments of 50 m'"""
        if step not in self.steps:
            self.setProgress(self.progress_value,text)
            return
        weights=[self.STEP_WEIGHTS[i] for i in self.steps]
        idx=self.steps.index(step)
        self.setProgress(2+95*sum(weights[:idx])/sum(weights),tr_msg('step {}/{}: {}').format(idx+1,len(self.steps),text))

    def varDescription(self,vars,type):
        """e.g. 'color: temp (Hourly average)'"""
        var=vars[type]
        return '{}: {}{}'.format(type,var['name'].split('$')[0],' ({})'.format(var['var_function']) if var['mode']=='var' and var['var_function'] else '')

    def getShowOnMapVarsDict(self):
        """{'color'/'size'/'rotation':{'mode':'var'/'par'/False, 'name': var_name/par_name, 'var_function': function_items, 'table_name': DB table},time:{starttime,endtime},data}"""
        vars={'color': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'size': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'rotation': {'mode':False, 'name': '', 'var_function': '', 'table_name': ''},
            'time': {'starttime': '', 'endtime':'', 'dt':False, 'first_time_var': ''},
            'data': ''}
            
        if self.dlg:
            if self.dlg.checkbox_varColor.isChecked():
                if self.dlg.rbtn_colorVar.isChecked():
                    vars['color']['mode']='var'
                    vars['color']['var_function']=self.dlg.color_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.color_var.currentText()
                    vars['color']['table_name']=self.dlg.color_table_name
                else:
                    vars['color']['mode']='par'
                    name=self.dlg.color_par.currentText()
                    vars['color']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['color']['name']=name
            if self.dlg.checkbox_varSize.isChecked():
                if self.dlg.rbtn_sizeVar.isChecked():
                    vars['size']['mode']='var'
                    vars['size']['var_function']=self.dlg.size_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.size_var.currentText()
                    vars['size']['table_name']=self.dlg.size_table_name    
                else:
                    vars['size']['mode']='par'
                    name=self.dlg.size_par.currentText()
                    vars['size']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['size']['name']=name
            if self.dlg.checkbox_varRotation.isChecked():
                if self.dlg.rbtn_rotationVar.isChecked():
                    vars['rotation']['mode']='var'
                    vars['rotation']['var_function']=self.dlg.rotation_function.currentText()
                    vars['time']['starttime']=self.dlg.starttime.text()
                    vars['time']['endtime']=self.dlg.endtime.text()
                    name=self.dlg.rotation_var.currentText()
                    vars['rotation']['table_name']=self.dlg.rotation_table_name
                else:
                    vars['rotation']['mode']='par'
                    name=self.dlg.rotation_par.currentText()
                    vars['rotation']['table_name']=self.dlg.feature+'s'
                if name:
                    vars['rotation']['name']=name
        else:
            dprint('kwargs vars')
            vars=self.vars

        self.planSteps(vars)
        vars=self.getShowOnMapData(vars)
        return vars
    
    def getShowOnMapData(self,vars):
        dprint(vars)
        #drop old line_seg_%_vis tables
        self.setStep('drop',tr_msg('removing old visualization tables'))
        sql="""WITH tables_to_drop AS (
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = '{}'
      AND table_name LIKE 'line_s_%_vis'
)
SELECT execute_dynamic_sql(format('DROP TABLE "{}".%I;', table_name))
    FROM tables_to_drop;""".format(self.config['versionName'],self.config['versionName']) # nosec B608
        self.cur.execute(sql)
        
        if vars['color']['var_function'] in self.time_values:
            time_color=True
        else:
            time_color=False
        if vars['size']['var_function'] in self.time_values:
            time_size=True
        else:
            time_size=False  
        if vars['rotation']['var_function'] in self.time_values:
            time_rotation=True
        else:
            time_rotation=False
            
        self.first_time_var='color' if time_color else ('size' if time_size else ('rotation' if time_rotation else False))
        dprint('++first-time-var: '+str(self.first_time_var))
        if self.first_time_var:
            dt=getAvergageByMode(vars[self.first_time_var]['var_function'],self.cur,self.config,vars[self.first_time_var]['table_name']) #hours
        else:
            dt=False
        dprint(dt)
        first_par_var='color' if vars['color']['mode'] else ('size' if vars['size']['mode'] else ('rotation' if vars['rotation']['mode'] else False))
        dprint(self.first_time_var)
        dprint(first_par_var)
        first_group=self.first_time_var if self.first_time_var else first_par_var
        
        #if simulation results and line feature
        if self.simData and self.feature=='line':
            dprint('update DB with visualization tables')
            #re-create table line_seg_vis, which holds the geometry of the visualized pipe segements
            #check if > calculated segments
                
            srid=loadProjectConfig(self.config)['srid']
            
            #store cumulate simulation results in _vis table if lineSegVis!=0 and var
            if vars['color']['mode']=='var' and vars['color']['name'].split('$')[0] in ('temp','p') or vars['size']['mode']=='var' and vars['size']['name'].split('$')[0] in ('temp','p'):
                sql="""DROP TABLE IF EXISTS "{}".line_seg_vis;
CREATE TABLE IF NOT EXISTS "{}".line_seg_vis
(
    id serial,
    lid integer NOT NULL,
    lid_seg integer NOT NULL,
    geom geometry(LineStringZ,{})
);
SELECT segmentize({},'{}','line_seg_vis');""".format(self.config['versionName'],self.config['versionName'],srid,1000000 if vars['color']['var_function']=='specific_dp' else self.lineSegVisLength,self.config['versionName']) # nosec B608
                dprint(sql)
                self.setStep('segmentize',tr_msg('splitting the lines into segments') if vars['color']['var_function']=='specific_dp' else tr_msg('splitting the lines into segments of {} m').format(self.lineSegVisLength))
                self.cur.execute(sql)

                #load var data to the coresponding visualization table using averaged values for merged segments
                if vars['color']['mode']=='var' and vars['color']['var_function']!='specific_dp' :
                    interpolate=vars['color']['name'].split('$')[0]=='p' #linear interpolation using pressure values at start and end of the line
                    self.setStep('color_seg',tr_msg('{} {} on the line segments (color)').format(
                        tr_msg('interpolating') if interpolate else tr_msg('averaging'),vars['color']['name'].split('$')[0]))
                    self.cur.execute(self.segmentVisTableSql(vars['color']['name'],interpolate,vars['time']))
                    vars['color']['table_name']=vars['color']['table_name']+'_vis'

                if vars['size']['mode']=='var':
                    if vars['color']['name'] !=  vars['size']['name']: #if color and size car name is same --> do not twice
                        self.setStep('size_seg',tr_msg('averaging {} on the line segments (size)').format(vars['size']['name'].split('$')[0]))
                        self.cur.execute(self.segmentVisTableSql(vars['size']['name'],False,vars['time']))
                    vars['size']['table_name']=vars['size']['table_name']+'_vis'
                    
        dprint('get-data')
        # aggregated only for hourly/daily/monthly averages: otherwise each row is one result row (the GROUP BY over all columns
        # did not change the rows, it doubled the duration); the map table gets the geometry itself (WKT only for the network report)
        averaged=bool(self.first_time_var) and dt in ['hour','day','month']
        if self.first_time_var or first_par_var:
            sql="""SELECT {}.{} AS fid, {} AS geom {}, {}
    FROM {}{}{}{}
    ORDER BY {} {}.{};""".format(first_group,'fid' if vars[first_group]['mode']=='var' else 'id', # nosec B608
                ('ST_AsText({}.geom)' if self.networkReportDlg else '{}.geom').format(first_group), # nosec B608
                """,date_trunc('{}', {}.time) AS time""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else (',{}.time'.format(self.first_time_var) if self.first_time_var else ''), # nosec B608
                ','.join([i for i in # nosec B608
                [('avg(color."${}") AS color'.format(vars['color']['name'].split('$')[0]) if averaged else 'color."${}" AS color'.format(vars['color']['name'].split('$')[0])) if time_color else ('color.color' if vars['color']['mode']=='var' else ('color."{}"'.format(vars['color']['name']) +' AS color' if vars['color']['mode'] else '')), # nosec B608
                ('avg(size."${}") AS size' if averaged else 'size."${}" AS size').format(vars['size']['name'].split('$')[0]) if time_size else ('size.size' if vars['size']['mode']=='var' else ('size."{}"'.format(vars['size']['name']) +' AS size' if vars['size']['mode'] else '')), # nosec B608
                ('avg(rotation."${}") AS rotation' if averaged else 'rotation."${}" AS rotation').format(vars['rotation']['name'].split('$')[0]) if time_rotation else ('rotation.rotation' if vars['rotation']['mode']=='var' else ('rotation."{}"'.format(vars['rotation']['name']) +' AS rotation' if vars['rotation']['mode'] else '') )]  # nosec B608
                if i]), # nosec B608
                ','.join([i for i in  #from  # nosec B608
                    [""""{}".{} color""".format(self.config['versionName'],vars['color']['table_name']) if time_color else ( # nosec B608
                    """({}) color""".format(self.getNonTimeVarFunctionValue(vars['color'],'color',vars['time']))  # nosec B608
                    if vars['color']['mode']=='var' else ('"{}".{} AS color'.format(self.config['versionName'],vars['color']['table_name']) if vars['color']['mode']=='par' else '')), # nosec B608
                    """"{}".{} size""".format(self.config['versionName'],vars['size']['table_name']) if time_size else ( # nosec B608
                    """({}) size""".format(self.getNonTimeVarFunctionValue(vars['size'],'size',vars['time']))   # nosec B608
                    if vars['size']['mode']=='var'else ('"{}".{} AS size'.format(self.config['versionName'],vars['size']['table_name']) if vars['size']['mode']=='par' else '')), # nosec B608
                    """"{}".{} rotation""".format(self.config['versionName'],vars['rotation']['table_name']) if time_rotation else ( # nosec B608
                    """({}) rotation""".format(self.getNonTimeVarFunctionValue(vars['rotation'],'rotation',vars['time']))  # nosec B608
                    if vars['rotation']['mode']=='var' else ('"{}".{} AS rotation'.format(self.config['versionName'],vars['rotation']['table_name']) if vars['rotation']['mode']=='par' else ''))]  # nosec B608
                    if i]), # nosec B608
                '\n    WHERE ' if len([var for var in vars if var not in ['time','data']and vars[var]['mode']])>=2  or self.first_time_var else '', # nosec B608
                ' AND '.join([i for i in #where  # nosec B608
                    [' AND '.join([first_group+('.fid=' if vars[first_group]['mode']=='var' else '.id=')+var+('.fid' if vars[var]['mode']=='var' else '.id')  # nosec B608
                        for var in vars if var not in ['time','data']+[first_group] and vars[var]['mode']]), # nosec B608                      
                    ' AND '.join([first_group+'.geom='+var+'.geom'  # nosec B608
                        for var in vars if self.first_time_var and var not in ['time','data']+[self.first_time_var] and vars[var]['mode']=='var']),     # nosec B608                       
                    ' AND '.join([self.first_time_var+'.time='+var+'.time' for var in vars if var not in ['time','data']+[self.first_time_var] and vars[var]['var_function'] in self.time_values]), # nosec B608
                    """{}.time <= '{}' AND {}.time >= '{}'""".format(self.first_time_var,vars['time']['endtime'],self.first_time_var,vars['time']['starttime']) if self.first_time_var else ''] if i]), # nosec B608
                ('\n    GROUP BY ' if averaged else '')+','.join([i for i in #group by  # nosec B608
                    ["{}.geom".format(first_group), # nosec B608
                    """date_trunc('{}', {}.time)""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else ('{}.time'.format(self.first_time_var) if self.first_time_var else ''), # nosec B608
                    '{}.{}'.format(first_group,'fid' if vars[first_group]['mode']=='var' else 'id'), # nosec B608
                    ','.join([var+'.'+(var if vars[var]['mode']=='var' and vars[var]['var_function']!='Values' else '"'+('$' if vars[var]['mode']=='var' else '')+vars[var]['name'].split('$')[0]+'"') for var in vars if var not in ['time','data'] and (vars[var]['mode'] and vars[var]['var_function'] not in self.time_values or vars[var]['var_function']=='Values')])] if i]) if averaged else '', # nosec B608
                """date_trunc('{}', {}.time),""".format(dt,self.first_time_var) if self.first_time_var and dt in ['hour','day','month'] else ('{}.time,'.format(self.first_time_var) if self.first_time_var else ''), #order by  # nosec B608
                first_group,'fid' if vars[first_group]['mode']=='var' else 'id') # nosec B608
            dprint(sql)
        vars['time']['first_time_var']=self.first_time_var
        data_text=', '.join(self.varDescription(vars,type) for type in ['color','size','rotation'] if vars[type]['mode'])
        if self.first_time_var:
            data_text+=', {} - {}'.format(vars['time']['starttime'],vars['time']['endtime'])
        self.setStep('data',(tr_msg('querying {} ({})') if self.networkReportDlg else tr_msg('querying and storing {} ({})')).format(tr('@default',self.feature+'s'),data_text))
        if self.networkReportDlg:
            # network report: the rows are stored with the plot and rendered later (memory layer)
            self.cur.execute(sql)
            data=self.cur.fetchall()
        else:
            # map: indexed PostGIS table (the temporal controller then only fetches the rows of the current frame)
            self.vis_table=createResultVisTable(self.cur,self.config,vars,sql,self.feature)
            data=None
        #get dt if not averaged
        if not dt and self.first_time_var:
            self.setStep('dt',tr_msg('determining the time step'))
            sql="""WITH sub AS(
    SELECT a.time-LAG(a.time, 1) OVER () as dt
        FROM (SELECT time FROM "{}".{} GROUP BY time) a
        GROUP BY time 
        ORDER BY time
)
SELECT EXTRACT(epoch FROM dt)/3600 AS dt FROM sub WHERE dt IS NOT NULL LIMIT 1;""".format(self.config['versionName'],vars[self.first_time_var]['table_name']) # nosec B608
            dprint(sql)
            self.cur.execute(sql)
            dt=self.cur.fetchone()['dt']
            dprint(dt)

        vars['data']=data
        vars['time']['dt']=dt
        vars['time']['first_time_var']=self.first_time_var
        return vars
    
    def segmentVisTableSql(self,name,interpolate,time):
        """SQL for line_s_<name>_vis (fid, time, geom, segment, "$<var>"): the results of line_s_<name> on the visualization
        segments of line_seg_vis, interpolated between the values of result segments 1 and 2 (pressure) or averaged over the result
        segments which lie on a visualization segment. The result segment -> visualization segment mapping is determined once
        with the geometries of the first time step of each line (the geometry of a result segment is the same for all time steps;
        the spatial condition was evaluated for each time row, ~2.5x slower)"""
        v=self.config['versionName']
        col=name.split('$')[0]
        sql='DROP TABLE IF EXISTS "{v}"."line_s_{n}_vis" CASCADE;\n'.format(v=v,n=name)
        if interpolate:
            sql+="""CREATE UNLOGGED TABLE "{v}"."line_s_{n}_vis" AS
SELECT a.fid, a.time, seg.geom, seg.lid_seg AS segment,
        a."${c}"+CASE WHEN n.count=1 THEN (b."${c}"-a."${c}")/2 ELSE (b."${c}"-a."${c}")/(n.count-1)*(seg.lid_seg-1) END AS "${c}"
    FROM "{v}"."line_s_{n}" a
    JOIN "{v}"."line_s_{n}" b ON b.fid=a.fid AND b.time=a.time AND b.segment=2
    JOIN (SELECT lid, count(*) AS count FROM "{v}".line_seg_vis GROUP BY lid) n ON n.lid=a.fid
    JOIN "{v}".line_seg_vis seg ON seg.lid=a.fid
    WHERE a.segment=1 AND a.time BETWEEN '{t0}' AND '{t1}'
    ORDER BY a.fid, seg.lid_seg, a.time;
""".format(v=v,n=name,c=col,t0=time['starttime'],t1=time['endtime']) # nosec B608
        else:
            sql+="""DROP TABLE IF EXISTS pg_temp.line_seg_map;
CREATE TEMP TABLE line_seg_map AS
SELECT r.fid, r.segment, seg.lid_seg
    FROM (SELECT DISTINCT lid FROM "{v}".line_seg_vis) l
    CROSS JOIN LATERAL (SELECT min(time) AS t FROM "{v}"."line_s_{n}" WHERE fid=l.lid) t0
    JOIN "{v}"."line_s_{n}" r ON r.fid=l.lid AND r.time=t0.t
    JOIN "{v}".line_seg_vis seg ON seg.lid=r.fid AND ST_DWithin(ST_LineSubstring(seg.geom,0.01,0.99),r.geom,0.001);
ANALYZE line_seg_map;
CREATE UNLOGGED TABLE "{v}"."line_s_{n}_vis" AS
SELECT a.fid, a.time, seg.geom, a.lid_seg AS segment, a.value AS "${c}"
    FROM (SELECT s.fid, s.time, m.lid_seg, avg(s."${c}") AS value
            FROM "{v}"."line_s_{n}" s JOIN line_seg_map m ON m.fid=s.fid AND m.segment=s.segment
            WHERE s.time BETWEEN '{t0}' AND '{t1}'
            GROUP BY s.fid, m.lid_seg, s.time) a
    JOIN "{v}".line_seg_vis seg ON seg.lid=a.fid AND seg.lid_seg=a.lid_seg
    ORDER BY a.fid, a.lid_seg, a.time;
DROP TABLE line_seg_map;
""".format(v=v,n=name,c=col,t0=time['starttime'],t1=time['endtime']) # nosec B608
        sql+='CREATE INDEX "idx_line_s_{n}_vis_fid_time_segment" ON "{v}"."line_s_{n}_vis" (fid, time, segment);'.format(v=v,n=name) # nosec B608
        return sql

    def getNonTimeVarFunctionValue(self,var,type,time):
        if var['var_function']=='Max':
            sql="""SELECT fid,geom AS geom,max("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime']) # nosec B608
        elif var['var_function']=='Min':
            sql="""SELECT fid,geom AS geom,min("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime']) # nosec B608
        elif var['var_function']=='Average':
            sql="""SELECT fid,geom AS geom,avg("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime']) # nosec B608
        elif var['var_function']=='Last value':
            sql="""SELECT DISTINCT ON (fid{}) 
    fid,geom,"${}" AS {},time
FROM "{}".{}
WHERE time <= '{}'
ORDER BY fid{},time DESC""".format(',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '' ,var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['endtime'],',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '') # nosec B608
        elif var['var_function']=='Sum':
             sql="""SELECT fid,geom AS geom,sum("${}") AS {} FROM "{}".{} WHERE time BETWEEN '{}' AND '{}' GROUP BY fid,geom ORDER BY fid""".format(var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],time['endtime']) # nosec B608
        elif var['var_function']=='First value':
            sql="""SELECT DISTINCT ON (fid{}) 
    fid,geom AS geom,"${}" AS {},time
FROM "{}".{}
WHERE time >= '{}'
ORDER BY fid{},time ASC;""".format(',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '',var['name'].split('$')[0],type,self.config['versionName'],var['table_name'],time['starttime'],',segment' if var['name'].split('$')[0] in ['p','temp'] and 'line_' in var['table_name'] else '') # nosec B608
        elif var['var_function']=='specific_dp':
            sql="""WITH length_per_fid AS (
    SELECT lid AS fid, st_length(geom) AS len, geom
    FROM {}.line_seg_vis
)
SELECT 
    a.fid,lp.geom,
    MAX(ABS(a."$p" - b."$p") / lp.len) AS {}
FROM {}.{} a
JOIN {}.{} b
    ON a.fid = b.fid
   AND a.time = b.time
   AND a.segment = 1
   AND b.segment = 2
JOIN length_per_fid lp
    ON lp.fid = a.fid
WHERE a.time between '{}' and '{}'
GROUP BY a.fid, lp.geom""".format( # nosec B608
                self.config['versionName'],type,self.config['versionName'],var['table_name'],self.config['versionName'],var['table_name'],time['starttime'],time['endtime']) # nosec B608
        dprint(sql)
        return sql

            
    def showOnMap(self):
        self.vars=self.getShowOnMapVarsDict()
        if not self.networkReportDlg:
            # layers are created in the main thread (a layer created in a pool thread keeps its own DB connection)
            self.setStep('layer',tr_msg('creating the map layer'))
            self.temp_layer = runInMainThread(showOnMapPostgisLayer,self.config,self.vis_table,self.feature,self.layer_name)
            # the layer is styled in the main thread by update_finished of the dialog (sets 100%)
            self.setStep('render',tr_msg('styling the map layer'))
            # finished is emitted once by run() (it was emitted twice, so the layer was rendered twice)
 
    @pyqtSlot()
    @closesOwnConnection
    def run(self):
        dprint('Show data on map')
        self.setProgress(1,tr_msg('reading the settings'))
        try:
            self.showOnMap()
            if self.networkReportDlg:
                self.progress_value=100
                self.signals.progress.emit(100)
                self.signals.status.emit(tr_msg('done'))
            self.signals.finished.emit(tr_msg('Data has been successfully visualized on map!'),self)  
        except Exception:
            QgsMessageLog.logMessage(
                traceback.format_exc(),
                "Districts",
                MessageCritical
            ) 
            failed_step=self.progress_text
            self.progress_value=0
            self.signals.progress.emit(0)
            self.signals.status.emit(tr_msg('failed at {} (see message log Districts)').format(failed_step) if failed_step else tr_msg('failed (see message log Districts)'))
            self.signals.finished.emit(tr_msg('Data visualization has failed!'),self)  
