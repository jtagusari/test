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

class initgroundabsorption(initabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initgroundabsorption","Polygon layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterEnum,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initgroundabsorption","Overwrite existing fields?"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("initgroundabsorption","Ground absorption" )
      }
    }
  }
  
  def __init__(self) -> None:
    super().__init__()
    self.FIELDS_ADD.update(
      {"G":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": 0.0}}
    )
      
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):    
    self.setFields(parameters, context, feedback)
    dest_id = self.createVectorLayerAsSink(parameters, context, feedback)
              
    return {"OUTPUT": dest_id}
  
  def createInstance(self):
    return initgroundabsorption()

  def displayName(self):
    return self.tr("Ground absorption")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initgroundabsorption()
