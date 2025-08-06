from qgis.PyQt.QtCore import QDateTime,QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon,QKeySequence
from qgis.PyQt.QtWidgets import QShortcut,QDockWidget,QAction,QListWidgetItem,QFileDialog,QStackedWidget,QListView,QLineEdit,QDialog,QTableWidgetItem
from .ida_districts_result_visualization_dialog import IDADistrictsResultVisualizationDialog,IDADistrictsPathReportsDialog,PlotLoadProfilesDialog,ImportMeasuremntsDialog, ShowOnMapDialog
from qgis.core import QgsTemporalNavigationObject,QgsGeometry,QgsInterval,QgsDateTimeRange,QgsVectorLayer,QgsFeature,QgsClassificationEqualInterval,QgsRendererRangeLabelFormat,QgsStyle,QgsGraduatedSymbolRenderer, QgsSingleSymbolRenderer,QgsSymbol,QgsFilledMarkerSymbolLayer,QgsSymbolLayer,QgsProperty,Qgis
from qgis.gui import QgsMapCanvas,QgsTemporalControllerWidget
from plugins.utility_functions.util import *
from plugins.utility_functions.files import *
from plugins.utility_functions.db import *
from plugins.utility_functions.dialog import *
from plugins.utility_functions.show_on_map import *
from qgis.PyQt import sip

# Initialize Qt resources from file resources.py
from .resources import *

import os.path
import psycopg2
import psycopg2.extras
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib

import datetime
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
from PyQt5.QtCore import Qt

