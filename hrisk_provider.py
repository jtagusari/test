from qgis.core import QgsProcessingProvider
from .noisefromtraffic import noisefromtraffic
from .fetchjageom import fetchjageom
from .receiverfacade import receiverfacade
from .receiverregulargrid import receiverregulargrid
from .receiverdelaunaygrid import receiverdelaunaygrid
from .isosurface import isosurface


class hrisk_provider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(fetchjageom())
        self.addAlgorithm(noisefromtraffic())
        self.addAlgorithm(receiverfacade())
        self.addAlgorithm(receiverregulargrid())
        self.addAlgorithm(receiverdelaunaygrid())
        self.addAlgorithm(isosurface())

    def id(self):
        return 'hrisk'

    def name(self):
        return self.tr('H-RISK')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()
