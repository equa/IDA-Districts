from qgis.PyQt.QtCore import QObject,pyqtSignal
from qgis.PyQt.QtWidgets import QTreeView,QAction,QMainWindow,QWidget,QPushButton,QHBoxLayout,QVBoxLayout,QLabel,QLineEdit,QCheckBox,QComboBox, QProgressBar

#duplicate code
class IDA_Districts_NameDialog(QMainWindow):
    def __init__(self,title,label_text,old_input,old_description):
        """Constructor."""
        super().__init__()
        self.setWindowTitle(title)     
        
        #label
        layout_label = QVBoxLayout() 
        label =QLabel(label_text)
        layout_label.addWidget(label)
        
        label_description =QLabel('You can add a description:')
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
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addLayout(layout_name)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)
        
class ApproveDialog(QMainWindow):
    def __init__(self,title,label_text):
        super().__init__()
        self.setWindowTitle(title)
        
        #label
        label =QLabel(label_text)
        
        #buttons     
        layout_buttons = QHBoxLayout()
        self.btn_ok=QPushButton("Ok")
        layout_buttons.addWidget(self.btn_ok)
        self.btn_cancel=QPushButton("Cancel")
        layout_buttons.addWidget(self.btn_cancel)
        
        #---------------set layouts together-------------------
        layout_win = QVBoxLayout()
        layout_win.addWidget(label)
        layout_win.addLayout(layout_buttons)
        
        widget=QWidget()
        widget.setLayout(layout_win)
        self.setCentralWidget(widget)