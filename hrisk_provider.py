from qgis.core import QgsProcessingProvider
from .rtn_calc_alg import rtn_calc_alg


class hrisk_provider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(rtn_calc_alg())

    def id(self):
        return 'H-RISK'

    def name(self):
        return self.tr('H-RISK')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()
