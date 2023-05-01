from qgis.core import QgsProcessingProvider

from .noisefromtraffic import noisefromtraffic
from .noisefromemission import noisefromemission
from .emissionfromroadtraffic import emissionfromroadtraffic
from .initroad import initroad
from .initbuilding import initbuilding
from .fetchjageom import fetchjageom
from .fetchjaroad import fetchjaroad
from .fetchosmroad import fetchosmroad
from .fetchosmbuilding import fetchosmbuilding
from .fetchjabuilding import fetchjabuilding
from .fetchsrtmdem import fetchsrtmdem
from .fetchjadem import fetchjadem
from .fetchjapop import fetchjapop
from .receiverfacade import receiverfacade
from .receiverregulargrid import receiverregulargrid
from .receiverdelaunaygrid import receiverdelaunaygrid
from .isosurface import isosurface
from .estimatelevelofbuilding import estimatelevelofbuilding
from .estimatepopulationofbuilding import estimatepopulationofbuilding
from .estimateriskofbuilding import estimateriskofbuilding


class hrisk_provider(QgsProcessingProvider):

    def __init__(self):
        QgsProcessingProvider.__init__(self)

    def unload(self):
        pass

    def loadAlgorithms(self):
        self.addAlgorithm(fetchjageom())
        self.addAlgorithm(fetchjaroad())
        self.addAlgorithm(fetchjabuilding())
        self.addAlgorithm(fetchjadem())
        self.addAlgorithm(fetchjapop())
        self.addAlgorithm(fetchosmroad())
        self.addAlgorithm(fetchosmbuilding())
        self.addAlgorithm(fetchsrtmdem())
        self.addAlgorithm(noisefromtraffic())
        self.addAlgorithm(noisefromemission())
        self.addAlgorithm(initroad())
        self.addAlgorithm(initbuilding())
        self.addAlgorithm(emissionfromroadtraffic())
        self.addAlgorithm(receiverfacade())
        self.addAlgorithm(receiverregulargrid())
        self.addAlgorithm(receiverdelaunaygrid())
        self.addAlgorithm(isosurface())
        self.addAlgorithm(estimatelevelofbuilding())
        self.addAlgorithm(estimatepopulationofbuilding())
        self.addAlgorithm(estimateriskofbuilding())

    def id(self):
        return 'hrisk'

    def name(self):
        return self.tr('H-RISK')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()
