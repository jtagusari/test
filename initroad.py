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
    "OVERWRITE_MODE": {
      "ui_func": QgsProcessingParameterEnum,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("initroad","Overwrite or Append?"),
        "options":[
          QT_TRANSLATE_NOOP("initroad","Overwrite"),
          QT_TRANSLATE_NOOP("initroad","Append")
        ],
        "defaultValue": 0
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("sourceemissionfield","Road with emission fields" )
      }
    }
  }
  
  FIELDS_ADD = {    
    "pk":         {"TYPE": QVariant.Int   , "DEFAULT_VALUE": None},
    "lv_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lv_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lv_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "mv_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "mv_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "mv_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "hv_d":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "hv_e":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "hv_n":       {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lv_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "lv_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "lv_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "mv_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "mv_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "mv_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "hv_spd_d":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "hv_spd_e":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "hv_spd_n":   {"TYPE": QVariant.Double, "DEFAULT_VALUE": 60.0},
    "lwd63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwd8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwe8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn63":      {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn125":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn250":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn500":     {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn1000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn2000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn4000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
    "lwn8000":    {"TYPE": QVariant.Double, "DEFAULT_VALUE": None},
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
