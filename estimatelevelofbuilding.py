from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterField,
  QgsProcessingParameterString,
  QgsProcessingParameterBoolean,
  QgsFeatureRequest
  )

from qgis import processing
from .algabstract import algabstract
import sys

class estimatelevelofbuilding(algabstract):
  PARAMETERS = {
    
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "BUILDING_BID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Building ID Field of the Building layer"),
        "parentLayerParameterName": "BUILDING"
      }
    },
    "RECEIVER": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Receiver layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      }
    },
    "RECEIVER_BID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Building ID Field of the Receiver layer"),
        "parentLayerParameterName": "RECEIVER"
      }
    },
    "RECEIVER_RID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Receiver ID Field of the Receiver layer"),
        "parentLayerParameterName": "RECEIVER"
      }
    },                          
    "LEVEL": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Sound level layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      }
    },
    "LEVEL_RID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Receiver ID Field of the Sound level layer"),
        "parentLayerParameterName": "LEVEL"
      }
    },
    "LEVEL_ASSIGN": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Sound level field(s) of the Sound level layer"),
        "parentLayerParameterName": "LEVEL",
        "allowMultiple": True
      }
    },
    "LEVEL_PREFIX": {
      "ui_func": QgsProcessingParameterString,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Prefix of the Sound level field(s)"),
        "defaultValue": "Level_"
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Overwrite fields if they already exist?"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("estimatelevelofbuilding","Building features with facade levels")
      }
    }
  }
      
  def initAlgorithm(self, config):
    self.initParameters()


  def processAlgorithm(self, parameters, context, feedback):
    
    # initialize road layer (and data provider) to which vector features added
    bldg = self.parameterAsSource(parameters, "BUILDING", context)
    bldg_bid = self.parameterAsString(parameters, "BUILDING_BID", context)
    
    if not bldg_bid in bldg.fields().names():
      sys.exit(self.tr("The following attribute does not exist in the bldg layer:") + bldg_bid)
    
    receiver = self.parameterAsSource(parameters, "RECEIVER", context).materialize(QgsFeatureRequest(), feedback)
    receiver_bid = self.parameterAsFields(parameters, "RECEIVER_BID", context)[0]
    receiver_rid = self.parameterAsFields(parameters, "RECEIVER_RID", context)[0]
    
    if not receiver_bid in receiver.fields().names():
      sys.exit(self.tr("The following attribute does not exist in the receiver layer:") + receiver_bid)
    if not receiver_rid in receiver.fields().names():
      sys.exit(self.tr("The following attribute does not exist in the receiver layer:") + receiver_rid)

    
    level = self.parameterAsSource(parameters, "LEVEL", context).materialize(QgsFeatureRequest(), feedback)
    level_rid = self.parameterAsFields(parameters, "LEVEL_RID", context)[0]
    level_values = self.parameterAsFields(parameters, "LEVEL_ASSIGN", context)
    level_prefix = self.parameterAsString(parameters, "LEVEL_PREFIX", context)

    if not level_rid in level.fields().names():
      sys.exit(self.tr("The following attribute does not exist in the receiver layer:") + level_rid)
    
    for level_value in level_values:
      if not level_value in level.fields().names():
        sys.exit(self.tr("The following attribute does not exist in the receiver layer:") + level_value)
    
    # first add level values to the receivers
    receiver_joined = processing.run(
      "native:joinattributestable",
      {
        "INPUT": receiver,
        "FIELD": receiver_rid,
        "INPUT_2": level,
        "FIELD_2": level_rid,
        "FIELDS_TO_COPY": level_values,
        "METHOD": 0,
        "DISCARD_NONMATCHING": False,
        "PREFIX": level_prefix,
        "OUTPUT": "TEMPORARY_OUTPUT"
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
      
    
    # aggregate the level values for each bldg
    aggregates = [
      {
        "aggregate": "first_value", "input": receiver_bid, "name": receiver_bid,
        "delimiter": ",", "length": 0, "precision": 0, "type": 4
      }
    ]
    summarized_field = []
    for field_copy in level_values:
      field_copied = level_prefix + field_copy
      for func_str in ["maximum", "minimum"]:
        new_field = field_copied + "_" + func_str
        aggregates.append(
          {
            "aggregate": func_str, "input": field_copied, "name": new_field,
            "delimiter": ",", "length": 0, "precision": 0, "type": 6
          }
        )
        summarized_field.append(new_field)
      
    
    receiver_aggregate = processing.run(
      "native:aggregate",
      {
        "INPUT": receiver_joined,
        "GROUP_BY": receiver_bid,
        "AGGREGATES": aggregates,
        "OUTPUT": "TEMPORARY_OUTPUT"
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
    
    # finally the aggregated values are joined
    building_joined = processing.run(
      "native:joinattributestable",
      {
        "INPUT": bldg.materialize(QgsFeatureRequest(), feedback),
        "FIELD": bldg_bid,
        "INPUT_2": receiver_aggregate,
        "FIELD_2": receiver_bid,
        "FIELDS_TO_COPY": summarized_field,
        "METHOD": 0,
        "DISCARD_NONMATCHING": False,
        "PREFIX": None,
        "OUTPUT": "TEMPORARY_OUTPUT"
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
        
    # define the feature sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context, 
      building_joined.fields(), building_joined.wkbType(), building_joined.sourceCrs()
    )
    
    sink.addFeatures(building_joined.getFeatures())
          
    return {"OUTPUT": dest_id}
  

  def displayName(self):
    return self.tr("Estimate levels to buildings")

  def group(self):
    return self.tr("Evaluate health risk")

  def groupId(self):
    return "healthrisk"

  def createInstance(self):
    return estimatelevelofbuilding()
