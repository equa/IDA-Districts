from qgis.PyQt import QtCore, QtGui, QtWidgets
from qgis.core import Qgis
from qgis.PyQt.QtCore import Qt
from qgis._3d import QgsPolygon3DSymbol

QT6 = QtCore.QT_VERSION >= 0x060000

if QT6:
    from qgis.PyQt.QtGui import QAction
else:
    from qgis.PyQt.QtWidgets import QAction
    
if QT6:
    from qgis.PyQt import sip
else:
    import sip
    
def get_event_pos(event):
    try:
        return event.position().toPoint()  # Qt6
    except AttributeError:
        return event.pos()  # Qt5
        
if QT6:
    MessageInfo = Qgis.MessageLevel.Info
    MessageWarning = Qgis.MessageLevel.Warning
    MessageCritical = Qgis.MessageLevel.Critical
    MessageSuccess = Qgis.MessageLevel.Success
else:
    MessageInfo = Qgis.Info
    MessageWarning = Qgis.Warning
    MessageCritical = MessageCritical
    MessageSuccess = Qgis.Success
    
if QT6:
    ItemIsSelectable = Qt.ItemFlag.ItemIsSelectable
    ItemIsEnabled = Qt.ItemFlag.ItemIsEnabled
    ItemIsEditable = Qt.ItemFlag.ItemIsEditable
    ItemIsUserCheckable = Qt.ItemFlag.ItemIsUserCheckable
else:
    ItemIsSelectable = Qt.ItemIsSelectable
    ItemIsEnabled = Qt.ItemIsEnabled
    ItemIsEditable = Qt.ItemIsEditable
    ItemIsUserCheckable = Qt.ItemIsUserCheckable
    
if QT6:
    ApplicationShortcut = Qt.ShortcutContext.ApplicationShortcut
else:
    ApplicationShortcut = Qt.ApplicationShortcut
    
if QT6:
    PolygonPropertyHeight = QgsPolygon3DSymbol.Property.PropertyHeight
    PolygonPropertyExtrusionHeight = (QgsPolygon3DSymbol.Property.PropertyExtrusionHeight)
else:
    PolygonPropertyHeight = QgsPolygon3DSymbol.PropertyHeight
    PolygonPropertyExtrusionHeight = (QgsPolygon3DSymbol.PropertyExtrusionHeight)