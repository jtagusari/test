from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP
  )
from qgis.core import (
  QgsProject,
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterString,
  QgsProcessingParameterFeatureSink,
  QgsCategorizedSymbolRenderer,
  QgsRendererCategory,
  QgsFillSymbol,
  QgsProcessingParameterField,
  QgsFeatureRequest,
  QgsProcessingLayerPostProcessorInterface
  )

from qgis import processing
from .algabstract import algabstract

import os
import re

class isosurface(algabstract):
  PARAMETERS = { 
    "LEVEL_RESULT": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Sound level layer"),
        "types": [QgsProcessing.TypeVectorPoint]
      }
    },
    "LEVEL_RID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Receiver ID Field of the Sound level layer"),
        "parentLayerParameterName": "LEVEL_RESULT",
        "defaultValue": "IDRECEIVER"
      }
    },
    "TRIANGLES": { # Note: the name "TRIANGLES" should not be changed
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Triangle layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "triangleGeomPath",
      "save_layer_get_path": True
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
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("isosurface","Isosurface")
      }
    }
  }
        
  def initAlgorithm(self, config):
    self.initParameters() 

  def processAlgorithm(self, parameters, context, feedback):
    self.initNoiseModellingPath("isosurface.groovy")
    self.addNoiseModellingPath(
      {
        "LEVEL_PATH": os.path.join(self.NOISEMODELLING["TEMP_DIR"], "LEVEL_RESULT.geojson"),
        "ISOSURFACE_PATH": os.path.join(self.NOISEMODELLING["TEMP_DIR"], "CONTOURLNG_NOISE_MAP.geojson")
        }
      )
    
    processing.run(
      "native:renametablefield",
      {
        "INPUT": self.parameterAsSource(parameters, "LEVEL_RESULT", context).materialize(QgsFeatureRequest(), feedback),
        "FIELD": self.parameterAsFields(parameters, "LEVEL_RID", context)[0],
        "NEW_NAME": "PK",
        "OUTPUT": self.NOISEMODELLING["LEVEL_PATH"]
      }
    )
    
    self.initNoiseModellingArg(parameters, context, feedback)
    self.addNoiseModellingArg({"resultGeomPath": self.NOISEMODELLING["LEVEL_PATH"]})
    
    feedback.pushCommandInfo(self.NOISEMODELLING["CMD"])   
    
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)
    
    # import the result    
    dest_id = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT", self.NOISEMODELLING["ISOSURFACE_PATH"])
    
    return {"OUTPUT": dest_id}          

  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):    
    
    isosurface_path = list(context.layersToLoadOnCompletion().keys())[0]
    global isosurface_postprocessor
    isosurface_postprocessor = isosurfacePostProcessor()    
    context.layerToLoadOnCompletionDetails(isosurface_path).setPostProcessor(isosurface_postprocessor)
    return {}

  
  def displayName(self):
    return self.tr("Isosurface")

  def group(self):
    return self.tr('Predict sound level')

  def groupId(self):
    return 'soundlevel'

  def createInstance(self):
    return isosurface()


class isosurfacePostProcessor (QgsProcessingLayerPostProcessorInterface):
  
  def postProcessLayer(self, layer, context, feedback):
    
    # find the vector layer
    root = QgsProject.instance().layerTreeRoot()
    vl = root.findLayer(layer.id())
    
    col_map = {
      "< 35 dB":    {"lower": -999, "upper":  35, "color": "255,255,255, 100"},
      "35 - 40 dB": {"lower":   35, "upper":  40, "color": "160,186,191, 100"},
      "40 - 45 dB": {"lower":   40, "upper":  45, "color": "184,214,209, 100"},
      "45 - 50 dB": {"lower":   45, "upper":  50, "color": "206,228,204, 100"},
      "50 - 55 dB": {"lower":   50, "upper":  55, "color": "226,242,191, 100"},
      "55 - 60 dB": {"lower":   55, "upper":  60, "color": "243,198,131, 100"},
      "60 - 65 dB": {"lower":   60, "upper":  65, "color": "232,126, 77, 100"},
      "65 - 70 dB": {"lower":   65, "upper":  70, "color": "205, 70, 62, 100"},
      "70 - 75 dB": {"lower":   70, "upper":  75, "color": "161, 26, 77, 100"},
      "75 - 80 dB": {"lower":   75, "upper":  80, "color": "117,  8, 92, 100"},
      "> 80 dB":    {"lower":   80, "upper": 999, "color": " 67, 10, 74, 100"}
    }
    
    col_dict = {}
    for ft in layer.getFeatures():
      if not ft["ISOLABEL"] in col_dict.keys():
        isovalue_list = [float(s) for s in re.findall(r"\d+\.*\d*", ft["ISOLABEL"])]
        if re.match(r"<", ft["ISOLABEL"]) != None:
          isovalue_list.append(-999)
        isovalue_mean = sum(isovalue_list) / len(isovalue_list)
        for col_map_item in col_map.values():
          if isovalue_mean >= col_map_item["lower"] and isovalue_mean < col_map_item["upper"]:
            col_dict[ft["ISOLABEL"]] = col_map_item
    
    # set renderer
    renderer = QgsCategorizedSymbolRenderer("ISOLABEL")
                
    # set symbols
    for key, value in col_dict.items():
      renderer.addCategory(
        QgsRendererCategory(
          key, QgsFillSymbol.createSimple({"color":value.get("color")}), key + " dB"
        )
      )
    # apply renderer
    vl.layer().setRenderer(renderer)
    vl.layer().triggerRepaint()   
    