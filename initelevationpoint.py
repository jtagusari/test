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

class initelevationpoint(initabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initelevationpoint","Point layer"),
        "types": [QgsProcessing.TypeVectorPoint],
        "optional": True
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterEnum,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initelevationpoint","Overwrite existing fields?"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("initelevationpoint","Elevation points" )
      }
    }
  }
  
  def __init__(self) -> None:
    super().__init__()
    self.FIELDS_ADD.update(
      {"alti":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None}}
    )
      
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):    
    self.setFields(parameters, context, feedback)
    dest_id = self.createVectorLayerAsSink(parameters, context, feedback)
              
    return {"OUTPUT": dest_id}
  
  def createInstance(self):
    return initelevationpoint()

  def displayName(self):
    return self.tr("Elevation point")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initelevationpoint()
