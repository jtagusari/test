
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
from .noiseabstract import noiseabstract

class noisefromemission(noiseabstract):
  PARAMETERS = {
    "ROAD": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Road layer"),
        "types": [QgsProcessing.TypeVectorLine]
      },
      "n_mdl":"roadGeomPath",
      "save_layer_get_path": True
    },
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },
    "RECEIVER": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Receiver layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      },
      "n_mdl": "receiverGeomPath",
      "save_layer_get_path": True
    },
    "DEM": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Elevation point layer"),
        "types": [QgsProcessing.TypeVectorPoint],
        "optional": True
      },
      "n_mdl": "demGeomPath",
      "save_layer_get_path": True
    },
    "GROUND_ABS": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Ground absorption layer"),
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
        "description": QT_TRANSLATE_NOOP("noisefromemission","Max distance between source and receiver (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 200.0, "maxValue": 1000.0
      },
      "n_mdl": "confMaxSrcDist"
    },
    "MAX_REFL_DIST": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Max distance between source and reflection wall (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 50.0, "maxValue": 300.0
      },
      "n_mdl": "confMaxReflDist"
    },
    "REFL_ORDER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Max number of reflections (times)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 1, "maxValue": 5
      },
      "n_mdl": "confReflOrder"
    },
    "HUMIDITY": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Relative humidity (%)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 70.0, "maxValue": 100.0
      },
      "n_mdl": "confHumidity"
    },
    "TEMPERATURE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Temperature (°C)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": -40.0, "defaultValue": 15.0, "maxValue": 50.0
      },
      "n_mdl": "confTemperature"
    },
    "WALL_ALPHA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Reflectance at wall (0: fully absorbent - 1: fully reflective)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 1.0, "maxValue": 1.0
      },
      "n_mdl": "paramWallAlpha"
    }, 
    "DIFF_VERTICAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Diffraction at vertical edge"),
        "defaultValue": False
      },
      "n_mdl": "confDiffVertical"
    },
    "DIFF_HORIZONTAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Diffraction at horizontal edge"),
        "defaultValue": True
      },
      "n_mdl": "confDiffHorizontal"
    },
    "THREAD_NUMBER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Number of threads to calculate (0: all)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 0, "maxValue": 20
      },
      "n_mdl": "confThreadNumber"
    },
    "ESTIMATE_LEVEL_AND_RISK": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Estimate sound levels and health risks (only for facade receivers)"),
        "defaultValue": False
      }
    },
    "MAKE_ISOSURFACE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Make isosurface (only for delaunay receivers and triangle layer is necessary)"),
        "defaultValue": False
      }
    },
    "TRIANGLE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Triangle layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      }
    },
    "ISO_CLASS": {
      "advanced": True,
      "ui_func": QgsProcessingParameterString,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromemission","Separation of sound levels for isosurfaces (e.g. 35.0,40.0)"),
        "defaultValue": "35.0,40.0,45.0,50.0,55.0,60.0,65.0,70.0,75.0,80.0,200.0",
        "multiLine": False
      }
    },    
    "SMOOTH_COEF": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Smoothing parameter (Bezier curve coefficient)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 1.0, "maxValue": 2.0
      }
    },
    "WPS_ARGS": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Arguments used for the calculation" )
      },
      "visibleByDefault": False
    },    
    "LDEN": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Lden" )
      },
      "visibleByDefault": True
    },    
    "LNIGHT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Lnight" )
      },
      "visibleByDefault": True
    },    
    "LDAY": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Lday" )
      },
      "visibleByDefault": False
    },    
    "LEVENING": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Levening" )
      },
      "visibleByDefault": False
    },    
    "BUILDING_WITH_LEVEL": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromemission","Building with facade level" )
      },
      "visibleByDefault": True
    }
  }
    
  def initAlgorithm(self, config):
    self.initParameters()

  def processAlgorithm(self, parameters, context, feedback):
    self.initNoiseModelling("noisefromemission.groovy")
    self.initWpsArgs(parameters, context, feedback)

    feedback.pushCommandInfo(self.NOISEMODELLING["CMD"])   
                
    # execute groovy script using wps_scripts
    self.execNoiseModelling(parameters, context, feedback)
    feedback.setProgress(100)
    
    self.NOISEMODELLING["WPS_ARGS"].update({"time_stamp": datetime.datetime.now().isoformat()})
    
    # join sound levels to buildings, if specified
    if self.parameterAsBoolean(parameters, "ESTIMATE_LEVEL_AND_RISK", context):
      
      # set buildings and receivers layer
      bldg_layer = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback)
      rcv_layer = self.parameterAsSource(parameters, "RECEIVER", context).materialize(QgsFeatureRequest(), feedback)
      
      # check if the receier has building id
      if self.ARGS_FOR_BLDG_LEVEL["RECEIVER_BID"] in rcv_layer.fields().names() and \
        self.ARGS_FOR_BLDG_LEVEL["RECEIVER_RID"] in rcv_layer.fields().names():
          self.cmptBuildingLevel(parameters,context,feedback,bldg_layer,rcv_layer)
      
    # make iso surface, if specified
    if self.parameterAsBoolean(parameters, "MAKE_ISOSURFACE", context):
      
      # set buildings and receivers layer
      bldg_layer = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback)
      rcv_layer = self.parameterAsSource(parameters, "RECEIVER", context).materialize(QgsFeatureRequest(), feedback)
      
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
    output_dict = self.NOISEMODELLING["RESULTS_PATH"]
    output_dict.update(self.NOISEMODELLING["RESULTS_BUILDING_PATH"])
    for file_name, file_path in output_dict.items():
      self.PROC_RESULTS[file_name] = self.importNoiseModellingResultsAsSink(
        parameters, context, file_name, file_path
        )

    return self.PROC_RESULTS
  
  def displayName(self):
    return self.tr("Prediction from emission")

  def group(self):
    return self.tr("Predict sound level")

  def groupId(self):
    return "soundlevel"

  def createInstance(self):
    return noisefromemission()

