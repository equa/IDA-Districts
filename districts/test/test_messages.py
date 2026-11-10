"""Messages for the user (state messages, info, warnings, errors) are translated with tr_msg (utility_functions/translations.py):
the english text is the source, the german text is in the context 'Messages' of i18n/districts_de.ts."""
import ast
import os
import re
import xml.etree.ElementTree as ET

from qgis.PyQt.QtCore import QCoreApplication, QTranslator

from districts.utility_functions.translations import tr_msg

PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'test', 'simulation_tests', 'test_functions', '__pycache__', '.git'}


def message_literals():
    """{text: file} of the literal texts passed to tr_msg in the plugin sources"""
    literals = {}
    for folder, dirs, files in os.walk(PLUGIN_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if not name.endswith('.py'):
                continue
            with open(os.path.join(folder, name), encoding='utf-8-sig') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'tr_msg' and node.args
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                    literals.setdefault(node.args[0].value, name)
    return literals


def german_messages():
    root = ET.parse(os.path.join(PLUGIN_DIR, 'i18n', 'districts_de.ts')).getroot()
    context = [c for c in root.iter('context') if c.findtext('name') == 'Messages'][0]
    return {m.findtext('source'): m.findtext('translation') or '' for m in context.iter('message')}


def placeholders(text):
    return sorted(re.findall(r'\{[^}]*\}', text))


def test_every_message_has_a_german_translation():
    literals = message_literals()
    german = german_messages()
    assert len(literals) > 200
    missing = sorted('{} ({})'.format(repr(text), name) for text, name in literals.items() if not german.get(text))
    assert not missing, 'tr_msg texts without german translation in i18n/districts_de.ts (context Messages):\n' + '\n'.join(missing)


def test_placeholders_of_the_translations_match():
    wrong = sorted(repr(source) for source, translation in german_messages().items() if placeholders(source) != placeholders(translation))
    assert not wrong, 'placeholders of source and translation differ:\n' + '\n'.join(wrong)


def test_tr_msg_with_the_german_qm():
    translator = QTranslator()
    assert translator.load(os.path.join(PLUGIN_DIR, 'i18n', 'districts_de.qm'))
    QCoreApplication.installTranslator(translator)
    try:
        assert tr_msg('Simulation finished') == 'Simulation abgeschlossen'
        assert tr_msg('Error') == 'Fehler'
        assert tr_msg('Version {} does already exist!').format('v1') == 'Die Version v1 existiert bereits!'
        # texts of variables (e.g. the finished message of a worker) and unknown texts stay as they are
        assert tr_msg('a text without translation') == 'a text without translation'
    finally:
        QCoreApplication.removeTranslator(translator)
