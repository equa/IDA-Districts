# coding=utf-8
"""Descriptions of the dialogs show data on map, load results and network report: translated in english and german."""
import os

import pytest
from qgis.PyQt.QtCore import QCoreApplication, QTranslator

from .. import ida_rv_dialog
from ..ida_rv_dialog import LoadResultsDialog, NetworkReportDialog, ShowOnMapDialog

I18N = os.path.join(os.path.dirname(__file__), os.pardir, 'i18n')


@pytest.fixture(params=[('en', 'Show data on map', 'Load results', 'Network report'),
                        ('de', 'Daten auf Karte anzeigen', 'Ergebnisse laden', 'Netzbericht')], ids=['en', 'de'])
def titles(request):
    translator = QTranslator()
    assert translator.load(os.path.join(I18N, 'districts_{}.qm'.format(request.param[0])))
    QCoreApplication.installTranslator(translator)
    yield request.param[1:]
    QCoreApplication.removeTranslator(translator)


def test_descriptions(titles, monkeypatch):
    monkeypatch.setattr(ida_rv_dialog, 'loadModellingSettings', lambda plugin_dir, config: {'fd_meterPerNode': 10})
    show_on_map = ShowOnMapDialog(None, {}, '', None)
    load_results = LoadResultsDialog(None)
    report = NetworkReportDialog('')
    for text_info, title in zip((show_on_map.text_info, load_results.text_info, report.text_info), titles):
        text = text_info.toPlainText()
        assert text.startswith(title) and '_info' not in text
        assert text_info.isReadOnly()
    # the report's widgets sit in a dialog layout below the description
    assert report.layout().indexOf(report.verticalLayoutWidget) == 0
    assert report.verticalLayout.indexOf(report.text_info) == 0