class IDADistrictsResultVisualization:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__).replace('/','\\')
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'IDADistrictsResultVisualization_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&IDADistricts Result Visualization')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.requestedOutputs=loadRequestedOutputs(self.plugin_dir,self.dictDB)
        self.modellingSettings=loadModellingSettings(self.plugin_dir,self.dictDB)
        #print(self.requestedOutputs)
        self.cur=''
        self.conn=''

        shortcut = QShortcut(QKeySequence('Alt+Shift+R'), iface.mainWindow())
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(self.openPlugin)

    def openPlugin(self):
        self.run()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('IDADistrictsResultVisualization', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        #icon_path = ':/plugins/ida_districts_result_visualization/icon-result-visualization.png'
        #icon_path='C:\\Users\\Peter\\AppData\\Roaming\\QGIS\\QGIS3\\profiles\\default\\python\\plugins\\ida_districts_result_visualization\\icon-result-visualization.png'
        icon_path = self.plugin_dir+'\\icon-result-visualization.png'
        self.add_action(
            icon_path,
            text=self.tr(u'IDA Districts Result Visualization'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&IDADistricts Result Visualization'),
                action)
            self.iface.removeToolBarIcon(action)

    def getCustomerId(self,lids):
        sql="""SELECT c.id, ST_Z(ST_EndPoint(l.geom)) AS height, c.submodel,b_t_conns.conn_type_id
    FROM "{}".customers c, "{}".lines l, customer_templates c_t, bundle_type_conns b_t_conns, "{}".customer_connections c_conns
    WHERE c_conns.c_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=c_t.conn_bundle_type AND 
        l.id IN ({}) AND c_t.template=c.template AND c_conns.cid=c.id AND l.id=c_conns.lid
    GROUP BY c.id,l.geom, b_t_conns.conn_type_id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],','.join(str(i[0]) for i in lids))
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        cid=[[str(data['id']),data['height']],data['submodel'],data['conn_type_id']]
        #print(cid)
        return cid
        
    def getEnergyPlantId(self,lids):
        sql="""SELECT ep.id AS epid, l.id AS lid, ST_length(l.geom) AS length, ST_Z(ST_StartPoint(l.geom)) AS height,ep.submodel, b_t_conns.conn_type_id
    FROM "{}".energy_plants ep, "{}".lines l, energy_plant_templates ep_t, bundle_type_conns b_t_conns, "{}".energy_plant_connections ep_conns
    WHERE  l.id IN ({}) AND ep_t.template=ep.template AND 
        ep_conns.ep_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=ep_t.conn_bundle_type AND ep_conns.epid=ep.id AND l.id=ep_conns.lid
    GROUP BY ep.id,l.id, height,l.geom,b_t_conns.conn_type_id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],','.join(str(i) for i in lids))
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        epid=[str(data['epid']),data['height']]
        lid=[str(data['lid']),data['length']]
        return [epid,lid,data['submodel'],data['conn_type_id']]

    def getMainEnergyPlantId(self,network):
        sql="""SELECT ep.id AS epid, l.id AS lid, ST_length(l.geom) AS length, ST_Z(ST_StartPoint(l.geom)) AS height,ep.submodel, b_t_conns.conn_type_id
    FROM "{}".energy_plants ep, "{}".lines l,energy_plant_templates ep_t, bundle_type_conns b_t_conns, "{}".energy_plant_connections ep_conns
    WHERE {} = ANY (ep.network) AND l.network={} AND ep_t.template=ep.template AND
        ep_conns.ep_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=ep_t.conn_bundle_type AND ep_conns.epid=ep.id AND l.id=ep_conns.lid
    GROUP BY ep.id,l.id, height,l.geom, b_t_conns.conn_type_id
    ORDER BY ep.id LIMIT 1;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],network,network)
        #print(sql)
        self.cur.execute(sql)
        data=self.cur.fetchone()
        epid=[str(data['epid']),data['height']]
        lid=[str(data['lid']),data['length']]
        return [epid,lid,data['submodel'],data['conn_type_id']]
        
    def orderLids(self,lids,lid_start):
        """returns [[str(id),length]]"""
        #print('order lids')
        path=[0]
        lids_new=[lid_start]
        #print(lid_start[1])
        path.append(lid_start[1])
        length_sum=lid_start[1]
        for i in range(len(lids)-1):
            sql="""SELECT l2.id,ST_3DLength(l2.geom) AS length
    FROM "{}".lines l1, "{}".lines l2
    WHERE l1.id!=l2.id AND l1.id={} AND l2.id IN ({}) AND ST_dWithIn(ST_EndPoint(l1.geom),l2.geom,0.0001) """.format(self.dictDB['versionName'],self.dictDB['versionName'],lids_new[-1][0],",".join([str(lid) for lid in lids]))
            #print(sql)
            self.cur.execute(sql)
            data=self.cur.fetchone()
            lids_new.append([str(data['id']),data['length']])
            length_sum+=data['length']
            path.append(length_sum)
        #print(lids_new)
        return lids_new,path
        
    def getJids(self,lids):
        """[[str(id),height]]"""
        #print('get jids')
        jids=[]
        for lid in lids[:-1]:
            sql="""SELECT j.id,ST_Z(ST_EndPoint(l.geom)) AS height
    FROM "{}".lines l,"{}".junctions j
    WHERE l.id={} AND ST_dWithIn(ST_EndPoint(l.geom),j.geom,0.0001);""".format(self.dictDB['versionName'],self.dictDB['versionName'],lid[0])
            #print(sql)
            self.cur.execute(sql)
            data=self.cur.fetchone()
            #print(data)
            if data:
                jids.append([str(data['id']),data['height']])
            else:
                jids.append(['0','0'])
        #print(jids)
        return jids
    
    def getJunctionVariables(self,jids,filedata_j):
        variables={}
        counter=2
        jid_old=''
        connections={}
        for filedata in filedata_j:
            for var in filedata[0].strip().split()[3:]:
                jid=var.split('_')[1]
                #print('jid:'+str(jid)+'; jid_old: '+str(jid_old))
                if jid!=jid_old and counter!=3:
                    #print(connections)
                    if jid_old in [jid[0] for jid in jids]:
                        #print(connections)
                        variables[jid_old]=connections
                    connections={}
                connections[var.split('_')[2]]=[counter,counter-1]
                #print(connections)
                counter+=1
                jid_old=jid
            if connections and jid_old in [jid[0] for jid in jids]:
                #print('++')
                variables[jid_old]=connections
        #print(variables)
        return variables
        
    def getMaxRow(self,filedata_ep,filedata_c,col_sup,col_ret,epid,cid,quantity):
        max_value=0
        i_max=1
        #print('col sup'+str(col_sup)) 
        for i in range(1,len(filedata_c)):
            value=float(filedata_ep[i].strip().split()[col_sup])-float(filedata_c[i].strip().split()[col_sup])+((epid[1]-cid[1])/10*10**5 if quantity=='pressure'else 0) #add height because only the dynamic pressure is considered; 10m --> 1 bar
            if value>max_value:
                max_value=value
                i_max=i
        return [i_max,max_value]
        
    def getDateRow(self,filedata_ep,filedata_c,col_sup,col_ret,epid,cid,quantity,date):
        value=0
        row_counter=1
        date=float(date)
        closest_date=0
            
        for i in range(1,len(filedata_c)):
            date_row=float(filedata_ep[i].strip().split()[0]) #add height because only the dynamic pressure is considered; 10m --> 1 bar
            if abs(date_row-date)<abs(closest_date-date):
                closest_date=date_row
                row_counter=i
                value=float(filedata_ep[i].strip().split()[col_sup])-float(filedata_c[i].strip().split()[col_sup])+((epid[1]-cid[1])/10*10**5 if quantity=='pressure'else 0)
        return [row_counter,value]
        
    def getDataJunction(self,filedata_j,i_max):
        col_counter=0
        data_j=[]
        for filedata in filedata_j:
            for data in filedata[i_max].strip().split():
                if col_counter !=1:
                    data_j.append(float(data))
                col_counter+=1
        return data_j
        
    def showplot(self,data_j,jids,epid,cid,path,data_ep,data_c,variables,quantity,title):
        #print(data_ep[0])
        #print(data_c[0])
        #print(variables)
        for jid in jids:
            #print(jid)
            #print(jid[0])
            #print(variables[jid[0]]['1'])
            pass
        quantity_data_sup=[data_ep[0]]+[data_j[variables[jid[0]]['1'][1]] for jid in jids]+[data_c[0]]
        quantity_data_ret=[data_ep[1]]+[data_j[variables[jid[0]]['2'][1]] for jid in jids]+[data_c[1]]
        height=[epid[1]]+[jid[1] for jid in jids]+[cid[1]]

        #print(height)
        #print(quantity_data_sup)
        #print(quantity_data_ret)
        fig, (ax1, ax2) = plt.subplots(2, 1)
        fig.suptitle(title)
        ax1.plot(path, quantity_data_sup, linewidth=4.0)
        ax1.plot(path, quantity_data_ret, linewidth=4.0)
        ax1.grid(True)
        
        #ax1.set_xlabel('Length, m')
        ax1.set_xlabel('Trasse, m')
        if quantity=='pressure':
            #ax1.set_ylabel('Pressure, Pa')
            ax1.set_ylabel('Druck, Pa')
        else:
            #ax1.set_ylabel('Temperature, °C')
            ax1.set_ylabel('Temperatur, °C')
            
        ax2.plot(path, height,linewidth=3.0)    
        #ax2.set_xlabel('Length, m')
        ax2.set_xlabel('Trasse, m')
        #ax2.set_ylabel('Height level, m')
        ax2.set_ylabel('Höhenprofil, m')
        ax2.grid(True)
        
        SMALL_SIZE = 24
        MEDIUM_SIZE = 30
        BIGGER_SIZE = 40

        plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
        plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
        plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
        plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
        plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
        plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
        plt.rc('figure', figsize=(30.0, 20.0))  # fontsize of the figure title
        #manager = plt.get_current_fig_manager()
        #manager.window.showMaximized()
        plt.show()
        #fig.savefig('C:\\Users\\Peter\\RMB Group AG\\EXT 140000 FW Zollikon - Dokumente\\General\\02 Equa\\Simulation\\Ergebnisse\\Sportplatz\\Temperaturschaubilder\\Temperaturschaubild Fohrbach Kunde {}.png'.format(str(cid[0])))
    
    def generatePathReport(self,dlg):
        """Just fo supply and return line. Todo update to all connection types"""
        #print('generate path diagram')
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)
        if dlg.rbtn_pathTemp.isChecked():
            quantity='temperature'
        elif dlg.rbtn_pathPressure.isChecked():
            quantity='pressure'            
        col_sup=3
        col_ret=2
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
                            
            submodels=getNetworkSubmodels(self.cur,self.dictDB,[dlg.network.currentText()])
            filedata_j=[]
            for submodel in submodels:
                file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],submodel,'p_lines' if quantity=='pressure' else 'Temp_nodes')
                #print(file)
                filedata_j.append(readFileToList(file))
            
            if dlg.rbtn_lineIds.isChecked():   
                lids=[dlg.listWidget_ids.item(i).text() for i in range(dlg.listWidget_ids.count())]
                #print(lids)
                
                #ep id
                epid,lid_start,submodel,conn_type=self.getEnergyPlantId(lids)
                file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\energy_plant_{}\\{}_{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],submodel,epid[0],quantity,conn_type)
                #print(file)
                filedata_ep=readFileToList(file)
                
                lids,path=self.orderLids(lids,lid_start)
                #customer id
                cid,submodel,conn_type=self.getCustomerId(lids)
                
                file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\Customer_{}\\{}_{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],submodel,cid[0],quantity,conn_type)
                #print(file)
                filedata_c=readFileToList(file)
                      
                i_max,max_value=self.getMaxRow(filedata_ep,filedata_c,col_sup,col_ret,epid,cid,quantity)
                        
                data_ep=[float(filedata_ep[i_max].strip().split()[col_sup]),float(filedata_ep[i_max].strip().split()[col_ret])]
                data_c=[float(filedata_c[i_max].strip().split()[col_sup]),float(filedata_c[i_max].strip().split()[col_ret])]

                #junction ids               
                jids=self.getJids(lids)               
                
                #print(filedata_j)

                variables=self.getJunctionVariables(jids,filedata_j)
                
                data_j=self.getDataJunction(filedata_j,i_max)
                    
                #print(path)
                #print(data_ep)
                #print(data_c)
                #print(data_j)
                
                title='Time= '+str(data_j[0])+'h ; Customer ID='+cid[0]+'; Energy plant ID='+epid[0]+'; Line Ids='+','.join([str(lid[0]) for lid in lids])
                self.showplot(data_j,jids,epid,cid,path,data_ep,data_c,variables,quantity,title)

            elif dlg.rbtn_weakPoint.isChecked() or dlg.rbtn_customer.isChecked() or dlg.rbtn_energy_plant.isChecked():
                #ep id
                epid,lid_start,submodel,conn_type=self.getMainEnergyPlantId(dlg.network.currentText())
                file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\energy_plant_{}\\{}_{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],submodel,epid[0],quantity,conn_type)
                #print(file)
                filedata_ep=readFileToList(file)
                if dlg.rbtn_weakPoint.isChecked():
                    sql="""(SELECT c.id,ST_Z(ST_EndPoint(l.geom)) AS height,'customer' AS feature,c.submodel, b_t_conns.conn_type_id
    FROM "{}".customers c, "{}".lines l, "{}".customer_connections c_conns, customer_templates c_t, bundle_type_conns b_t_conns
    WHERE c_conns.c_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=c_t.conn_bundle_type AND c_conns.cid=c.id AND l.id=c_conns.lid AND 
        c_t.template=c.template AND l.network={} AND {}=ANY(c.network)
UNION
SELECT ep.id,ST_Z(ST_EndPoint(l.geom)) AS height,'energy_plant' AS feature,ep.submodel, b_t_conns.conn_type_id
    FROM "{}".energy_plants ep, "{}".lines l, "{}".energy_plant_connections ep_conns, energy_plant_templates ep_t, bundle_type_conns b_t_conns
    WHERE ep_conns.ep_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=ep_t.conn_bundle_type AND {}=ANY(ep.network) AND ep_conns.epid=ep.id AND l.id=ep_conns.lid AND 
        NOT ep.id={} AND l.network={} AND ep_t.template=ep.template
)
ORDER BY id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText(),dlg.network.currentText(),self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText(),epid,dlg.network.currentText())
                elif dlg.rbtn_customer.isChecked():
                    sql="""SELECT c.id,ST_Z(ST_EndPoint(l.geom)) AS height,'customer' AS feature,c.submodel, b_t_conns.conn_type_id
    FROM "{}".customers c, "{}".lines l, "{}".customer_connections c_conns, customer_templates c_t, bundle_type_conns b_t_conns
    WHERE c_conns.c_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=c_t.conn_bundle_type AND c_conns.cid=c.id AND l.id=c_conns.lid AND 
        c_t.template=c.template AND l.network={} AND {}=ANY(c.network) AND c.id IN ({});""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText(),dlg.network.currentText(),','.join([dlg.listWidget_ids.item(i).text() for i in range(dlg.listWidget_ids.count())]))
                elif dlg.rbtn_energy_plant.isChecked():
                    sql="""SELECT ep.id,ST_Z(ST_EndPoint(l.geom)) AS height,'energy_plant' AS feature,ep.submodel, b_t_conns.conn_type_id
    FROM "{}".energy_plants ep, "{}".lines l, "{}".energy_plant_connections ep_conns, energy_plant_templates ep_t, bundle_type_conns b_t_conns
    WHERE ep_conns.ep_seq=b_t_conns.sequence AND b_t_conns.conn_bundle_type_id=ep_t.conn_bundle_type AND {}=ANY(ep.network) AND ep_conns.epid=ep.id AND l.id=ep_conns.lid AND 
        NOT ep.id={} AND l.network={} AND ep_t.template=ep.template AND ep.id IN ({});""".format(self.dictDB['versionName'],self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText(),epid,dlg.network.currentText(),','.join([dlg.listWidget_ids.item(i).text() for i in range(dlg.listWidget_ids.count())]))
                #print(sql)
                self.cur.execute(sql)
                fids=[[str(f['id']), f['height'],f['feature'],f['submodel'],f['conn_type_id']] for f in self.cur.fetchall()]
                #print(fids)  
                
                #set up topology
                sql="""TRUNCATE temp.streets_help;
