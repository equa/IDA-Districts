import os
from qgis.utils import iface
from qgis.PyQt.QtCore import QObject,pyqtSignal
from qgis.PyQt.QtWidgets import QDialog,QTreeView,QPushButton,QRadioButton, QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar,QFileDialog,QGroupBox
from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt

from .utility_functions.translations import *
from .utility_functions.dialog import *
from .utility_functions.utility import *
from .utility_functions.files import *


class IDA_Districts_NameDialog(QDialog):
    def __init__(self,title,label_text,old_input,old_description):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(title)     
        
        #label
        #print(label_text)
        layout_label = QVBoxLayout() 
        label =QLabel(label_text)
        layout_label.addWidget(label)
        
        label_description =QLabel(tr('@default','description'))
        layout_label.addWidget(label_description)
        
        #input 
        layout_input = QVBoxLayout()         
        self.input =QLineEdit(old_input)
        layout_input.addWidget(self.input)
        
        self.input_description =QLineEdit(old_description)
        layout_input.addWidget(self.input_description)
        
        #set name settings together
        layout_name = QHBoxLayout() 
        layout_name.addLayout(layout_label)
        layout_name.addLayout(layout_input)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_name)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)
        
class ExportProjectDialog(QDialog):
    def __init__(self):
        """Constructor ExportProjectDialog"""
        super().__init__()
        self.setWindowTitle(tr('@default',"export_project_settings"))    
        
        #comboboxes
        layout_settings = QVBoxLayout()
        self.exportInvokedFeatures =QCheckBox(tr('@default',"invoked_features"))
        self.exportPrn =QCheckBox(tr('@default',"prn_results")) 
        self.exportDBResults =QCheckBox(tr('@default',"db_results")) 
        layout_settings.addWidget(self.exportInvokedFeatures)
        layout_settings.addWidget(self.exportPrn)
        layout_settings.addWidget(self.exportDBResults)
        
        #choose dir
        layout_file= QHBoxLayout()
        
        #label
        layout_label= QVBoxLayout()
        self.project_dir=QLabel(tr('@default',"select_directory"))
        self.project_name=QLabel(tr('@default',"project_name"))
        
        layout_label.addWidget(self.project_dir)
        layout_label.addWidget(self.project_name)

        #values
        layout_values= QVBoxLayout()
        layout_dir= QHBoxLayout()
        self.dirname=QLineEdit('')
        self.btn_selectDir=QPushButton("...")
        self.btn_selectDir.clicked.connect(self.dirDlg)
        
        layout_dir.addWidget(self.dirname)
        layout_dir.addWidget(self.btn_selectDir)
        layout_values.addLayout(layout_dir)
        #file name
        self.project_name_input=QLineEdit("")
        
        layout_values.addWidget(self.project_name_input)
        
        layout_file.addLayout(layout_label)
        layout_file.addLayout(layout_values)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"export"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #progress bar
        self.progress=QProgressBar()
        
        #set layout together       
        layout_export = QVBoxLayout()
        layout_export.addLayout(layout_settings)
        layout_export.addLayout(layout_file)
        layout_export.addLayout(layout_buttons)
        layout_export.addWidget(self.progress)
        
        self.setLayout(layout_export)    
        
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        
    def dirDlg(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('@default',"select_directory"),
            ''
        )
        self.dirname.setText(standardizePath(folder))
      
class ProjectConfigDialog(QDialog):
    def __init__(self):
        """Constructor Project Configurations"""
        super().__init__()
        self.setWindowTitle(tr('@default',"project_configuration_settings"))    
        
        #labels
        layout_labels = QVBoxLayout()
        label_srid =QLabel(tr('@default',"coordinate_system_srid"))
        layout_labels.addWidget(label_srid)   
        
        #values
        layout_values = QVBoxLayout()
        self.srid =QLineEdit("")
        layout_values.addWidget(self.srid)  
        
        layout_field_input = QHBoxLayout()
        layout_field_input.addLayout(layout_labels)
        layout_field_input.addLayout(layout_values)   
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #set layout together       
        layout_project = QVBoxLayout()
        layout_project.addLayout(layout_field_input)
        layout_project.addLayout(layout_buttons)
        
        self.setLayout(layout_project)
        
