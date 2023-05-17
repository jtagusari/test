from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink
  )


from .algabstract import algabstract
import os

class receiverregulargrid(algabstract):
  PARAMETERS = { 
    "FENCE": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverregulargrid","Fence layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "fenceGeomPath",
      "save_layer_get_path": True
    },
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverregulargrid","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },    
    "SOURCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverregulargrid","Source layer"),
        "types": [QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine,QgsProcessing.TypeVectorPolygon],
        "optional": True,
      },
      "n_mdl": "sourceGeomPath",
      "save_layer_get_path": True
    },    
    
    "DELTA": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverregulargrid","Distance between receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 10.0, "maxValue": 100.0
      },
      "n_mdl": "delta"
    },
    "HEIGHT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverregulargrid","Height of receivers (m)"),
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
    self.initNoiseModellingPath("receiverregulargrid.groovy")
    self.addNoiseModellingPath(
      {"RECEIVER_PATH": os.path.join(self.NOISEMODELLING["TEMP_DIR"], "RECEIVERS.geojson")}
      )
    self.initNoiseModellingArg(parameters, context, feedback)
        
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)
    
    # import the result    
    dest_id_rcv = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT", self.NOISEMODELLING["RECEIVER_PATH"])
    
    return {"OUTPUT": dest_id_rcv}
          

  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}


  def displayName(self):
    return self.tr("Regular grid")

  def group(self):
    return self.tr('Set receivers')

  def groupId(self):
    return 'receiver'

  def createInstance(self):
    return receiverregulargrid()
