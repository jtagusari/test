from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterBoolean,
  QgsField,
  QgsFeature,
  QgsVectorLayer
  )

import sys
from .algabstract import algabstract

class sourceaddroadfields(algabstract):
  PARAMETERS = {                  
    "INPUT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("sourceemissionfield","Line layer"),
        "types": [QgsProcessing.TypeVectorLine],
        "optional": True
      }
    },
    "STOP_IF_DEFINED": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args":{
        "description" : QT_TRANSLATE_NOOP("sourceemissionfield","Stop the process if there are any field already defined (or append unique fields without stopping the process)"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("sourceemissionfield","Road with emission fields" )
      }
    }
  }
  
  ROAD_FIELDS = {    
    "pk":        {"type": QVariant.Int},
    "lv_d":      {"type": QVariant.Double},
    "lv_e":      {"type": QVariant.Double},
    "lv_n":      {"type": QVariant.Double},
    "mv_d":      {"type": QVariant.Double},
    "mv_e":      {"type": QVariant.Double},
    "mv_n":      {"type": QVariant.Double},
    "hv_d":      {"type": QVariant.Double},
    "hv_e":      {"type": QVariant.Double},
    "hv_n":      {"type": QVariant.Double},
    "lv_spd_d":  {"type": QVariant.Double},
    "lv_spd_e":  {"type": QVariant.Double},
    "lv_spd_n":  {"type": QVariant.Double},
    "mv_spd_d":  {"type": QVariant.Double},
    "mv_spd_e":  {"type": QVariant.Double},
    "mv_spd_n":  {"type": QVariant.Double},
    "hv_spd_d":  {"type": QVariant.Double},
    "hv_spd_e":  {"type": QVariant.Double},
    "hv_spd_n":  {"type": QVariant.Double},
    "lwd63":      {"type": QVariant.Double},
    "lwd125":     {"type": QVariant.Double},
    "lwd250":     {"type": QVariant.Double},
    "lwd500":     {"type": QVariant.Double},
    "lwd1000":    {"type": QVariant.Double},
    "lwd2000":    {"type": QVariant.Double},
    "lwd4000":    {"type": QVariant.Double},
    "lwd8000":    {"type": QVariant.Double},
    "lwe63":      {"type": QVariant.Double},
    "lwe125":     {"type": QVariant.Double},
    "lwe250":     {"type": QVariant.Double},
    "lwe500":     {"type": QVariant.Double},
    "lwe1000":    {"type": QVariant.Double},
    "lwe2000":    {"type": QVariant.Double},
    "lwe4000":    {"type": QVariant.Double},
    "lwe8000":    {"type": QVariant.Double},
    "lwn63":      {"type": QVariant.Double},
    "lwn125":     {"type": QVariant.Double},
    "lwn250":     {"type": QVariant.Double},
    "lwn500":     {"type": QVariant.Double},
    "lwn1000":    {"type": QVariant.Double},
    "lwn2000":    {"type": QVariant.Double},
    "lwn4000":    {"type": QVariant.Double},
    "lwn8000":    {"type": QVariant.Double},
    "pvmt":      {"type": QVariant.String},
    "temp_d":    {"type": QVariant.Double},
    "temp_e":    {"type": QVariant.Double},
    "temp_n":    {"type": QVariant.Double},
    "ts_stud":   {"type": QVariant.Double},
    "pm_stud":   {"type": QVariant.Double},
    "junc_dist": {"type": QVariant.Double},
    "slope":     {"type": QVariant.Double},
    "way":       {"type": QVariant.Int}
  }
    
  def initAlgorithm(self, config):
    self.initParameters()


  def processAlgorithm(self, parameters, context, feedback):    
    # initialize road layer (and data provider) to which vector features added
    road_layer = self.parameterAsSource(parameters, "INPUT", context)
    stop_if_defined = self.parameterAsBoolean(parameters, "STOP_IF_DEFINED", context)
    
    if road_layer == None:
      road_layer = QgsVectorLayer("LineString", "road_blank", "memory")
    
    # initialize fields
    road_fields = road_layer.fields()
    
    # add fields of road traffic
    fields_append = []
    for field_name, args in self.ROAD_FIELDS.items():
      
      # if it is already defined, stop or pass
      if field_name.lower() in map(lambda x: x.lower(), road_fields.names()):
        if stop_if_defined:
          sys.exit(self.tr("The following field is already set in the layer: ") + field_name)
      # if it is not defined, append it
      else:
        args["name"] = field_name
        fields_append.append(field_name)
        road_fields.append(QgsField(**args))    
    
    if len(fields_append) == 0:
      sys.exit(self.tr("All road traffic fields have been already set."))
    
    # define the feature sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context, road_fields, road_layer.wkbType(), road_layer.sourceCrs()
    )
    
    # add features
    for fid, ft in enumerate(road_layer.getFeatures(), start = 1):
      new_ft = QgsFeature(road_fields)
      new_ft.setGeometry(ft.geometry())
      for existing_field in ft.fields().names():
        new_ft[existing_field] = ft[existing_field]
      new_ft["pk"] = fid
      sink.addFeature(new_ft)
          
    return {"OUTPUT": dest_id, "FIELDS_APPEND": fields_append}
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Road with acoustic information")

  def group(self):
    return self.tr("Set sources")

  def groupId(self):
    return "source"

  def createInstance(self):
    return sourceaddroadfields()
