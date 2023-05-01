from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterEnum
  )

from .initabstract import initabstract

class initdem(initabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initdem","Point layer"),
        "types": [QgsProcessing.TypeVectorPoint],
        "optional": True
      }
    },
    "OVERWRITE_MODE": {
      "ui_func": QgsProcessingParameterEnum,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initdem","Overwrite or Append?"),
        "options":[
          QT_TRANSLATE_NOOP("initdem","Overwrite"),
          QT_TRANSLATE_NOOP("initdem","Append")
        ],
        "defaultValue": 0
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("sourceemissionfield","DEM" )
      }
    }
  }
  
  FIELDS_ADD = {    
    "alti":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None}
  }
      
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):    
    self.setFields(parameters, context, feedback)
    dest_id = self.createVectorLayerAsSink(parameters, context, feedback)
              
    return {"OUTPUT": dest_id}
  
  def createInstance(self):
    return initdem()

  def displayName(self):
    return self.tr("DEM")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initdem()