INSERT INTO temp.streets_help (geom,length_m) SELECT ST_Force2D(geom),ST_3Dlength(geom) FROM "{}".lines;
SELECT pgr_createTopology('temp.streets_help',0.0001,'geom','id',clean:='true');""".format(self.dictDB['versionName'])
                self.cur.execute(sql)
                
                sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".energy_plants ep WHERE ST_dWithin(ep.geom,st_v.the_geom,0.0001) AND ep.id={};""".format(self.dictDB['versionName'],epid[0])
                #print(sql)
                self.cur.execute(sql)
                v_epid=self.cur.fetchone()['vid']
                #print(v_epid)
                
                weak_point_id=0
                weak_point_value=0
                for fid in fids:
                    #print('*---------------------*')
                    #print(fid)
                    
                    file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\{}_{}\\{}_{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],fid[3],fid[2].capitalize(),fid[0],quantity,fid[4])
                    #print(file)
                    filedata_c=readFileToList(file)
                    if dlg.rbtn_maxValue.isChecked():
                        row,value=self.getMaxRow(filedata_ep,filedata_c,col_sup,col_ret,epid,fid,quantity)
                    elif dlg.rbtn_Date.isChecked():
                        date=dlg.date_input.text()
                        row,value=self.getDateRow(filedata_ep,filedata_c,col_sup,col_ret,epid,fid,quantity,date)
                    if value>weak_point_value:
                        weak_point_id=fid
                        weak_point_value=value
                        filedata_c_weakpoint=filedata_c
                    #print(row)
                    #print(value)

                #print(weak_point_value)    
                #print(weak_point_id)    
                sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".{}s f WHERE ST_dWithin(f.geom,st_v.the_geom,0.0001) AND f.id={};""".format(self.dictDB['versionName'],weak_point_id[2],weak_point_id[0])
                #print(sql)
                self.cur.execute(sql)
                v_id=self.cur.fetchone()['vid']
                #print(v_id)
                
                #get line with shortest path
                sql="""WITH sub As(
    SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
)
SELECT l.id,ST_3DLength(l.geom) AS length FROM sub,temp.streets_help st_h, "{}".lines l WHERE sub.edge=st_h.id AND st_h.geom=st_force2D(l.geom);""".format(v_epid,v_id,self.dictDB['versionName'])
                self.cur.execute(sql)
                lids=[[lid['id'],lid['length']] for lid in self.cur.fetchall()]
                #print(lids)
                
                #junction ids               
                jids=self.getJids(lids)
                #print(jids)
                
                variables=self.getJunctionVariables(jids,filedata_j)
                        
                data_ep=[float(filedata_ep[row].strip().split()[col_sup]),float(filedata_ep[row].strip().split()[col_ret])]
                data_c=[float(filedata_c_weakpoint[row].strip().split()[col_sup]),float(filedata_c_weakpoint[row].strip().split()[col_ret])]
                data_j=self.getDataJunction(filedata_j,row)
                dp=data_ep[0]-data_ep[1]
                dt=data_c[0]-data_c[1]
                
                path=[0]
                path_sum=0
                for lid in lids:
                    path_sum+=lid[1]
                    path.append(path_sum)
                #print(path)
                #print(data_ep)
                #print(data_c)
                #print(data_j)
                if dlg.rbtn_pathTemp.isChecked():
                    title='Simulationszeit='+str(round(data_j[0],3))+' h ; Kunden ID='+weak_point_id[0]+ ' ; Temperaturdifferenz Übergabestation: ' +str(round(dt,2))+' °C'
                    #title='Weakpoint; Time='+str(data_j[0])+'h ; '+weak_point_id[2].capitalize().replace('_',' ')+' ID='+weak_point_id[0]+'; Main energy plant ID='+epid[0]+'; Line Ids='+','.join([str(lid[0]) for lid in lids])
                elif dlg.rbtn_pathPressure.isChecked(): 
                    title='Netzschlechtpunkt; Simulationszeit='+str(round(data_j[0],3))+' h ; Kunden ID='+weak_point_id[0]+ ' ; Druckdifferenz: ' +str(dp)+' Pa'
                    #title='Simulationszeit='+str(data_j[0])+' h ; Kunden ID='+weak_point_id[0]+ ' ; Druckdifferenz: ' +str(dp)+' Pa'




                self.showplot(data_j,jids,epid,weak_point_id,path,data_ep,data_c,variables,quantity,title)

                #select lids in lines
                lines_layer=QgsProject.instance().mapLayersByName('lines')   
                if lines_layer:             
                    lines_layer[0].selectByExpression("id in {}".format(tuple([lid[0] for lid in lids])))

    def savePlots(self,dlg):
        """Just fo supply and return line. Todo update to all connection types"""
        #print('generate path diagram')
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)
        if dlg.rbtn_pathTemp.isChecked():
            quantity='temperature'
        elif dlg.rbtn_pathPressure.isChecked():
            quantity='pressure'            
        col_sup=3
        col_ret=2
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            
            file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],dlg.network.currentText(),'p_lines' if quantity=='pressure' else 'Temp_nodes')
            #print(file)
            filedata_j=readFileToList(file)
 
            if dlg.rbtn_customer.isChecked():
                #ep id
                epid,lid_start,submodel,conn_type=self.getMainEnergyPlantId(dlg.network.currentText())
                file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\energy_plant_{}\\{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],dlg.network.currentText(),epid[0],quantity)
                #print(file)
                filedata_ep=readFileToList(file)
                if dlg.rbtn_weakPoint.isChecked():
                    sql="""SELECT c.id,ST_Z(ST_EndPoint(l.geom)) AS height
    FROM "{}".customers c, "{}".lines l
    WHERE c.network=array[{}] AND St_dWithin(c.geom,l.geom,0.000001)
    ORDER BY c.id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText())
                elif dlg.rbtn_customer.isChecked():
                    sql="""SELECT c.id,ST_Z(ST_EndPoint(l.geom)) AS height
    FROM "{}".customers c, "{}".lines l
    WHERE c.network=array[{}] AND St_dWithin(c.geom,l.geom,0.000001) AND c.id IN ({})
    ORDER BY c.id;""".format(self.dictDB['versionName'],self.dictDB['versionName'],dlg.network.currentText(),','.join([dlg.listWidget_ids.item(i).text() for i in range(dlg.listWidget_ids.count())]))
                #print(sql)
                self.cur.execute(sql)
                cids=[[str(cid['id']), cid['height']] for cid in self.cur.fetchall()]
                #print(cids)  
                
                #set up topology
                sql="""TRUNCATE temp.streets_help;