class ApproveDialog(QDialog):
    def __init__(self,title,label_text):
        super().__init__()
        self.setWindowTitle(title)
        
        #label
        label =QLabel(label_text)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"ok"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(label)
        layout_win.addLayout(layout_buttons)
        
        self.setLayout(layout_win)

class NewProjectDlg(QDialog):
    def __init__(self,dlg_main,config):
        """Constructor NewProjectDlg"""
        super().__init__()
        self.setWindowTitle(tr('@default',"new_districts_project"))  
        self.dlg_main=dlg_main
        self.config=config
        self.process_running=False


        #project name 
        layout_project= QHBoxLayout() 

        label_project_name =QLabel(tr('@default',"project_name"))
        layout_project.addWidget(label_project_name)
        
        self.project_name=QLineEdit()
        layout_project.addWidget(self.project_name)
      
        #template 
        self.selectTemplate =QComboBox()
        templates_plugin_dir = os.path.join(get_districts_plugin_dir(), 'templates')
        templates_plugin =[folder for folder in os.listdir(templates_plugin_dir) if os.path.isdir(os.path.join(templates_plugin_dir, folder))]
        templates_ida_dir = os.path.join(self.config['pathDistricts'], 'Samples')
        templates_ida =[folder for folder in os.listdir(templates_ida_dir) if os.path.isdir(os.path.join(templates_ida_dir, folder))]

        items = {
            folder: tr("@default", folder)
            for folder in templates_plugin + templates_ida
}
        
        # Add items to the combobox, storing the original key as user data
        for original_key, translated_text in items.items():
            self.selectTemplate.addItem(translated_text, original_key) # The second argument is the userData

        index = self.selectTemplate.findData('heating_network')
        if index != -1:
            self.selectTemplate.setCurrentIndex(index)
        self.selectTemplate.currentTextChanged.connect(self.update_checkbox_dbDefaultValues)

        #Qheckboxes
        layout_settings = QVBoxLayout()
        self.checkbox_db_defaultValues =QCheckBox("DB default values")
        self.checkbox_db_defaultValues.setDisabled(True) 
        self.checkbox_invokedFeatures =QCheckBox("Invoked features") 
        self.checkbox_prn =QCheckBox(".prn results") 
        self.checkbox_DBResults =QCheckBox("Database results") 
        layout_settings.addWidget(self.checkbox_db_defaultValues)
        layout_settings.addWidget(self.checkbox_invokedFeatures)
        layout_settings.addWidget(self.checkbox_prn)
        layout_settings.addWidget(self.checkbox_DBResults)
        layout_settings.setContentsMargins(30, 0, 0, 0)
        
        self.group_box_autsave = QGroupBox("")
        self.group_box_autsave.setLayout(layout_settings)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton(tr('@default',"create"))
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton(tr('@default',"cancel"))
        layout_buttons.addWidget(self.btn_cancel)
        
        self.progress=QProgressBar()

        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_project)
        layout_win.addWidget(self.selectTemplate)
        #layout_win.addWidget(self.group_box_autsave)
        layout_win.addLayout(layout_buttons)
        layout_win.addWidget(self.progress)
        
        self.setLayout(layout_win)
        #self.update_checkbox_dbDefaultValues() 
        
    def update_checkbox_dbDefaultValues(self,text):
        current_data=self.selectTemplate.currentData()
        if current_data in ['db_default_values','empty_project']:
            self.checkbox_db_defaultValues.setCheckState(checkState())
            self.checkbox_invokedFeatures.setCheckState(uncheckState())
            self.checkbox_prn.setCheckState(uncheckState())
            self.checkbox_DBResults.setCheckState(uncheckState())
            self.checkbox_invokedFeatures.setDisabled(True) 
            self.checkbox_prn.setDisabled(True) 
            self.checkbox_DBResults.setDisabled(True) 
        else:
            self.checkbox_db_defaultValues.setCheckState(uncheckState())
            self.checkbox_invokedFeatures.setEnabled(True) 
            self.checkbox_prn.setEnabled(True) 
            self.checkbox_DBResults.setEnabled(True) 
            
    def update_progress(self,progress):
        self.progress.setValue(progress)
        
    def show_error_message(self, message):
        # Show the error message in a messageBar
        iface.messageBar().pushMessage("Error", message, level=Qgis.Critical)
        









