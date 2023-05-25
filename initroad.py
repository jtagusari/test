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

class initroad(initabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initroad","Line layer"),
        "types": [QgsProcessing.TypeVectorLine],
        "optional": True
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initroad","Overwrite existing fields?"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("initroad","Road" )
      }
    }
  }
  
  FIELDS_ADD = {    
    "LV_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LV_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LV_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "MV_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "MV_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "MV_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "HV_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "HV_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "HV_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LV_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "LV_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "LV_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "MV_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "MV_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "MV_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "HV_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "HV_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "HV_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "LWd63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWd8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWe8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "LWn8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "pvmt":       {"TYPE": QVariant.String, "DEFAULT_VALUE": "DEF"},
    "temp_d":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "temp_e":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "temp_n":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "ts_stud":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "pm_stud":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "junc_dist":  {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "slope":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "way":        {"TYPE": QVariant.Int   , "DEFAULT_VALUE": None}
  }
  
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):
    self.setFields(parameters, context, feedback)
    dest_id = self.createVectorLayerAsSink(parameters, context, feedback)
              
    return {"OUTPUT": dest_id}
  
  def createInstance(self):
    return initroad()


  def displayName(self):
    return self.tr("Road with acoustic information")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initroad()
