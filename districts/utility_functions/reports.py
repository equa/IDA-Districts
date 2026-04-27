from qgis.core import QgsLayerTreeNode,QgsLayerTreeGroup,QgsLegendStyle,QgsLayoutItemScaleBar,QgsLayoutItemLegend,QgsLayerTree,QgsRectangle,QgsLayoutItemMap,QgsRasterLayer,QgsVectorLayer,QgsAttributeEditorAction,QgsAction,QgsProject,Qgis,QgsPrintLayout,QgsLayoutItemPage,QgsLayoutItemLabel,QgsLayoutPoint,QgsLayoutItemPolygon,QgsLayoutExporter
from qgis.PyQt.QtCore import QPointF, Qt
from qgis.PyQt.QtGui import QFont, QColor, QPolygonF

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

from .files import *
from .translations import *
from .topology import *
from .show_on_map import *
from .db import *

import tempfile
import os 
import math 

def getKPIUnit(name):
    if name.startswith("tsup") or name.startswith("tret"):
        return '°C'
    elif name.startswith("qsup") or name.startswith("qamb"):
        if "spec" in name:
            return 'kWh/m2 ERA'
        elif "linedensity" in name:
            return 'kWh/m trench'
        elif "density" in name:
            return 'kWh/m2 plot'
        else:
            return 'kWh'
    elif name=='eff_width':
        return 'm'
    elif name=='volume':
        return 'm3'
    else:
        return ''
    
