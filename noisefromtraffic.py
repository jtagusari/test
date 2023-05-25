
from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterString,
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink,
  QgsFeatureRequest,
  QgsReferencedRectangle,
  QgsCoordinateReferenceSystem
  )

import datetime
import os
from .noiseabstract import noiseabstract

class noisefromtraffic(noiseabstract):
  PARAMETERS = {
    "ROAD": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Road layer"),
        "types": [QgsProcessing.TypeVectorLine]
      },
      "n_mdl":"roadGeomPath",
      "save_layer_get_path": True
    },
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },
    "RECEIVER": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Receiver layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      },
      "n_mdl": "receiverGeomPath",
      "save_layer_get_path": True
    },
    "DEM": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Elevation point layer"),
        "types": [QgsProcessing.TypeVectorPoint],
        "optional": True
      },
      "n_mdl": "demGeomPath",
      "save_layer_get_path": True
    },
    "GROUND_ABS": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Ground absorption layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      },
      "n_mdl":"groundAbsPath",
      "save_layer_get_path": True
    },
  
    "MAX_SRC_DIST": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Max distance between source and receiver (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 200.0, "maxValue": 1000.0
      },
      "n_mdl": "confMaxSrcDist"
    },
    "MAX_REFL_DIST": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Max distance between source and reflection wall (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 50.0, "maxValue": 300.0
      },
      "n_mdl": "confMaxReflDist"
    },
    "REFL_ORDER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Max number of reflections (times)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 1, "maxValue": 5
      },
      "n_mdl": "confReflOrder"
    },
    "HUMIDITY": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Relative humidity (%)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 70.0, "maxValue": 100.0
      },
      "n_mdl": "confHumidity"
    },
    "TEMPERATURE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Temperature (°C)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": -40.0, "defaultValue": 15.0, "maxValue": 50.0
      },
      "n_mdl": "confTemperature"
    },
    "WALL_ALPHA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Reflectance at wall (0: fully absorbent - 1: fully reflective)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 1.0, "maxValue": 1.0
      },
      "n_mdl": "paramWallAlpha"
    }, 
    "DIFF_VERTICAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Diffraction at vertical edge"),
        "defaultValue": False
      },
      "n_mdl": "confDiffVertical"
    },
    "DIFF_HORIZONTAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Diffraction at horizontal edge"),
        "defaultValue": True
      },
      "n_mdl": "confDiffHorizontal"
    },
    "FAV_OCURRENCE_DAY": {
      "advanced": True,
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Probability of occurrence of favorable condition (day)"),
        "defaultValue": "0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5"
      },
      "n_mdl": "confFavorableOccurrencesDay"
    },
    "FAV_OCURRENCE_EVENING": {
      "advanced": True,
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Probability of occurrence of favorable condition (evening)"),
        "defaultValue": "0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5"
      },
      "n_mdl": "confFavorableOccurrencesEvening"
    },
    "FAV_OCURRENCE_NIGHT": {
      "advanced": True,
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Probability of occurrence of favorable condition (night)"),
        "defaultValue": "0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5"
      },
      "n_mdl": "confFavorableOccurrencesNight"
    },
    "THREAD_NUMBER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Number of threads to calculate (0: all)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 0, "maxValue": 20
      },
      "n_mdl": "confThreadNumber"
    },
    "ESTIMATE_LEVEL_AND_RISK": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Estimate sound levels and health risks (only for facade receivers)"),
        "defaultValue": False
      }
    },
    "WPS_ARGS": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Arguments for the calculation" )
      },
      "visibleByDefault": False
    },    
    "LDEN": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Lden" )
      },
      "visibleByDefault": True
    },    
    "LNIGHT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Lnight" )
      },
      "visibleByDefault": True
    },    
    "LDAY": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Lday" )
      },
      "visibleByDefault": False
    },    
    "LEVENING": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Levening" )
      },
      "visibleByDefault": False
    },    
    "BUILDING_WITH_LEVEL": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Building with facade level" )
      },
      "visibleByDefault": True
    }
  }
    
  def initAlgorithm(self, config):
    self.initParameters()


  def processAlgorithm(self, parameters, context, feedback):    
    self.initNoiseModellingPath(
      {
        "GROOVY_SCRIPT": os.path.join(os.path.dirname(__file__), "noisemodelling","hriskscript", "noisefromtraffic.groovy")
      }
    )
    self.initNoiseModellingArg(parameters, context, feedback)
                
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)   
    feedback.setProgress(100)
    
    self.NOISEMODELLING["WPS_ARGS"].update({"time_stamp": datetime.datetime.now().isoformat()})
    
    # join sound levels to buildings, if specified
    if self.parameterAsBoolean(parameters, "ESTIMATE_LEVEL_AND_RISK", context):
      
      # set buildings and receivers layer
      bldg_layer = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback)
      rcv_layer = self.parameterAsSource(parameters, "RECEIVER", context).materialize(QgsFeatureRequest(), feedback)
      
      # check if the receier has building id
      if self.BLDG_LEVEL_ARGS["RECEIVER_BID"] in rcv_layer.fields().names() and \
        self.BLDG_LEVEL_ARGS["RECEIVER_RID"] in rcv_layer.fields().names():
          self.cmptBuildingLevel(parameters,context,feedback,bldg_layer,rcv_layer)
      
    
    # output the results
    self.PROC_RESULTS["WPS_ARGS"] = self.outputWpsArgs(
      parameters, context,
      QgsReferencedRectangle(
        self.parameterAsSource(parameters, "RECEIVER", context).materialize(QgsFeatureRequest(), feedback).extent(),
        QgsCoordinateReferenceSystem("EPSG:" + self.NOISEMODELLING["WPS_ARGS"]["inputSRID"])
      )
    )    
    
    # finally import as sink
    output_dict = self.NOISEMODELLING["LEVEL_RESULTS"]
    output_dict.update(self.NOISEMODELLING["BUILDING_RESULTS"])
    for file_name, file_path in output_dict.items():
      self.PROC_RESULTS[file_name] = self.importNoiseModellingResultsAsSink(
        parameters, context, file_name, file_path
        )

    return self.PROC_RESULTS
  
  def displayName(self):
    return self.tr("Prediction from traffic")

  def group(self):
    return self.tr("Predict sound level")

  def groupId(self):
    return "soundlevel"

  def createInstance(self):
    return noisefromtraffic()

