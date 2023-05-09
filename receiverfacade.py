from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink
  )


from .receiverabstract import receiverabstract

class receiverfacade(receiverabstract):
  PARAMETERS = { 
    "BUILDING": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverfacade","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },    
    "SOURCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverfacade","Source layer"),
        "types": [QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine,QgsProcessing.TypeVectorPolygon],
        "optional": True,
      },
      "n_mdl": "sourceGeomPath",
      "save_layer_get_path": True
    },    
    "FENCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverfacade","Fence layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True,
      },
      "n_mdl": "fenceGeomPath",
      "save_layer_get_path": True
    },
    
    "DELTA": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverfacade","Distance between receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 10.0, "maxValue": 100.0
      },
      "n_mdl": "delta"
    },
    "HEIGHT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverfacade","Height of receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 4.0, "maxValue": 100.0
      },
      "n_mdl": "height"
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverfacade","Receivers at facade" )
      }     
    }
  }
  
  def initAlgorithm(self, config):
    self.initParameters()

  def processAlgorithm(self, parameters, context, feedback):    
    self.initNoiseModelling("receiverfacade.groovy")
    self.initWpsArgs(parameters, context, feedback)
    
    feedback.pushCommandInfo(self.NOISEMODELLING["CMD"])   
    
    # execute groovy script using wps_scripts
    self.execNoiseModelling(parameters, context, feedback)
    
    # import the result    
    dest_id_rcv = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT",self.NOISEMODELLING["RECEIVER_PATH"])
    
    return {"OUTPUT": dest_id_rcv}

  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("At building facade")

  def group(self):
    return self.tr('Set receivers')

  def groupId(self):
    return 'receiver'

  def createInstance(self):
    return receiverfacade()
