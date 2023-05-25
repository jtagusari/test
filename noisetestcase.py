
from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterString,
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterEnum,
  QgsProcessingParameterFeatureSink,
  QgsFeatureRequest,
  QgsReferencedRectangle,
  QgsCoordinateReferenceSystem
  )

import datetime
import os
from .noiseabstract import noiseabstract


class noisetestcase(noiseabstract):
  PARAMETERS = {
    "CASE": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterEnum,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","Case"),
        "options": ["TC01"],
        "defaultValue": 0
      }
    },
    "TEST": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","test")
      }
    },
    "BUILDING__CASE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","Building layer")
      }
    },
    "RECEIVER_CASE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","Receiver layer")
      }
    },
    "DEM_CASE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","Elevation point layer")
      }
    },
    "GROUND_ABS_CASE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisetestcase","Ground absorption layer")
      }
    },  
    "LEVEL_CASE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisetestcase","Sound level" )
      }
    }    
  }
    
  def initAlgorithm(self, config):
    self.initParameters()

  def addTestCaseParameters(self, parameters, context, feedback):
    test_code = "TC{:02d}".format(self.parameterAsInt(parameters, "CASE", context) + 1)
    case_dir = os.path.join(os.path.dirname(__file__), "testcases", test_code)
    
    required_geom_names = ["SOURCE","BUILDING", "RECEIVER", "DEM", "GROUND_ABS"]
    n_mdl_param_names = ["roadGeomPath", "buildingGeomPath", "receiverGeomPath", "demGeomPath", "groundAbsorptionGeomPath"]
    for geom_name, n_mdl_name in zip(required_geom_names,n_mdl_param_names):
      if os.file.exists(os.path.join(case_dir, geom_name + ".geojson")):
        parameters[geom_name] = os.path.join(case_dir, geom_name + ".geojson")
        self.PARAMETERS[geom_name]["n_mdl"] = n_mdl_name
        self.PARAMETERS[geom_name]["save_layer_get_path"] = True
        if geom_name == "SOURCE":
          self.PARAMETERS[geom_name]["crs_referrence"] = True
    
    pass
  
  def processAlgorithm(self, parameters, context, feedback):
    self.initNoiseModellingPath(
      {
        "GROOVY_SCRIPT": os.path.join(os.path.dirname(__file__), "noisemodelling","hriskscript", "noisetestcase.groovy")
      }
    )
    self.addTestCaseParameters(parameters, context, feedback)
    self.initNoiseModellingArg(parameters, context, feedback)
                
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)
    feedback.setProgress(100)
    
              
    # finally import as sink
    output_dict = self.NOISEMODELLING["LEVEL_RESULTS"]
    output_dict.update(self.NOISEMODELLING["BUILDING_RESULTS"])
    for file_name, file_path in output_dict.items():
      self.PROC_RESULTS[file_name] = self.importNoiseModellingResultsAsSink(
        parameters, context, file_name, file_path
        )

    return self.PROC_RESULTS
  
  def displayName(self):
    return self.tr("Exec test case")

  def group(self):
    return self.tr("Configurations")

  def groupId(self):
    return "config"

  def createInstance(self):
    return noisetestcase()