INSERT INTO temp.streets_help (geom,length_m) SELECT ST_Force2D(geom),ST_3Dlength(geom) FROM "{}".lines;
SELECT pgr_createTopology('temp.streets_help',0.0001,'geom','id',clean:='true');""".format(self.dictDB['versionName'])
                self.cur.execute(sql)
                
                sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".energy_plants ep WHERE ST_dWithin(ep.geom,st_v.the_geom,0.0001) AND ep.id={};""".format(self.dictDB['versionName'],epid[0])
                #print(sql)
                self.cur.execute(sql)
                v_epid=self.cur.fetchone()['vid']
                #print(v_epid)
                
                weak_point_id=0
                weak_point_value=0
                for cid in cids:
                    #print('*---------------------*')
                    #print(cid)
                    
                    file=getQGISPluginsDir(self.plugin_dir)+'\\ida_districts_modeling_simulation\\network_models\\{}\\{}\\network_{}\\Customer_{}\\{}.prn'.format(self.dictDB['projectName'],self.dictDB['versionName'],dlg.network.currentText(),cid[0],quantity)
                    #print(file)
                    filedata_c=readFileToList(file)
                    if dlg.rbtn_maxValue.isChecked():
                        row,value=self.getMaxRow(filedata_ep,filedata_c,col_sup,col_ret,epid,cid,quantity)
                    elif dlg.rbtn_Date.isChecked():
                        date=dlg.date_input.text()
                        row,value=self.getDateRow(filedata_ep,filedata_c,col_sup,col_ret,epid,cid,quantity,date)
                    
                    weak_point_id=cid
                    weak_point_value=value
                    filedata_c_weakpoint=filedata_c
                    #print(row)
                    #print(value)
 
                
                    sql="""SELECT st_v.id::integer AS vid FROM temp.streets_help_vertices_pgr st_v,"{}".customers c WHERE ST_dWithin(c.geom,st_v.the_geom,0.0001) AND c.id={};""".format(self.dictDB['versionName'],weak_point_id[0])
                    #print(sql)
                    self.cur.execute(sql)
                    v_cid=self.cur.fetchone()['vid']
                        
                    #get line with shortest path
                    sql="""WITH sub As(
    SELECT seq, node, edge, cost
            FROM pgr_dijkstra(
                'SELECT sh.id, sh.source, sh.target, sh.length_m as cost FROM temp.streets_help sh',
                {}, 
                {},
                false
            )
    )
    SELECT l.id,ST_3DLength(l.geom) AS length FROM sub,temp.streets_help st_h, "{}".lines l WHERE sub.edge=st_h.id AND st_h.geom=st_force2D(l.geom);""".format(v_epid,v_cid,self.dictDB['versionName'])
                    self.cur.execute(sql)
                    lids=[[lid['id'],lid['length']] for lid in self.cur.fetchall()]
                    #print(lids)
                    
                    #junction ids               
                    jids=self.getJids(lids)
                    #print(jids)
                    
                    variables=self.getJunctionVariables(jids,filedata_j)
                    #print(variables)   
                            
                    data_ep=[float(filedata_ep[row].strip().split()[col_sup]),float(filedata_ep[row].strip().split()[col_ret])]
                    data_c=[float(filedata_c_weakpoint[row].strip().split()[col_sup]),float(filedata_c_weakpoint[row].strip().split()[col_ret])]
                    data_j=self.getDataJunction(filedata_j,row)
                    dp=data_ep[0]-data_ep[1]
                    dt=data_c[0]-data_c[1]
                    
                    path=[0]
                    path_sum=0
                    for lid in lids:
                        path_sum+=lid[1]
                        path.append(path_sum)
                    #print(path)
                    #print(data_ep)
                    #print(data_c)
                    #print(data_j)
                    #title='Weakpoint; Time='+str(data_j[0])+'h ; Customer ID='+weak_point_id[0]+'; Energy plant ID='+epid[0]+'; Line Ids='+','.join([str(lid[0]) for lid in lids])
                    #title='Netzschlechtpunkt; Simulationszeit='+str(data_j[0])+' h ; Kunden ID='+weak_point_id[0]+ ' ; Druckdifferenz: ' +str(dp)+' Pa'
                    #title='Simulationszeit='+str(data_j[0])+' h ; Kunden ID='+weak_point_id[0]+ ' ; Druckdifferenz: ' +str(dp)+' Pa'
                    title='Simulationszeit='+str(data_j[0])+' h ; Kunden ID='+weak_point_id[0]+ ' ; Temperaturdifferenz Übergabestation: ' +str(round(dt,2))+' °C'


                    self.showplot(data_j,jids,epid,weak_point_id,path,data_ep,data_c,variables,quantity,title)

                    #select lids in lines
                    lines_layer=QgsProject.instance().mapLayersByName('lines')   
                    if lines_layer:             
                        lines_layer[0].selectByExpression("id in {}".format(tuple([lid[0] for lid in lids])))

            
    def addSelectedIDs(self,dlg):
        """Adds all selected lines to list dlg.listWidget_ids"""
        #print('add selected lines')
        layer = self.iface.activeLayer()
        if layer:
            #print(layer.name())
            if layer.name()=='lines' and dlg.rbtn_lineIds.isChecked() or layer.name()=='customers' and dlg.rbtn_customer.isChecked():
                features = layer.selectedFeatures()
                #print(features)
                for f in features:
                    #print(f['id'])
                    item = QListWidgetItem(str(f['id']))
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                    dlg.listWidget_ids.addItem(item)

    def addID(self,dlg):
        """Add id to list dlg.listWidget_ids"""
        #print('add id')
        item = QListWidgetItem('')
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        dlg.listWidget_ids.addItem(item)
                    
                    
    def deleteIDs(self,dlg):
        listItems=dlg.listWidget_ids.selectedItems()
        if not listItems: return        
        for item in listItems:
            dlg.listWidget_ids.takeItem(dlg.listWidget_ids.row(item))
            
        
                    
    def showPathReports(self):
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)                       
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.dlg_pathReports=IDADistrictsPathReportsDialog()
            self.dlg_pathReports.btn_ok.clicked.connect(lambda: self.generatePathReport(self.dlg_pathReports))
            self.dlg_pathReports.btn_savePlots.clicked.connect(lambda: self.savePlots(self.dlg_pathReports))
            self.dlg_pathReports.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg_pathReports))
            self.dlg_pathReports.btn_addSelectedIDs.clicked.connect(lambda: self.addSelectedIDs(self.dlg_pathReports))
            self.dlg_pathReports.btn_deleteIDs.clicked.connect(lambda: self.deleteIDs(self.dlg_pathReports))
            self.dlg_pathReports.btn_addID.clicked.connect(lambda: self.addID(self.dlg_pathReports))
            self.cur.execute('SELECT network FROM "{}".lines GROUP BY network;'.format(self.dictDB['versionName']))
            self.dlg_pathReports.network.addItems([str(i['network']) for i in self.cur.fetchall()])
            self.dlg_pathReports.show()
    
    def getType(self,dlg):
        if dlg.rbtn_customer.isChecked():
            type='customer'
        elif dlg.rbtn_energy_plant.isChecked():
            type='energy_plant'
        return type
    
    def getFeatureIds(self,dlg):
        networks=[dlg.combo_networks.itemText(i) for i in range(dlg.combo_networks.count()) if dlg.combo_networks.itemChecked(i)]
        if networks:
            type=self.getType(dlg)
            sql="""SELECT id FROM "{}".{}s{} ORDER BY id;""".format(self.dictDB['versionName'],type,' WHERE network && ARRAY['+','.join(networks)+']')
            self.cur.execute(sql)
            return [str(i['id']) for i in self.cur.fetchall()]
        else:
            return []
    
    def loadFeatureIds(self,dlg):
        dlg.listWidget_ids.clear()
        ids=self.getFeatureIds(dlg)
        #print(ids)
        dlg.listWidget_ids.addItems(ids)
    
    #dublicated code see invoke.py
    def plotLoadProfiles(self,dlg):
        """Show feature load in network simulation"""  
        idxs=[index.row() for index in dlg.listWidget_ids.selectedIndexes()]
        #print(idxs)
        count=0
        if idxs:
            fig, ax = plt.subplots(layout='constrained')
            fig2, ax2 = plt.subplots(layout='constrained')
            
            for idx in idxs:
                id=dlg.listWidget_ids.item(idx).text()
                #print(id)
                file_path=getModellingDir(self.plugin_dir)+"\\network_models\\{}\\{}\\network_{}\\{}_{}\\Hx.prn".format(self.dictDB['projectName'],self.dictDB['versionName'],dlg.combo_networks.currentText(),self.getType(dlg).capitalize(),id)  
                #print(file_path)
                if os.path.exists(file_path):
                    legend='Customer_'+id

                    #print(file_path)
                    filedata=readFileToList(file_path)

                    #print(filedata)
                    i=0
                    time=[]
                    power=[]
                    energy=[]
                    for line in filedata:
                        if i>0:
                            data=line.strip().split()
                            power.append([float(data[0]),max(0,float(data[2]))/1000])
                            energy.append([float(data[0]),float(data[4])/1000])
                        i+=1    
                    
                    power=np.array(power)  
                    energy=np.array(energy)    
                    #print(power)

                    time=np.arange(0,8760,0.1)
                    #print(time)

                    #linear interpolation
                    valuesPowerInt = np.interp(time, power[:,0], power[:,1])
                    valuesEnergyInt = np.interp(time, power[:,0], energy[:,1])
                    
                    if count==0:
                        power_sum=valuesPowerInt
                        energy_sum=valuesEnergyInt
                    else:
                        power_sum=np.add(power_sum,valuesPowerInt)
                        energy_sum=np.add(energy_sum,valuesEnergyInt)

                    #plotting
                    ax.plot(time, valuesPowerInt,label='Customer ID='+str(id))
                    ax2.plot(time, valuesEnergyInt,label='Customer ID='+str(id))

                    count+=1
                    
            ax.set_title('Load profiles customers')
            ax2.set_title('Cumulated energy customers')
            ax.set_xlabel('Time, h')
            ax2.set_xlabel('Time, h')
            ax.set_ylabel('Power, kW')
            ax2.set_ylabel('Energy, MWh')
            ax.grid()
            ax2.grid()

            plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
            fig.legend()
            fig2.legend()
            fig.show()            
            fig2.show()            
            if count>1:
                fig1, ax1 = plt.subplots(layout='constrained')
                #ax1.plot(time, power_sum, label='Total power, kW')
                ax1.plot(time, power_sum, label='Heizlast aller Kunden, kW', linewidth=4.0)
                #ax1.plot(time, energy_sum, label='Total energy, kWh')
                ax1.plot(time, energy_sum, label='Kumulierte Heizenergie, MWh', linewidth=4.0)
                #ax1.set_xlabel('Time, h')
                ax1.set_xlabel('Zeit, h')
                #ax1.set_ylabel('Power, W')
                #ax1.set_title('Total load profiles and cumulated energy')
                plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016,8760])
                ax1.grid()
                plt.legend()
                
                SMALL_SIZE = 30
                MEDIUM_SIZE = 35
                BIGGER_SIZE = 40

                plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
                plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
                plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
                plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
                plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
                plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
                plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title
                fig1.show()
                
        else:
            self.iface.messageBar().pushMessage("Info", "No feature selected or not invoked!", level=Qgis.Info)
            
    def loadProfiles(self):
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)                       
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.dlg_plotLoads=PlotLoadProfilesDialog()
            self.dlg_plotLoads.btn_plot.clicked.connect(lambda: self.plotLoadProfiles(self.dlg_plotLoads))
            self.dlg_plotLoads.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg_plotLoads))
            self.dlg_plotLoads.rbtn_customer.toggled.connect(lambda: self.loadFeatureIds(self.dlg_plotLoads))
            self.dlg_plotLoads.rbtn_energy_plant.toggled.connect(lambda: self.loadFeatureIds(self.dlg_plotLoads))
            
            self.dlg_plotLoads.combo_networks.addItem('Check all items')
            networks=getNetworks(self.cur,self.dictDB)
            self.dlg_plotLoads.combo_networks.addItems([str(i) for i in networks])
            for i in range(len(networks)):
                self.dlg_plotLoads.combo_networks.setItemChecked(i+1,False)
            self.dlg_plotLoads.combo_networks.currentTextChanged.connect(lambda: self.loadFeatureIds(self.dlg_plotLoads))
            self.loadFeatureIds(self.dlg_plotLoads)
            self.dlg_plotLoads.show()

    def getOpenFilesAndDirs(self,parent=None, caption='', directory='', 
                            filter='', initialFilter='', options=None):
        def updateText():
            # update the contents of the line edit widget with the selected files
            selected = []
            for index in view.selectionModel().selectedRows():
                selected.append('"{}"'.format(index.data()))
            lineEdit.setText(' '.join(selected))

        dialog = QFileDialog(parent, windowTitle=caption)
        dialog.setFileMode(dialog.ExistingFiles)
        if options:
            dialog.setOptions(options)
        dialog.setOption(dialog.DontUseNativeDialog, True)
        if directory:
            dialog.setDirectory(directory)
        if filter:
            dialog.setNameFilter(filter)
            if initialFilter:
                dialog.selectNameFilter(initialFilter)

        # by default, if a directory is opened in file listing mode, 
        # QFileDialog.accept() shows the contents of that directory, but we 
        # need to be able to "open" directories as we can do with files, so we 
        # just override accept() with the default QDialog implementation which 
        # will just return exec_()
        dialog.accept = lambda: QDialog.accept(dialog)

        # there are many item views in a non-native dialog, but the ones displaying 
        # the actual contents are created inside a QStackedWidget; they are a 
        # QTreeView and a QListView, and the tree is only used when the 
        # viewMode is set to QFileDialog.Details, which is not this case
        stackedWidget = dialog.findChild(QStackedWidget)
        view = stackedWidget.findChild(QListView)
        view.selectionModel().selectionChanged.connect(updateText)

        lineEdit = dialog.findChild(QLineEdit)
        # clear the line edit contents whenever the current directory changes
        dialog.directoryEntered.connect(lambda: lineEdit.setText(''))

        dialog.exec_()
        return dialog.selectedFiles()

    def getSourceVars(self,source):
        if os.path.isfile(source):
            vars=readFileToList(source)[0].split()
            #print(vars)
        elif os.path.exists(source):
            #print(os.listdir(source))
            vars=readFileToList(source+'/'+os.listdir(source)[0])[0].split()
            #print(vars)
        return vars[1:]
        
    def dataSourceDialog(self,dlg):
        source = self.getOpenFilesAndDirs(
            dlg, "Import file/directory","", '*.prn')
        #print(source)
        if source:
            dlg.lineEditSourceName.setText(source[0])
            dlg.tableVars.setRowCount(0)
            vars=self.getSourceVars(source[0])
            dlg.checked_vars={i: False for i in vars}
            for counter,var in enumerate(vars):
                dlg.tableVars.insertRow(counter)
    
                chkBoxItem=QTableWidgetItem(var)
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)  

                dlg.tableVars.setItem(counter,0,chkBoxItem)
                comboBox = QComboBox()
                comboBox.addItems(['Customer','Energy plant','Line'])
                dlg.tableVars.setCellWidget(counter, 1, comboBox)
                dlg.tableVars.setItem(counter, 2, QTableWidgetItem(''))
                dlg.tableVars.setItem(counter, 3, QTableWidgetItem(''))
                dlg.tableVars.setItem(counter, 4, QTableWidgetItem(''))
    
    def importMeasurementData(self,dlg):
        #print([i for i in range(dlg.tableVars.rowCount())])
        #print([i for i in range(dlg.tableVars.rowCount()) if dlg.tableVars.item(i,0).checkState() == Qt.Checked])
        var_dict=[{'var':dlg.tableVars.item(i,0).text(),
                    'colmn':i+2,
                    'feature':dlg.tableVars.cellWidget(i,1).currentText().replace(' ','_').lower(),
                    'alias':(dlg.tableVars.item(i,2).text() if dlg.tableVars.item(i,2).text() else dlg.tableVars.item(i,0).text()),
                    'min': float(dlg.tableVars.item(i,3).text()) if dlg.tableVars.item(i,3).text().isnumeric() else False,
                    'max': float(dlg.tableVars.item(i,4).text()) if dlg.tableVars.item(i,4).text().isnumeric() else False} 
                    for i in range(dlg.tableVars.rowCount()) if dlg.tableVars.item(i,0).checkState() == Qt.Checked]
        #print(var_dict)
        
        srid=loadProjectConfig(self.plugin_dir,self.dictDB['projectName'])['srid']
        source=dlg.lineEditSourceName.text()
        if os.path.isfile(source):
            files=[source]
        elif os.path.exists(source):
            files=[source+'/'+i for i in os.listdir(source)]
        
        for counter,file in enumerate(files):
            filedata=readFileToList(file)
            #print(filedata)
                
            for var in var_dict:
                #print(var)
                id=file.split('/')[-1].split('.')[0]
                #print(id)
                table_name=var['feature']+'_m_'+var['alias']
                #print(table_name)
                #print(checkTableNameExists(self.cur,self.dictDB,table_name))
                if not checkTableNameExists(self.cur,self.dictDB,table_name):
                    sql="""CREATE TABLE IF NOT EXISTS "{}".{}
(
    id serial,
    fid INTEGER,
    time timestamp,
    geom geometry({},{}),
    {} numeric,
    CONSTRAINT {}_pkey PRIMARY KEY (id));""".format(self.dictDB['versionName'],table_name,'LineStringZ' if var['feature']=='Line' else 'PointZ', srid,var['alias'],table_name)
                    #print(sql)
                    self.cur.execute(sql)
                elif dlg.delete_existing_data.checkState() == Qt.Checked and counter==0:
                    sql="""TRUNCATE "{}".{};""".format(self.dictDB['versionName'],table_name)
                    self.cur.execute(sql)
                elif dlg.delete_existingID_data.checkState() == Qt.Checked:
                    sql="""DELETE FROM "{}".{} WHERE fid={};""".format(self.dictDB['versionName'],table_name,id)
                    self.cur.execute(sql)
                    
            vars_data={var['colmn']:[] for var in var_dict}
            #print(vars_data)
            for i,line in enumerate(filedata):
                if i>0:
                    data=line.strip().split()
                    for colmn,max_value,min_value in [[i['colmn'],i['max'],i['min']] for i in var_dict]:
                        if dlg.checkbox_timestep.checkState() == Qt.Checked:
                            time_split=data[0].split('-')+data[1].split(':')
                            time={'year':int(time_split[0]),'month':int(time_split[1]),'day':int(time_split[2]),'hour':int(time_split[3]),'minute':int(time_split[4]),'second':int(time_split[5])}
                            ntp=getNTPTime(time['year'],time['month'],time['day'],time['hour'],time['minute'],time['second'])
                        vars_data[colmn].append([ntp if dlg.checkbox_timestep.checkState() == Qt.Checked else data[0]+' '+data[1],min(max(float(data[colmn]),min_value),max_value) if max_value and min_value else ((min(float(data[colmn]),max_value) if max_value else max(float(data[colmn]),min_value)) if max_value or min_value else float(data[colmn]))])
                        

            vars_data_np={i:np.array(vars_data[i]) for i in vars_data} 
            #print(vars_data_np)
            start_time_m=vars_data_np[[i for i in vars_data_np][0]][0][0]
            end_time_m=vars_data_np[[i for i in vars_data_np][0]][-1][0]


            if dlg.checkbox_timestep.checkState() == Qt.Checked:
                #linear interpolation
                time=[]
                #print(dlg.interpolation_dt.text())
                if is_number(dlg.interpolation_dt.text()):
                    dt=float(dlg.interpolation_dt.text())

                    if vars_data_np:
                        start_time=start_time_m-start_time_m%dt
                        #print(start_time)
                        end_time=end_time_m-end_time_m%dt+dt
                        #print(end_time)
                    else:
                        self.iface.messageBar().pushMessage("Info", "Please select a variable!", level=Qgis.Info)
                        return
                    time=np.arange(start_time,end_time,dt)
                    
                else:
                    self.iface.messageBar().pushMessage("Info", "Please enter a numerical interpolation time!", level=Qgis.Info)
                    return
            
            for var,var_data in zip(var_dict,vars_data_np):
                table_name=var['feature']+'_m_'+var['alias']
                if dlg.checkbox_timestep.checkState() == Qt.Checked:
                    var_data = np.interp(time, vars_data_np[var_data][:,0], vars_data_np[var_data][:,1])
                else:
                    time=vars_data_np[var_data][:,0]
                    var_data=vars_data_np[var_data][:,1]
                #print(var_data)
                sql='SELECT geom FROM "{}".{}s WHERE id={};'.format(self.dictDB['versionName'],var['feature'],id)
                self.cur.execute(sql)
                fid_geom=self.cur.fetchone()
                if fid_geom:
                    fid_geom=fid_geom['geom']
                else:
                    fid_geom=None
                
                self.copy_string_iterator_mData(self.conn,var_data,getMaxIdSchema(self.cur,table_name,self.dictDB['versionName'])+1,id,time,fid_geom,table_name,dlg)       
        #closeDialog(dlg)
        
        
    def copy_string_iterator_mData(self,connection, mdata, id_max,fid,time,geom,table_name,dlg) -> None:
        with connection.cursor() as cursor:
            mdata_string_iterator = StringIteratorIO((
                '|'.join(map(clean_csv_value, (
                    id,
                    fid,
                    getTimeFromNTP(data[0]) if dlg.checkbox_timestep.checkState() == Qt.Checked else data[0],
                    geom,
                    data[1]
                ))) + '\n'
                for id,data in enumerate(zip(time,mdata),id_max)
            ))
            cursor.copy_expert("""COPY "{}".{} FROM STDIN WITH (FORMAT csv, DELIMITER '|')""".format(self.dictDB['versionName'],table_name),mdata_string_iterator)
        
    
    def showImportMeasurements(self):
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)                       
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.dlg_importMeasurements=ImportMeasuremntsDialog()
            
            self.dlg_importMeasurements.btn_source.clicked.connect(lambda: self.dataSourceDialog(self.dlg_importMeasurements))
            self.dlg_importMeasurements.btn_import.clicked.connect(lambda: self.importMeasurementData(self.dlg_importMeasurements))
            self.dlg_importMeasurements.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg_importMeasurements))
            self.dlg_importMeasurements.show()
        
    def btn_showDataOnMap(self):
        self.dictDB=getDBConnectionData(self.plugin_dir)
        self.conn=dbConnect(self.dictDB,False)                       
        if self.conn:
            self.cur=self.conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
            self.dlg_showOnMap=ShowOnMapDialog(self.cur,self.dictDB,self.plugin_dir)
            self.dlg_showOnMap.btn_showOnMap.clicked.connect(lambda: self.showOnMap(self.dlg_showOnMap))
            self.dlg_showOnMap.btn_cancel.clicked.connect(lambda: closeDialog(self.dlg_showOnMap))
            self.dlg_showOnMap.featureGroupChanged(False)
            self.dlg_showOnMap.show()
            
    def showOnMap(self,dlg):
        fd_meterPerNode=float(loadModellingSettings(self.plugin_dir,self.dictDB)['fd_meterPerNode'])
        if int(dlg.lineSegVis.text())==0:
            iface.messageBar().pushMessage("Info", f"The line segment length for visualization should be greater than 0.", level=Qgis.Info)
            return False
        self.worker_showOnMap = WorkerShowOnMap(dictDB=self.dictDB,plugin_dir=self.plugin_dir,dlg=dlg,vars=None,feature=dlg.feature,layer_name=dlg.layer_name.text(),colorramp=dlg.colorramp.currentText(),
            color_classes=int(dlg.color_classes.text()),size_symbolMin=dlg.size_symbolMin.text(),size_symbolMax=dlg.size_symbolMax.text(),lineSegVis=int(dlg.lineSegVis.text()),
            rotation_symbolMin=dlg.rotation_symbolMin.text(),rotation_symbolMax=dlg.rotation_symbolMax.text(),simData=dlg.rbtn_simData.isChecked(),enable=True)
                
        self.threadpool_showOnMap = QThreadPool()
        self.worker_showOnMap.signals.error.connect(show_error_message)
        self.worker_showOnMap.signals.progress.connect(dlg.update_progress)  
        self.threadpool_showOnMap.start(self.worker_showOnMap) 

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = IDADistrictsResultVisualizationDialog()
            self.dlg.btn_path_reports.clicked.connect(self.showPathReports)
            self.dlg.btn_plotLoadProfiles.clicked.connect(self.loadProfiles)
            self.dlg.btn_importMeasurements.clicked.connect(self.showImportMeasurements)
            self.dlg.btn_showDataOnMap.clicked.connect(self.btn_showDataOnMap)
            # show the dialog
            self.dlg.show()
        else:
            self.dlg.show()
            self.dlg.activateWindow()
            #print('activate')

