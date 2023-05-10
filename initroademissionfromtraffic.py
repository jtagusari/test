
from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsFeatureRequest,
  QgsVectorLayer
  )

from qgis import processing
import os
from .algabstract import algabstract

class initroademissionfromtraffic(algabstract):
  PARAMETERS = {  
    "INPUT": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("initroademissionfromtraffic","Road layer"),
        "types": [QgsProcessing.TypeVectorLine]
      },
      "n_mdl":"roadGeomPath",
      "save_layer_get_path": True
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("initroademissionfromtraffic","Road" )
      }
    }
  }
  
  def initAlgorithm(self, config):
    self.initParameters()   
    
  def addPathNoiseModelling(self):
    self.NOISEMODELLING["ROAD_LW_PATH"] = os.path.join(self.NOISEMODELLING["TEMP_DIR"], "LW_ROADS.geojson")
    self.NOISEMODELLING["ROAD_JOINED_PATH"] = os.path.join(self.NOISEMODELLING["TEMP_DIR"], "LW_ROADS_JOINED.geojson")

  def processAlgorithm(self, parameters, context, feedback):
    self.initNoiseModelling("initroademissionfromtraffic.groovy")
    self.initWpsArgs(parameters,context,feedback)    
    
    feedback.pushCommandInfo(self.NOISEMODELLING["CMD"])   
    
    # execute groovy script using wps_scripts
    self.execNoiseModelling(parameters, context, feedback)
    
    # join to the source geom
    
    # first add level values to the receivers
    road_tr_layer = self.parameterAsSource(parameters, "INPUT", context).materialize(QgsFeatureRequest(), feedback)
    road_lw_layer = QgsVectorLayer(self.NOISEMODELLING["ROAD_LW_PATH"])
    
    lw_in_road_tr_layer = [fld for fld in road_tr_layer.fields().names() if fld[:3].lower() in ["lwd", "lwe","lwn"]]
    
    if len(lw_in_road_tr_layer) > 0:
      road_tr_layer = processing.run(
        "native:deletecolumn",
        {
          "INPUT": road_tr_layer,
          "COLUMN": lw_in_road_tr_layer,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
    
    processing.run(
      "native:joinattributestable",
      {
        "INPUT": road_tr_layer,
        "FIELD": "pk",
        "INPUT_2": road_lw_layer,
        "FIELD_2": "PK",
        "FIELDS_TO_COPY": [fld for fld in road_lw_layer.fields().names() if fld not in ["PK"]],
        "METHOD": 0,
        "DISCARD_NONMATCHING": False,
        "PREFIX": "",
        "OUTPUT": self.NOISEMODELLING["ROAD_JOINED_PATH"]
      }
    )
    
    # import the result    
    dest_id = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT", self.NOISEMODELLING["ROAD_JOINED_PATH"])
    
    return {"OUTPUT": dest_id}
    
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Road emission calculated from traffic")

  def group(self):
    return self.tr("Initialize features")

  def groupId(self):
    return "initfeature"

  def createInstance(self):
    return initroademissionfromtraffic()