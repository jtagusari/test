from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProject,
  QgsVectorLayer,
  QgsProcessing,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterString,
  QgsProcessingParameterFolderDestination,
  QgsVectorFileWriter,
  QgsCoordinateTransformContext,
  QgsCategorizedSymbolRenderer,
  QgsRendererCategory,
  QgsFillSymbol,
  edit,
  QgsField
  )

from qgis import processing

import os
import sys
import re
import asyncio

class isosurface(QgsProcessingAlgorithm):
  PARAMETERS = { 
    "LEVEL_RESULT": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Sound-level results layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      }
    },
    "TRIANGLE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Triangle layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "ISO_CLASS": {
      "ui_func": QgsProcessingParameterString,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Separation of sound levels for isosurfaces (e.g. 35.0,40.0)"),
        "defaultValue": "35.0,40.0,45.0,50.0,55.0,60.0,65.0,70.0,75.0,80.0,200.0",
        "multiLine": False
      },
      "n_mdl": "isoClass"
    },    
    "SMOOTH_COEF": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Smoothing parameter (Bezier curve coefficient)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.0, "defaultValue": 1.0, "maxValue": 2.0
      },
      "n_mdl": "smoothCoefficient"
    }
  }
  
  OUTPUT = {
    "OUTPUT_DIRECTORY": {
      "ui_func": QgsProcessingParameterFolderDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("isosurface","Output directory" )
      }
    }
  }
  
  ISOSURFACE_LAYER = None
  OUTPUT_DIR       = None
    
  NoiseModelling_HOME = os.environ["NoiseModelling"]
  NoiseModelling_SCRIPT = os.path.join(os.path.dirname(__file__), "groovy", "isosurface.groovy")
  
    
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
    
    # folder where the files are saved
    self.OUTPUT_DIR = os.path.normpath(self.parameterAsOutputLayer(parameters, "OUTPUT_DIRECTORY", context))
    if not os.path.exists(self.OUTPUT_DIR):
      os.mkdir(self.OUTPUT_DIR)
              
    isosurface_geom_path = os.path.join(self.OUTPUT_DIR, "ISOSURFACE.geojson")
    level_geom_path = os.path.join(self.OUTPUT_DIR, "LEVEL_ISOSURFACE.geojson")
    triangle_geom_path = os.path.join(self.OUTPUT_DIR, "TRIANGLES.geojson")
    
    # spatial join level and receiver
    level_with_pk = processing.run(
      "native:renametablefield",
      {
        "INPUT": self.parameterAsVectorLayer(parameters, "LEVEL_RESULT", context),
        "FIELD": "IDRECEIVER",
        "NEW_NAME": "PK",
        "OUTPUT": "memory:level_with_pk"
      }
    )["OUTPUT"]
    # self.parameterAsVectorLayer(parameters, "LEVEL_RESULT", context)
    # with edit(level_with_pk):
    #   level_with_pk.addAttribute(QgsField("PK", QVariant.Int))
    #   level_with_pk.updateFields()
    #   for fid, ft in enumerate(level_with_pk.getFeatures()):
    #     ft["PK"] = fid
    #     level_with_pk.updateFeature(ft)
            
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "GeoJSON"
    QgsVectorFileWriter.writeAsVectorFormatV3(
      level_with_pk, level_geom_path, 
      QgsCoordinateTransformContext(), save_options
    )
    
    QgsVectorFileWriter.writeAsVectorFormatV3(
      self.parameterAsVectorLayer(parameters, "TRIANGLE", context), triangle_geom_path, 
      QgsCoordinateTransformContext(), save_options
    )
    
    iso_class = self.parameterAsString(parameters, "ISO_CLASS", context)
    smooth_coef = self.parameterAsDouble(parameters, "SMOOTH_COEF", context)
    
    # set arguments for wps
    wps_args = {
      "w": self.OUTPUT_DIR, 
      "s": self.NoiseModelling_SCRIPT,
      "exportPath": isosurface_geom_path,
      "resultGeomPath": level_geom_path,
      "triangleGeomPath": triangle_geom_path,
      "isoClass": iso_class,
      "smoothCoefficient": smooth_coef
    }    
    
    # set the command to execute
    cmd = os.path.join("bin","wps_scripts") + "".join([" -" + k + " " + str(v) for k, v in wps_args.items()])
    feedback.pushCommandInfo(cmd)   
    
    # execute groovy script using wps_scripts
    loop = asyncio.ProactorEventLoop()      
    loop.run_until_complete(
      self.calc_stream(cmd, feedback)
    )
    
    self.ISOSURFACE_LAYER = QgsVectorLayer(isosurface_geom_path, "isosurface")
        
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
    if self.ISOSURFACE_LAYER != None:
      
      isocategory = {}
      for ft in self.ISOSURFACE_LAYER.getFeatures():
        if isocategory.get(ft["ISOLABEL"]) == None:
          isovalue_list = [float(s) for s in re.findall(r"\d+\.*\d*", ft["ISOLABEL"])]
          isovalue_mean = sum(isovalue_list) / len(isovalue_list)
          (isolabel, isocolor) = self.getNoisemapLabelColor(isovalue_mean)
          isocategory[ft["ISOLABEL"]] = {
            "mean": isovalue_mean,
            "color": isocolor,
            "label": isolabel
          }
          
      isosurface_renderer = QgsCategorizedSymbolRenderer("ISOLABEL")
      for key, value in isocategory.items():
        isosurface_renderer.addCategory(
          QgsRendererCategory(
            key, 
            QgsFillSymbol.createSimple({"color":value.get("color")}), 
            key
          )
        )
          
      self.ISOSURFACE_LAYER.setRenderer(isosurface_renderer)
      self.ISOSURFACE_LAYER.triggerRepaint()

      QgsProject.instance().addMapLayer(self.ISOSURFACE_LAYER)
      
    return {}

  def getNoisemapLabelColor(self, level):
    if level < 35:
      label = "< 35 dB"
      color_rgb = "255,255,255,255"
    elif level < 40:
      label = "35 - 40 dB"
      color_rgb = "160,186,191,255"
    elif level < 45:
      label = "40 - 45 dB"
      color_rgb = "184,214,209,255"
    elif level < 50:
      label = "45 - 50 dB"
      color_rgb = "206,228,204,255"
    elif level < 55:
      label = "50 - 55 dB"
      color_rgb = "226,242,191,255"
    elif level < 60:
      label = "55 - 60 dB"
      color_rgb = "243,198,131,255"
    elif level < 65:
      label = "60 - 65 dB"
      color_rgb = "232,126,77,255"
    elif level < 70:
      label = "65 - 70 dB"
      color_rgb = "205,70,62,255"
    elif level < 75:
      label = "70 - 75 dB"
      color_rgb = "161,26,77,255"
    elif level < 80:
      label = "75 - 80 dB"
      color_rgb = "117,8,92,255"
    else:
      label = "> 80 dB"
      color_rgb = "67,10,74,255"
    return label, color_rgb
  
  def name(self):
    return 'isosurface'

  def displayName(self):
    return self.tr("Isosurface")

  def group(self):
    return self.tr('Noise prediction')

  def groupId(self):
    return 'noiseprediction'

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return isosurface()
