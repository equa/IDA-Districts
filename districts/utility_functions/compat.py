from qgis.PyQt import QtCore, QtGui, QtWidgets

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