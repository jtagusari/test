from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProject,
  QgsVectorLayer,
  QgsProcessing,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFolderDestination,
  QgsVectorFileWriter,
  QgsCoordinateTransformContext
  )

from qgis import processing

import os
import sys
import asyncio

class receiverdelaunaygrid(QgsProcessingAlgorithm):
  PARAMETERS = { 
    "BUILDING": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },    
    "SOURCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Source layer"),
        "types": [QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine,QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "sourceGeomPath",
      "save_layer_get_path": True
    },    
    "FENCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Fence layer"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True
      },
      "n_mdl": "fenceGeomPath",
      "save_layer_get_path": True
    },
    "MAX_PROP_DIST": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum propagation distance between sources and receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 500.0, "maxValue": 2000.0
      },
      "n_mdl": "maxPropDist"
    },
    "ROAD_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Road width (m), where no receivers will be set closer than it"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 2.0, "maxValue": 20.0
      },
      "n_mdl": "roadWidth"
    },
    "MAX_AREA": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum trianglar area (m2)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 10.0, "defaultValue": 500.0, "maxValue": 10000.0
      },
      "n_mdl": "maxArea"
    },
    "HEIGHT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Height of receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 4.0, "maxValue": 100.0
      },
      "n_mdl": "height"
    },
    "ISO_SURFACE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Whether isosurfaces will be visible at the location of buildings"),
        "defaultValue": False
      },
      "n_mdl": "isoSurfaceInBuildings"
    }
  }
  
  OUTPUT = {
    "OUTPUT_DIRECTORY": {
      "ui_func": QgsProcessingParameterFolderDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Output directory" )
      }
    }
  }
  
  RECEIVER_LAYER = None
  TRIANGLE_LAYER = None
  OUTPUT_DIR     = None
    
  NoiseModelling_HOME = os.environ["NoiseModelling"]
  NoiseModelling_SCRIPT = os.path.join(os.path.dirname(__file__), "groovy", "receiverdelaunaygrid.groovy")
  
    
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
    
    # import ptvsd
    # ptvsd.debug_this_thread()
    
    # folder where the files are saved
    self.OUTPUT_DIR = os.path.normpath(self.parameterAsOutputLayer(parameters, "OUTPUT_DIRECTORY", context))
    if not os.path.exists(self.OUTPUT_DIR):
      os.mkdir(self.OUTPUT_DIR)
              
    # set arguments for wps
    wps_args = {
      "w": self.OUTPUT_DIR, 
      "s": self.NoiseModelling_SCRIPT,
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
            geom_path = os.path.join(self.OUTPUT_DIR, key + "_DELAUNAYGRID.geojson")
            save_geom(geom, geom_path)
            wps_args[value.get("n_mdl")] = geom_path
        else:
          if value.get("ui_func") == QgsProcessingParameterNumber:
            if value.get("ui_args").get("type") == QgsProcessingParameterNumber.Integer:
              value_input = self.parameterAsInt(parameters, key, context)
            else:
              value_input = self.parameterAsDouble(parameters, key, context)
          wps_args[value.get("n_mdl")] = value_input
    
    # set the command to execute
    cmd = os.path.join("bin","wps_scripts") + "".join([" -" + k + " " + str(v) for k, v in wps_args.items()])
    feedback.pushCommandInfo(cmd)   
    
    # execute groovy script using wps_scripts
    loop = asyncio.ProactorEventLoop()      
    loop.run_until_complete(
      self.calc_stream(cmd, feedback)
    )
    
    receiver_geom_path = os.path.join(self.OUTPUT_DIR, "RECEIVERS.geojson")
    triangle_geom_path = os.path.join(self.OUTPUT_DIR, "TRIANGLES.geojson")
    
    self.RECEIVER_LAYER = QgsVectorLayer(receiver_geom_path, "receiver_delaunaygrid")
    self.TRIANGLE_LAYER = QgsVectorLayer(triangle_geom_path, "receiver_delaunaygrid_triangle")
        
    return {}
  
  async def calc_stream(self, cmd, feedback):
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
        

  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):    
    if self.RECEIVER_LAYER != None:
      QgsProject.instance().addMapLayer(self.RECEIVER_LAYER)
      QgsProject.instance().addMapLayer(self.TRIANGLE_LAYER)
    return {}

  def name(self):
    return 'receiverdelaunaygrid'

  def displayName(self):
    return self.tr("Delaunary grid")

  def group(self):
    return self.tr('Set receivers')

  def groupId(self):
    return 'receiver'

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return receiverdelaunaygrid()