def networkReport(dlg,plugin_dir,cur,config,main_dlg):
    #print('---------Network report--------')
    # Get current project
    project = QgsProject.instance()
    manager = project.layoutManager()    
    srid=loadProjectConfig(config)['srid']
    
    # Remove existing layout with the same name
    layouts_list = manager.printLayouts()
    for layout in layouts_list:
        if layout.name() == "Network Report":  # Replace with your layout name
            manager.removeLayout(layout)

    # Create new print layout
    layout = QgsPrintLayout(project)        
    layout.setName("Network Report")  # Replace with your layout name
    y_layout = 155
    manager.addLayout(layout)

    # Add new page
    page = QgsLayoutItemPage(layout)
    page.setPageSize('A4', QgsLayoutItemPage.Portrait)
    layout.pageCollection().addPage(page)
    current_page = 1
    page_height = 297

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
    label_project.setText(tr("@default","project")+": ")
    label_project.setFont(font_header_label)
    label_project.adjustSizeToText()
    label_project.attemptMove(QgsLayoutPoint(20, 10, QgsUnitTypes.LayoutMillimeters))
    label_project.attemptResize(QgsLayoutSize(140, 15), True)

    project_ = QgsLayoutItemLabel(layout)
    project_.setText(config['projectName'])
    project_.setFont(font_header)
    project_.setFontColor(QColor("gray"))
    project_.adjustSizeToText()
    project_.attemptMove(QgsLayoutPoint(60, 10, QgsUnitTypes.LayoutMillimeters))
    project_.attemptResize(QgsLayoutSize(140, 15), True)


    # Add header project label
    label_version = QgsLayoutItemLabel(layout)
    label_version.setText(tr("@default","version")+": ")
    label_version.setFont(font_header_label)
    label_version.adjustSizeToText()
    label_version.attemptMove(QgsLayoutPoint(20, 18, QgsUnitTypes.LayoutMillimeters))
    label_version.attemptResize(QgsLayoutSize(140, 15), True)

    version = QgsLayoutItemLabel(layout)
    version.setText(config['versionName'])
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
    feature_layer = project.mapLayersByName(tr('@default','customers'))[0]
    feats = []
    for substation_feature in feature_layer.getFeatures():
        feats.append(substation_feature)
    #print(feats)
    #memory layer for customers
    layer_customer_mem = QgsVectorLayer("Point?crs=epsg:"+str(srid), tr("@default",'customer'), "memory")
    data_pr = layer_customer_mem.dataProvider()
    data_pr.addAttributes(feature_layer.fields())
    layer_customer_mem.updateFields()
    data_pr.addFeatures(feats)
    layer_customer_mem.setRenderer(feature_layer.renderer().clone())
    project.addMapLayer(layer_customer_mem)
    

    # Move Layer to top
    root = project.layerTreeRoot()
    myalayer = root.findLayer(layer_customer_mem.id())
    myClone = myalayer.clone()
    parent = myalayer.parent()
    parent.insertChildNode(0, myClone)
    parent.removeChildNode(myalayer)
    
    osm_layers = project.mapLayersByName('OpenStreetMap')
    if osm_layers:
        layer_osm = osm_layers[0]
        #print("OSM layer already exists")
        osm_existed=True
    else:
        # Add OSM XYZ Tile layer
        osm_existed=False
        url = "type=xyz&url=https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer_osm = QgsRasterLayer(url, "OpenStreetMap", "wms")  # "wms" works for XYZ in QGIS 3.40
        if not layer_osm.isValid():
            pass
            #print("Failed to load OSM layer")
        else:
            project.addMapLayer(layer_osm)
            #print("OSM layer added")
    
    
    feature_layer = project.mapLayersByName(tr('@default','energy_plants'))[0]
    feats = []
    for feature in feature_layer.getFeatures():
        feats.append(feature)
    #print(feats)
    #memory layer for energy plants
    layer_ep_mem = QgsVectorLayer("Point?crs=epsg:"+str(srid), tr("@default",'energy_plant'), "memory")
    data_pr = layer_ep_mem.dataProvider()
    data_pr.addAttributes(feature_layer.fields())
    layer_ep_mem.updateFields()
    data_pr.addFeatures(feats)
    layer_ep_mem.setRenderer(feature_layer.renderer().clone())
    project.addMapLayer(layer_ep_mem)
    
    feature_layer = project.mapLayersByName(tr('@default','lines'))[0]
    feats = []
    for feature in feature_layer.getFeatures():
        feats.append(feature)
    #print(feats)

    #memory layer for lines
    layer_network_mem = QgsVectorLayer("LineString?crs=epsg:"+str(srid), tr("@default",'line'), "memory")
    data_pr = layer_network_mem.dataProvider()
    data_pr.addAttributes(feature_layer.fields())
    layer_network_mem.updateFields()
    data_pr.addFeatures(feats)
    layer_network_mem.setRenderer(feature_layer.renderer().clone())
    project.addMapLayer(layer_network_mem)
    network_extent = layer_network_mem.extent()

    # ------------map-------------
    #Map
    map=QgsLayoutItemMap(layout)
    map.setRect(10,10,10,10)

    #Set Map Extent
    #defines map extent using map coordinates
    #get coordinates

    boundary_ext=network_extent.width()/5
    rectangle = QgsRectangle(
    network_extent.xMinimum()-boundary_ext,
    network_extent.yMinimum()-boundary_ext,
    network_extent.xMaximum() + network_extent.width() / 3 + boundary_ext,
    network_extent.yMaximum()+boundary_ext
)
    map.setExtent(rectangle)
    
    map.attemptMove(QgsLayoutPoint(20,30,QgsUnitTypes.LayoutMillimeters))
    map.attemptResize(QgsLayoutSize(170,120, QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(map)

    # legend
    root = QgsLayerTree()
    root.addLayer(layer_customer_mem)
    root.addLayer(layer_ep_mem)
    root.addLayer(layer_network_mem)
    root.addLayer(layer_osm)


    # Legenden-Objekt erstellen und hinzufügen (wie bisher)
    legend = QgsLayoutItemLegend(layout)
    legend.model().setRootGroup(root)
    legend.setLinkedMap(map)
    layout.addLayoutItem(legend)
    
    # Set layer font size
    style = legend.style(QgsLegendStyle.SymbolLabel)
    font = style.font()
    font.setPointSize(8)
    style.setFont(font)
    legend.setStyle(QgsLegendStyle.SymbolLabel, style)

    # Set group font size
    style = legend.style(QgsLegendStyle.Group)
    font = style.font()
    font.setPointSize(9)
    style.setFont(font)
    legend.setStyle(QgsLegendStyle.Group, style)

    # Set title font size
    style = legend.style(QgsLegendStyle.Title)
    font = style.font()
    font.setPointSize(10)
    style.setFont(font)
    legend.setStyle(QgsLegendStyle.Title, style)
    
    legend.setSymbolWidth(5)   # mm
    legend.setSymbolHeight(1)  # mm
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

    map.setLayers([layer_customer_mem,layer_ep_mem,layer_network_mem,layer_osm])
    
    #------------kpi table--------------
    if dlg.checkBox_kpi.isChecked():
        #print('------------kpi table--------------')
        # --- 1. prepare data ---
        sql="""SELECT * FROM "{}".kpi;""".format(config['versionName'])
        cur.execute(sql)
        kpi_table=cur.fetchone()
        kpis=[{i:float(kpi_table[i])} for i in kpi_table if kpi_table[i] is not None and i!='id']
        #print(kpis)
        requestedOutputs=loadRequestedOutputs(plugin_dir,config)
        if requestedOutputs['qsup_heat_spec_c_kpi'] and kpi_table['qsup_heat_c'] is not None:
            value = float(kpi_table['qsup_heat_c'])/getBuildingsEra(cur,config)
            kpis.append({'qsup_heat_spec_c':value})
        if requestedOutputs['qsup_cold_spec_c_kpi'] and kpi_table['qsup_cold_c'] is not None:
            value = float(kpi_table['qsup_cold_c'])/getBuildingsEra(cur,config)
            kpis.append({'qsup_cold_spec_c':value})
        if requestedOutputs['qsup_spec_c_kpi'] and kpi_table['qsup_c'] is not None:
            value = float(kpi_table['qsup_c'])/getBuildingsEra(cur,config)
            kpis.append({'qsup_spec_c':value})

        if requestedOutputs['qsup_heat_density_c_kpi'] and kpi_table['qsup_heat_c'] is not None:
            value = float(kpi_table['qsup_heat_c'])/network_extent.width()/network_extent.height()
            kpis.append({'qsup_heat_density_c':value})
        if requestedOutputs['qsup_cold_density_c_kpi'] and kpi_table['qsup_cold_c'] is not None:
            value = float(kpi_table['qsup_cold_c'])/network_extent.width()/network_extent.height()
            kpis.append({'qsup_cold_density_c':value})
        if requestedOutputs['qsup_density_c_kpi'] and kpi_table['qsup_c'] is not None:
            value = float(kpi_table['qsup_c'])/network_extent.width()/network_extent.height()
            kpis.append({'qsup_density_c':value})

        if requestedOutputs['qsup_heat_linedensity_c_kpi'] and kpi_table['qsup_heat_c'] is not None:
            value = float(kpi_table['qsup_heat_c'])/getNetworkLength(cur,config)
            kpis.append({'qsup_heat_linedensity_c':value})
        if requestedOutputs['qsup_cold_linedensity_c_kpi'] and kpi_table['qsup_cold_c'] is not None:
            value = float(kpi_table['qsup_cold_c'])/getNetworkLength(cur,config)
            kpis.append({'qsup_cold_linedensity_c':value})
        if requestedOutputs['qsup_linedensity_c_kpi'] and kpi_table['qsup_c'] is not None:
            value = float(kpi_table['qsup_c'])/getNetworkLength(cur,config)
            kpis.append({'qsup_linedensity_c':value})

        if requestedOutputs['eff_width']:
            value = network_extent.width()*network_extent.height()/getNetworkLength(cur,config)
            kpis.append({'eff_width':value})
        
        if requestedOutputs['volume_kpi']:
            value = getNetworkVolume(cur,config)
            kpis.append({'volume':value})

        num_entries = len(kpis)

        # define layout-mode: 4 columns if more than 4 entries
        columns_count = 4 if num_entries > 4 else 2
        table_data = []

        if columns_count == 4:
            # calc line counter for 2-block-layout
            rows_needed = math.ceil(num_entries / 2)
            for i in range(rows_needed):
                row = []
                # left block
                #print(kpis[i])
                (name_l, val_l), = kpis[i].items()         
                row.extend([tr("@default",name_l), "{:.3g}".format(val_l),getKPIUnit(name_l)])
                
                # right block
                idx_right = i + rows_needed
                if idx_right < num_entries:
                    (name_r, val_r), = kpis[idx_right].items()
                    row.extend([tr("@default",name_r), "{:.3g}".format(val_r),getKPIUnit(name_r)])
                else:
                    row.extend(["", ""]) # Padding
                table_data.append(row)
        else:
            # 2-column layout
            table_data = [[tr("@default",key), "{:.3g}".format(value),getKPIUnit(key)] for d in kpis for key, value in d.items()]
        #print(table_data)

        # --- 2. initalize table  ---
        table = QgsLayoutItemTextTable(layout)
        layout.addMultiFrame(table)

        # --- 3. define coulumn (HEADER) ---
        header_labels = [(tr("@default","kpi"),45), (tr("@default","value"),15),(tr("@default","unit"),21)] * (columns_count // 2)
        cols = []
        for label,width in header_labels:
            col = QgsLayoutTableColumn()
            col.setHeading(label)
            col.setWidth(width if columns_count == 4 else width+10) 
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

        # write data to table
        table.setContents(table_data)

        # --- 5. Generate FRAME  & registration ---
        frame = QgsLayoutFrame(layout, table)
        frame.setId("AttributTabelle")
        layout.addLayoutItem(frame)
        table.addFrame(frame)

        # --- 6. geomatry & position ---
        table.refreshAttributes()
        width = 170 if columns_count == 4 else 100

        y_layout +=table.totalHeight() + 1.5
        frame.attemptResize(QgsLayoutSize(width, max(10, y_layout), QgsUnitTypes.LayoutMillimeters))
        frame.attemptMove(QgsLayoutPoint(20, 155, QgsUnitTypes.LayoutMillimeters))
    
    #-------------pipes table---------
    if dlg.checkBox_pipeTable.isChecked():
        # Create a new page
        new_page = QgsLayoutItemPage(layout)

        # Optional: set size and orientation (default is A4 Portrait)
        new_page.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
        layout.pageCollection().addPage(new_page)
        y_layout=25
        current_page = layout.pageCollection().pageCount()
        
        
        # Add title pipe info
        label_pipe_info = QgsLayoutItemLabel(layout)
        label_pipe_info.setText(tr("@default","pipe_info_titel"))
        label_pipe_info.setFont(font_header_label)
        label_pipe_info.adjustSizeToText()
        label_pipe_info.attemptMove(QgsLayoutPoint(20, y_layout + (current_page-1) * page_height, QgsUnitTypes.LayoutMillimeters))
        label_pipe_info.attemptResize(QgsLayoutSize(140, 15), True)
        layout.addLayoutItem(label_pipe_info)
        y_layout+=8
        
        networks=getNetworks(cur,config)
        #print(networks)
        label_networks={}
        table_networks={}
        frame_networks={}
        for network in networks:
            pipe_info=getPipeInfo(cur,config,networks=[network])
            #print(pipe_info)
            table_data=[[i['name'],"{:.3g}".format(i['innerpipediameter']),"{:.3g}".format(i['length']),"{:.3g}".format(i['costs']) if i['costs'] is not None else ''] for i in pipe_info]
            table_data.append(['∑','',"{:.3g}".format(sum([i['length'] for i in pipe_info])),"{:.3g}".format(sum([i['costs'] for i in pipe_info if i['costs'] is not None]))])
            
            #print(y_layout)
            #print(y_layout+len(table_data)*5)
            if y_layout+len(table_data)*5 >290:
            # Create a new page
                new_page = QgsLayoutItemPage(layout)

                # Optional: set size and orientation (default is A4 Portrait)
                new_page.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
                layout.pageCollection().addPage(new_page)
                y_layout=25
                current_page = layout.pageCollection().pageCount()
                
            # Add title network
            label_networks[network] = QgsLayoutItemLabel(layout)
            label_networks[network].setText(tr("@default","network")+': '+network)
            label_networks[network].setFont(font_header_label)
            label_networks[network].adjustSizeToText()
            #print(y_layout + (current_page-1) * page_height)
            label_networks[network].attemptMove(QgsLayoutPoint(20,y_layout + (current_page-1) * page_height, QgsUnitTypes.LayoutMillimeters))
            label_networks[network].attemptResize(QgsLayoutSize(140, 15), True)
            layout.addLayoutItem(label_networks[network])

            # --- initalize table  ---
            table_networks[network] = QgsLayoutItemTextTable(layout)
            layout.addMultiFrame(table_networks[network])

            # --- define coulumn (HEADER) ---
            header_labels = [(tr("@default","pipe"),45), (tr("@default","innerdiameter"),40),(tr("@default","length"),25),(tr("@default","costs"),25)]
            cols = []
            for label,width in header_labels:
                col = QgsLayoutTableColumn()
                col.setHeading(label)
                col.setWidth(width) 
                cols.append(col)
            table_networks[network] .setColumns(cols)

            # --- STYLING ---
            table_networks[network] .setGridStrokeWidth(0.000001) 
            table_networks[network] .setGridColor(QColor("White"))

            # Content Text Format
            content_text_format = QgsTextFormat()
            content_text_format.setFont(font_table) 
            content_text_format.setColor(QColor("Black"))
            table_networks[network] .setContentTextFormat(content_text_format)

            # Header Text Format
            header_text_format = QgsTextFormat()
            header_text_format.setFont(font_table_label)
            header_text_format.setColor(QColor("Black"))
            table_networks[network] .setHeaderTextFormat(header_text_format)

            # write data to table
            table_networks[network] .setContents(table_data)

            # --- Generate FRAME  & registration ---
            frame_networks[network] = QgsLayoutFrame(layout, table_networks[network])
            frame_networks[network].setId("table network "+network)
            
            layout.addLayoutItem(frame_networks[network])
            table_networks[network] .addFrame(frame_networks[network])

            # --- 6. geomatry & position ---
            table_networks[network] .refreshAttributes()
            width = 170

            y_layout+=8
            frame_networks[network].attemptResize(QgsLayoutSize(width, max(10, table_networks[network] .totalHeight() + 1.5), QgsUnitTypes.LayoutMillimeters))
            frame_networks[network].attemptMove(QgsLayoutPoint(20, y_layout + (current_page-1) * page_height, QgsUnitTypes.LayoutMillimeters))
            
            y_layout+=table_networks[network].totalHeight()

    #plot images
    map_layers=[]
    if dlg.data:
        # Create a new page
        new_page = QgsLayoutItemPage(layout)

        # Optional: set size and orientation (default is A4 Portrait)
        new_page.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
        layout.pageCollection().addPage(new_page)
        y_layout=35
        current_page = layout.pageCollection().pageCount()

        
        # Add title pipe info
        label_map_plots = QgsLayoutItemLabel(layout)
        label_map_plots.setText(tr("@default","map_plots"))
        label_map_plots.setFont(font_header_label)
        label_map_plots.adjustSizeToText()
        label_map_plots.attemptMove(QgsLayoutPoint(20,y_layout - 10 + (current_page-1) * page_height, QgsUnitTypes.LayoutMillimeters))
        label_map_plots.attemptResize(QgsLayoutSize(140, 15), True)
        layout.addLayoutItem(label_map_plots)

        maps={}
        legends={}
        roots={}
        north={}
        scales={}
        page_image_counter=0
        for counter,plot in enumerate(dlg.data):
            if counter%2==0 and counter!=0:
                # Create a new page
                new_page = QgsLayoutItemPage(layout)

                # Optional: set size and orientation (default is A4 Portrait)
                new_page.setPageSize('A4', QgsLayoutItemPage.Orientation.Portrait)
                layout.pageCollection().addPage(new_page)
                y_layout=35
                current_page = layout.pageCollection().pageCount()
                page_image_counter=0
            elif counter==0:
                pass
            else:
                page_image_counter+=1
            #print(plot)
            plot_layer=showOnMapMemoryLayer(plot['data'],config,plugin_dir,plot['feature'],plot['name'])
            renderMapPlot(plot_layer,plot['data'],cur,config,first_time_var=plot['first_time_var'],color_classes=plot['color_classes'],colormode=plot['colormode'],
                colorramp=plot['colorramp'],feature=plot['feature'],varRotation=plot['varRotation'],size_symbolMin=plot['size_symbolMin'],size_symbolMax=plot['size_symbolMax'],
                rotation_symbolMin=plot['rotation_symbolMin'],rotation_symbolMax=plot['rotation_symbolMax'],networkReportDlg=True)
                
            # 1) Ensure no edit session is open
            if plot_layer.isEditable():
                try:
                    plot_layer.commitChanges()
                    #print("Committed pending edits.")
                except Exception as e:
                    #print("Commit error:", e)
                    plot_layer.rollBack()

            map_layers=[plot_layer]
            if plot['feature'] == 'line':
                map_layers.append(layer_customer_mem)
                map_layers.append(layer_ep_mem)
            elif plot['feature'] == 'customer':
                map_layers.append(layer_network_mem)
                map_layers.append(layer_ep_mem)            
            elif plot['feature'] == 'energy_plant':
                map_layers.append(layer_customer_mem)
                map_layers.append(layer_network_mem)
            map_layers.append(layer_osm)
            #print(map_layers)
                

            # ------------map-------------
            #Map
            maps[counter]=QgsLayoutItemMap(layout)
            maps[counter].setRect(10,10,10,10)

            #Set Map Extent
            #defines map extent using map coordinates
            #get coordinates

            boundary_ext=network_extent.width()/5
            rectangle = QgsRectangle(
            network_extent.xMinimum()-boundary_ext,
            network_extent.yMinimum()-boundary_ext,
            network_extent.xMaximum() + network_extent.width() / 3 + boundary_ext,
            network_extent.yMaximum()+boundary_ext
        )
            maps[counter].setExtent(rectangle)
            
            maps[counter].attemptMove(QgsLayoutPoint(20,y_layout + (current_page-1) * page_height+page_image_counter*130,QgsUnitTypes.LayoutMillimeters))
            maps[counter].attemptResize(QgsLayoutSize(170,120, QgsUnitTypes.LayoutMillimeters))
            layout.addLayoutItem(maps[counter])

            # legend
            roots[counter] = QgsLayerTree()
            for layer in map_layers:
                roots[counter].addLayer(layer)
                
            # Legenden-Objekt erstellen und hinzufügen (wie bisher)
            legends[counter] = QgsLayoutItemLegend(layout)
            legends[counter].model().setRootGroup(roots[counter])
            legends[counter].setLinkedMap(maps[counter])
            layout.addLayoutItem(legends[counter])
            
            # Set layer font size
            style = legends[counter].style(QgsLegendStyle.SymbolLabel)
            font = style.font()
            font.setPointSize(8)
            style.setFont(font)
            legends[counter].setStyle(QgsLegendStyle.SymbolLabel, style)

            # Set group font size
            style = legends[counter].style(QgsLegendStyle.Group)
            font = style.font()
            font.setPointSize(9)
            style.setFont(font)
            legends[counter].setStyle(QgsLegendStyle.Group, style)

            # Set title font size
            style = legends[counter].style(QgsLegendStyle.Title)
            font = style.font()
            font.setPointSize(10)
            style.setFont(font)
            legends[counter].setStyle(QgsLegendStyle.Title, style)
            
            legends[counter].setSymbolWidth(5)   # mm
            legends[counter].setSymbolHeight(1)  # mm
            
            # position and size
            legends[counter].setResizeToContents(False)
            legends[counter].attemptResize(QgsLayoutSize(50, 110, QgsUnitTypes.LayoutMillimeters))
            legends[counter].attemptMove(QgsLayoutPoint(138,  40 + (current_page-1) * page_height+page_image_counter*130, QgsUnitTypes.LayoutMillimeters))
            

            #Add scale bar    
            scales[counter]=QgsLayoutItemScaleBar(layout)
            scales[counter].setStyle('Single Box')
            scales[counter].setFont(QFont("Arial",15))
            scales[counter].setFontColor(QColor("Black"))
            scales[counter].setBackgroundEnabled(True)
            scales[counter].setFillColor(QColor("Black"))
            scales[counter].applyDefaultSize(QgsUnitTypes.DistanceMeters)
            scales[counter].setMapUnitsPerScaleBarUnit(1)
            scales[counter].setNumberOfSegments(2)
            scales[counter].setUnitsPerSegment(50)
            scales[counter].setUnitLabel("m")
            scales[counter].setLinkedMap(map)
            layout.addLayoutItem(scales[counter])
            scales[counter].attemptMove(QgsLayoutPoint(22,y_layout+105+(current_page-1) * page_height+page_image_counter*130,QgsUnitTypes.LayoutMillimeters))
            scales[counter].attemptResize(QgsLayoutSize(50,8, QgsUnitTypes.LayoutMillimeters))

            #north arrow 
            north[counter]=QgsLayoutItemPicture(layout)
            north[counter].setMode(QgsLayoutItemPicture.FormatSVG)
            north[counter].setPicturePath(":/images/north_arrows/layout_default_north_arrow.svg")
            north[counter].attemptMove(QgsLayoutPoint(25, y_layout+10+(current_page-1) * page_height+page_image_counter*130, QgsUnitTypes.LayoutMillimeters))
            north[counter].attemptResize(QgsLayoutSize(*[150,150], QgsUnitTypes.LayoutPixels))
            layout.addLayoutItem(north[counter])

            #print(map_layers)
            maps[counter].setLayers(map_layers)
    
    #pdf
    temp_folder = tempfile.gettempdir()+'\\'
    createDir(temp_folder,'ida_districts')
    export_path=temp_folder+'ida_districts\\'
    export_path=export_path.replace('/',"\\")
    #print(export_path)
    if os.path.exists(export_path):
        export_path+='network_report.pdf'
        #print(export_path)
        export = QgsLayoutExporter(layout)
        export.exportToPdf(export_path, QgsLayoutExporter.PdfExportSettings())

        os.startfile(export_path)
        
    
    #Redo changes
    project.removeMapLayer(layer_customer_mem)
    project.removeMapLayer(layer_ep_mem)
    project.removeMapLayer(layer_network_mem)
    #for layer in map_layers:
    #    project.removeMapLayer(layer)
    if not osm_existed:
        try:
            project.removeMapLayer(layer_osm)
        except:
            pass
    iface.mapCanvas().refresh()

def setupCustomerDataSheet(config,plugin_dir,projectConfig):
    """Setup of the customer data sheet (RMB project) including button which generates a print layout and exports a pdf"""
    
    feature_layer=QgsProject.instance().mapLayersByName(tr('@default','customers'))[0] 
    #print(feature_layer)
    
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
from districts.utility_functions.files import *


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
buildings_layer=QgsProject.instance().mapLayersByName(tr('@default','buildings'))[0]
#print('---buildings----')
#print([% $x %])
#print(QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ))
feats = []
for building_feature in buildings_layer.getFeatures():
    if QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ).within(building_feature.geometry()):
        feats.append(building_feature)
#print(feats)

layer_buildings_mem = QgsVectorLayer("Polygon?crs=epsg:"+str(srid), tr('@default',"buildings"), "memory")
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

feature_layer = project.mapLayersByName(tr('@default','customers'))[0]
feats = []
for substation_feature in feature_layer.getFeatures():
    if QgsGeometry.fromWkt( 'POINT( [% $x %] [% $y %])' ).within(substation_feature.geometry()):
        feats.append(substation_feature)
#print(feats)
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
    osm_existed=True
    #print("OSM layer already exists")
else:
    # Add OSM XYZ Tile layer
    osm_existed=False
    url = "type=xyz&url=https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png"
    layer_osm = QgsRasterLayer(url, "OpenStreetMap", "wms")  # "wms" works for XYZ in QGIS 3.40
    if not layer_osm.isValid():
        pass
        #print("Failed to load OSM layer")
    else:
        project.addMapLayer(layer_osm)
        #print("OSM layer added")

layer_network = project.mapLayersByName(tr('@default','lines'))[0]
layer_ep = project.mapLayersByName(tr('@default','energy_plants'))[0]
  
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
#print('------------attribute table--------------')
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
#print([%id%])
try:
    filenames=matplotlibPowerPlots(plugin_dir,config,cur,[%id%],feature_type='customer',show_plot=False,save_plot=True)
except:
    filenames=[]
#print(filenames)
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
#print(export_path)
if os.path.exists(export_path):
    export_path+='customer_'+str([%id%])+'_report.pdf'
    #print(export_path)
    export = QgsLayoutExporter(layout)
    export.exportToPdf(export_path, QgsLayoutExporter.PdfExportSettings())

    subprocess.Popen([export_path],shell=True)
    
#Redo changes
project.removeMapLayer(layer_customer_mem)
project.removeMapLayer(layer_buildings_mem)
if not osm_existed:
    project.removeMapLayer(layer_osm)

iface.mapCanvas().refresh()
""".format(config['projectName'],config['versionName'],projectConfig['srid'],config)

    #print(action_text)

    helpAction = QgsAction(Qgis.AttributeActionType.GenericPython, tr('@default','customer_data_sheet'), action_text, None, capture=False, shortTitle=tr('@default','customer_data_sheet'), actionScopes={'Feature'})
    feature_layer.actions().addAction(helpAction)

    form_config = feature_layer.editFormConfig()

    rootContainer = form_config.invisibleRootContainer()
    #print(rootContainer)
    editorAction = QgsAttributeEditorAction(helpAction, rootContainer)
    rootContainer.addChildElement(editorAction)

    feature_layer.setEditFormConfig(form_config)