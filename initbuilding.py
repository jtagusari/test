from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterBoolean
  )

from .initabstract import initabstract

class initbuilding(initabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initbuilding","Polygon layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initbuilding","Overwrite existing fields?"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("initbuilding","Building" )
      }
    }
  }
  
  FIELDS_ADD = {    
    "PK":         {"TYPE": QVariant.Int   , "DEFAULT_VALUE": None},
    "height":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": 6.0}
  }
      
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):    
    self.setFields(parameters, context, feedback)
    dest_id = self.createVectorLayerAsSink(parameters, context, feedback)
              
    return {"OUTPUT": dest_id}
  
  def createInstance(self):
    return initbuilding()

  def displayName(self):
    return self.tr("Building")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initbuilding()
