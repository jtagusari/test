
from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProject,
  QgsProcessing,
  QgsVectorLayer,
  QgsVectorFileWriter,
  QgsCoordinateTransformContext,
  QgsProcessingParameterString,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFolderDestination,
  QgsGraduatedSymbolRenderer,
  QgsRendererRange,
  QgsClassificationRange,
  QgsMarkerSymbol
  )
import asyncio
import re
import os
import sys
import datetime
import json

class noisefromtraffic(QgsProcessingAlgorithm):
  PARAMETERS = {  
    "PROJECT_ID": {
      "ui_func": QgsProcessingParameterString,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Project ID"),
        "defaultValue":  datetime.datetime.now().strftime("%y%m%d%H%M%S")
      }
    },
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
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","DEM layer"),
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
    "THREAD_NUMBER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Number of threads to calculate (0: all)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 0, "maxValue": 20
      },
      "n_mdl": "confThreadNumber"
    }    
  }
  
  OUTPUT = {
    "OUTPUT_DIRECTORY": {
      "ui_func": QgsProcessingParameterFolderDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("noisefromtraffic","Output directory" )
      }
    }
  }
  
  NoiseModelling_HOME = os.environ["NoiseModelling"]
  NoiseModelling_SCRIPT = os.path.join(os.path.dirname(__file__), "groovy", "noisefromtraffic.groovy")
  
  PROJECT_ID_PREFIX = "proj_" # project id must start with a alphabet
  PROJECT_ID_SUFFIX = "_" # project id must start with a alphabet
  
  def initAlgorithm(self, config):
    self.PARAMETERS["PROJECT_ID"]["ui_args"]["defaultValue"] = datetime.datetime.now().strftime("%y%m%d%H%M%S")
    
    for key, value in {**self.PARAMETERS, **self.OUTPUT}.items():
      args = value.get("ui_args")
      args["name"] = key
      args["description"] = self.tr(args["description"])
                    
      ui = value.get("ui_func")(**args)
      
      if value.get("advanced") != None and value.get("advanced") == True:
        ui.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        
      self.addParameter(ui)  
    

  def processAlgorithm(self, parameters, context, feedback):
        
    # import ptvsd
    # ptvsd.debug_this_thread()
    # project ID
    self.PROJECT_ID = self.PROJECT_ID_PREFIX + self.parameterAsString(parameters, "PROJECT_ID", context)
    
    # folder where the files are saved
    self.OUTPUT_DIR = os.path.normpath(self.parameterAsOutputLayer(parameters, "OUTPUT_DIRECTORY", context))
    if not os.path.exists(self.OUTPUT_DIR):
      os.mkdir(self.OUTPUT_DIR)
        
    # initialize arguments passed to groovy script
    wps_args = {
      "w": self.OUTPUT_DIR, 
      "s": self.NoiseModelling_SCRIPT, 
      "projectId": self.PROJECT_ID + self.PROJECT_ID_SUFFIX,
      "exportDir": self.OUTPUT_DIR
    }
    
    # get CRS
    crs_key = [key for key, value in self.PARAMETERS.items() if value.get("crs_referrence") != None and value.get("crs_referrence") == True]
    crs_referrence = self.parameterAsVectorLayer(parameters, crs_key[0], context).sourceCrs()
    
    # define save function
    def save_geom(vector_layer, path):
      save_options = QgsVectorFileWriter.SaveVectorOptions()
      save_options.driverName = "GeoJSON"
      QgsVectorFileWriter.writeAsVectorFormatV3(
        vector_layer, path, QgsCoordinateTransformContext(), save_options
      )
    
    # get the value from each input, which are passed to groovy script
    for key, value in self.PARAMETERS.items():
      if value.get("n_mdl") != None:
        if value.get("save_layer_get_path") != None and value.get("save_layer_get_path") == True:
          geom = self.parameterAsVectorLayer(parameters, key, context)
          if geom != None:
            if geom.sourceCrs() != crs_referrence:
              sys.exit(self.tr("CRS is not the same!"))
            geom_path = os.path.join(self.OUTPUT_DIR, self.PROJECT_ID + key + ".geojson")
            save_geom(geom, geom_path)
            wps_args[value.get("n_mdl")] = geom_path
        else:
          if value.get("ui_func") == QgsProcessingParameterNumber:
            if value.get("ui_args").get("type") == QgsProcessingParameterNumber.Integer:
              value_input = self.parameterAsInt(parameters, key, context)
            else:
              value_input = self.parameterAsDouble(parameters, key, context)
          elif value.get("ui_func") == QgsProcessingParameterBoolean:
            value_input = self.parameterAsInt(parameters, key, context)
          elif value.get("ui_func") == QgsProcessingParameterString:
            value_input = self.parameterAsString(parameters, key, context)
          wps_args[value.get("n_mdl")] = value_input
    
    # set the command to execute
    cmd = os.path.join("bin","wps_scripts") + "".join([" -" + k + " " + str(v) for k, v in wps_args.items()])
    feedback.pushCommandInfo(cmd)    
    
    # output arguments as json
    wps_args["time_stamp"] = datetime.datetime.now().isoformat()
    with open(os.path.join(self.OUTPUT_DIR, self.PROJECT_ID + "arguments.json"), "w") as fj:
      json.dump(wps_args, fj, indent = 2)
    
    # execute groovy script using wps_scripts
    loop = asyncio.ProactorEventLoop()      
    loop.run_until_complete(
      self.calc_stream_with_progress(cmd, feedback)
    )
    
    return {}
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    proj_group = QgsProject.instance().layerTreeRoot().addGroup(self.PROJECT_ID)
    isosurface_renderer = QgsGraduatedSymbolRenderer("LAEQ")
    isocategory = {
      "< 35 dB":    {"lower": -999, "upper":  35, "color": "255,255,255,255"},
      "35 - 40 dB": {"lower":   35, "upper":  40, "color": "160,186,191,255"},
      "40 - 45 dB": {"lower":   40, "upper":  45, "color": "184,214,209,255"},
      "45 - 50 dB": {"lower":   45, "upper":  50, "color": "206,228,204,255"},
      "50 - 55 dB": {"lower":   50, "upper":  55, "color": "226,242,191,255"},
      "55 - 60 dB": {"lower":   55, "upper":  60, "color": "243,198,131,255"},
      "60 - 65 dB": {"lower":   60, "upper":  65, "color": "232,126,77,255" },
      "65 - 70 dB": {"lower":   65, "upper":  70, "color": "205,70,62,255"  },
      "70 - 75 dB": {"lower":   70, "upper":  75, "color": "161,26,77,255"  },
      "75 - 80 dB": {"lower":   75, "upper":  80, "color": "117,8,92,255"   },
      "> 80 dB":    {"lower":   80, "upper": 999, "color": "67,10,74,255"   }
    }
    
    for key, value in isocategory.items():
      isosurface_renderer.addClassRange(
        QgsRendererRange(
          QgsClassificationRange(key, value.get("lower"), value.get("upper")), 
          QgsMarkerSymbol.createSimple({"color":value.get("color")})
        )
      )
      
      
    for noise_idx in ["LDAY","LEVENING", "LNIGHT", "LDEN"]:
      file_path = os.path.join(self.OUTPUT_DIR, self.PROJECT_ID + self.PROJECT_ID_SUFFIX + noise_idx + "_GEOM.geojson")
      if os.path.exists(file_path):
        geom = QgsVectorLayer(path = file_path, baseName = noise_idx)
        geom.setRenderer(isosurface_renderer)
        geom.triggerRepaint()
        
        QgsProject.instance().addMapLayer(geom, False)
        proj_group.addLayer(geom)
    return {}

  async def calc_stream_with_progress(self, cmd, feedback):
    # set proc
    proc = await asyncio.create_subprocess_shell(
      cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
      cwd = self.NoiseModelling_HOME
    )

    while True:
      if proc.stdout.at_eof() and proc.stderr.at_eof():
        break  

      stderr_raw = await proc.stderr.readline() # for debugging
      stderr = stderr_raw.decode()
      
      if stderr:
        feedback.pushInfo(stderr.replace("\n",""))

      prg_match = re.search(r".*[0-9]+\.[0-9]+.*%", stderr)
      if prg_match:                
        feedback.setProgress(
          int(float(re.search(r"[0-9]+\.[0-9]+", prg_match.group()).group()))
        )

  def name(self):
    return "noisefromtraffic"

  def displayName(self):
    return self.tr("Level from traffic")

  def group(self):
    return self.tr("Noise prediction")

  def groupId(self):
    return "noiseprediction"

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return noisefromtraffic()
