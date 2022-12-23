from qgis.PyQt.QtCore import QCoreApplication, QTranslator, QSettings
from qgis.core import QgsApplication

import os

from .hrisk_provider import hrisk_provider


class hrisk_plugin(object):
    def __init__(self, iface):
        self.iface = iface
        self.searchDialog = None

        # Initialize the plugin path directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        try:
            locale = QSettings().value("locale/userLocale", "en", type=str)[0:2]
        except Exception:
            locale = "en"
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'hrisk_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
            
    def initGui(self):
        self.provider = hrisk_provider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
