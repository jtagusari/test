
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
  QgsProcessing,
  QgsVectorFileWriter,
  QgsCoordinateTransformContext,
  QgsFeatureSink,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition,
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink
  )
import asyncio
import re
import tempfile
import os
import sys

class rtn_calc_alg(QgsProcessingAlgorithm):
  PARAMETERS = {  
    "ROAD": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": "Road layer",
        "types": [QgsProcessing.TypeVectorLine]
      },
      "n_mdl":"roadGeomPath",
      "save_layer_get_path": True
    },
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": "Building layer",
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },
    "RECEIVER": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": "Receiver layer",
        "types": [QgsProcessing.TypeVectorPoint]
      },
      "n_mdl": "receiverGeomPath",
      "save_layer_get_path": True
    },
    "DEM": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": "DEM layer",
        "types": [QgsProcessing.TypeVectorPoint],
        "optional": True
      },
      "n_mdl": "demGeomPath",
      "save_layer_get_path": True
    },
    "GROUND_ABS": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": "Ground absorption layer",
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
        "description": "Max distance between source and receiver (m)",
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 500.0, "maxValue": 1000.0
      },
      "n_mdl": "confMaxSrcDist"
    },
    "MAX_REFL_DIST": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Max distance between source and reflection wall (m)",
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 100.0, "maxValue": 300.0
      },
      "n_mdl": "confMaxReflDist"
    },
    "REFL_ORDER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Max number of reflections (times)",
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 3, "maxValue": 5
      },
      "n_mdl": "confReflOrder"
    },
    "HUMIDITY": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Relative humidity (%)",
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 70.0, "maxValue": 100.0
      },
      "n_mdl": "confHumidity"
    },
    "TEMPERATURE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Temperature (°C)",
        "type": QgsProcessingParameterNumber.Double,
        "minValue": -40.0, "defaultValue": 15.0, "maxValue": 50.0
      },
      "n_mdl": "confTemperature"
    },
    "WALL_ALPHA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Reflectance at wall (0: fully absorbent - 1: fully reflective)",
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 1.0, "maxValue": 1.0
      },
      "n_mdl": "confWallAlpha"
    }, 
    "DIFF_VERTICAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": "Diffraction at vertical edge",
        "defaultValue": False
      },
      "n_mdl": "confDiffVertical"
    },
    "DIFF_HORIZONTAL": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": "Diffraction at horizontal edge",
        "defaultValue": True
      },
      "n_mdl": "confDiffHorizontal"
    },
    "THREAD_NUMBER": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": "Number of threads to calculate (0: all)",
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 0, "defaultValue": 0, "maxValue": 20
      },
      "n_mdl": "confThreadNumber"
    }    
  }
  
  OUTPUT = {
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": "Output layer" 
      }
    }
  }
  
  NoiseModelling_SCRIPT = os.path.join(os.path.dirname(__file__), "rtn_calc.groovy")
  
  def initAlgorithm(self, config):
    for key, value in {**self.PARAMETERS, **self.OUTPUT}.items():
      args = value.get("ui_args")
      args["name"] = key
      args["description"] = self.tr(args["description"])
              
      ui = value.get("ui_func")(**args)
      
      if value.get("advanced") != None and value.get("advanced") == True:
        ui.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        
      self.addParameter(ui)  
    

  def processAlgorithm(self, parameters, context, feedback):
    import ptvsd
    ptvsd.debug_this_thread()
    
    
    # with tempfile.TemporaryDirectory() as tempdir:
    tempdir = tempfile.mkdtemp() # not to delete temporary directory
    
    wps_args = {"w": tempdir, "s": self.NoiseModelling_SCRIPT, "exportDir": tempdir}
    
    # get CRS
    crs_key = [key for key, value in self.PARAMETERS.items() if value.get("crs_referrence") != None and value.get("crs_referrence") == True]
    crs_referrence = self.parameterAsVectorLayer(parameters, crs_key[0], context).sourceCrs()
    
    # define save function
    def save_geom(vector_layer, path):
      save_options = QgsVectorFileWriter.SaveVectorOptions()
      save_options.driverName = "GeoJSON"
      QgsVectorFileWriter.writeAsVectorFormatV2(
        vector_layer, path, QgsCoordinateTransformContext(), save_options
      )
    
    # get the value from each input
    for key, value in self.PARAMETERS.items():
      if value.get("save_layer_get_path") != None and value.get("save_layer_get_path") == True:
        geom = self.parameterAsVectorLayer(parameters, key, context)
        if geom != None:
          if geom.sourceCrs() != crs_referrence:
            sys.exit(self.tr("CRS is not the same!"))
          geom_path = os.path.join(tempdir, key + ".geojson")
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
        wps_args[value.get("n_mdl")] = value_input
        
    
    # # save road layer      
    # road = self.parameterAsVectorLayer(parameters, self.ROAD, context)
    
    # qctc = QgsCoordinateTransformContext()
    # vw_options = QgsVectorFileWriter.SaveVectorOptions()
    # vw_options.driverName = "GeoJSON"
    
    # wps_args[self.ROAD.lower()] = os.path.join(tempdir, self.ROAD)
    # QgsVectorFileWriter.writeAsVectorFormatV2(
    #   road, wps_args[self.ROAD.lower()], qctc, vw_options
    # )
    # wps_args[self.ROAD.lower()] = wps_args[self.ROAD.lower()] + ".geojson"
    
    # # save other layers
    # for lname in [self.BUILDING, self.RECEIVER, self.DEM, self.GROUND_ABS]:  
    #   vl = self.parameterAsVectorLayer(parameters, lname, context)
    #   if vl != None:
    #     if vl.sourceCrs() != road.sourceCrs():
    #       sys.exit(self.tr("CRS is not the same!"))
    #     else:
    #       wps_args[lname.lower()] = os.path.join(tempdir, lname)
    #       QgsVectorFileWriter.writeAsVectorFormatV2(
    #         vl, wps_args[lname.lower()], qctc, vw_options
    #       )
    #       wps_args[lname.lower()] = wps_args[lname.lower()]+".geojson"
    
    # wps_args["paraWallAlpha"] = self.parameterAsDouble(parameters, self.REFLECTANCE, context)
    # wps_args["confReflOrder"] = self.parameterAsInt(parameters, self.MAX_N_REFL, context)
    # wps_args["confMaxSrcDist"] = self.parameterAsDouble(parameters, self.MAX_DIST_SRC, context)
    # wps_args["confMaxReflDist"] = self.parameterAsDouble(parameters, self.MAX_DIST_REFL, context)
    # wps_args["confThreadNumber"] = self.parameterAsInt(parameters, self.N_THREAD, context)
    # wps_args["confDiffVertical"] = self.parameterAsInt(parameters, self.DIF_AT_VEDGE, context)
    # wps_args["confDiffHorizontal"] = self.parameterAsInt(parameters, self.DIF_AT_HEDGE, context)
    # wps_args["confHumidity"] = self.parameterAsDouble(parameters, self.HUMIDITY, context)
    # wps_args["confTemperature"] = self.parameterAsDouble(parameters, self.TEMPERATURE, context)
    
    # (sink, dest_id) = self.parameterAsSink(
    #   parameters, "OUTPUT",
    #   context, road.fields(), road.wkbType(), road.sourceCrs()
    #   )

    args = "".join([" -" + k + " " + str(v) for k, v in wps_args.items()])
    
    nm_path = os.environ["NoiseModelling"]
    feedback.pushInfo("[cd:NoiseModelling] " + nm_path)
    
    cmd = "bin\wps_scripts" + args
    feedback.pushCommandInfo(cmd)    
    
    loop = asyncio.ProactorEventLoop()      
    # loop.run_until_complete(
    #   self.calc_stream_with_progress(nm_path, cmd, feedback)
    # )
      
    # return {self.OUTPUT: dest_id}

  async def calc_stream_with_progress(self, nm_path, cmd, feedback):
    # set proc
    proc = await asyncio.create_subprocess_shell(
      cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
      cwd = nm_path
    )

    while True:
      if proc.stdout.at_eof() and proc.stderr.at_eof():
        break  

      stderr = (await proc.stderr.readline()).decode()
      
      if stderr:
        feedback.pushInfo(stderr.replace("\n",""))

      prg_match = re.search(r"Compute.*[0-9]+\.[0-9]+.*%", stderr)
      if prg_match:                
        feedback.setProgress(
          int(float(re.search(r"[0-9]+\.[0-9]+", prg_match.group()).group()))
        )


  def name(self):
    return 'rtn_calc_alg'

  def displayName(self):
    return self.tr("rtn_calc_alg")

  def group(self):
    return self.tr('rtn')

  def groupId(self):
    return 'rtn'

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return rtn_calc_alg()
