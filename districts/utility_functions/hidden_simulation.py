"""IDA Districts started without its window for a simulation (option -W hidden of the batch call)."""
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QCheckBox

from .translations import tr_msg

# one setting for all dialogs that simulate: the choice of the last dialog is the start of the next one
SETTING = 'Districts/hideSimulation'


def windowOptions(hidden: bool) -> list[str]:
    return ['-W', 'hidden'] if hidden else []


def hideSimulationDefault():
    try:
        return QSettings().value(SETTING, True, type=bool)
    except Exception:
        return True


def hideSimulationCheckBox():
    check = QCheckBox(tr_msg('Hide the simulation run'))
    check.setToolTip(tr_msg('IDA Districts runs the simulation without its window (-W hidden).'))
    check.setChecked(hideSimulationDefault())
    # clicked, not toggled: a run that sets the box from its parameters does not change the setting
    check.clicked.connect(lambda checked: QSettings().setValue(SETTING, bool(checked)))
    return check
