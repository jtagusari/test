from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
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
  QgsProcessingLayerPostProcessorInterface,
  QgsVectorLayer
  )

from qgis import processing
from .algabstract import algabstract
from .noisecolor import getNoiseColorMap

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
    "LEVEL_LID": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("isosurface","Sound-level Field of the Sound level layer"),
        "parentLayerParameterName": "LEVEL_RESULT",
        "defaultValue": "LAEQ"
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
        
  FIELDS_LEVEL = {    
    "PL":   {"TYPE": QVariant.Int, "DEFAULT_VALUE": None},
    "LAEQ": {"TYPE": QVariant.Double, "DEFAULT_VALUE": None}
  }
  def initAlgorithm(self, config):
    self.initParameters() 

  def processAlgorithm(self, parameters, context, feedback):
    self.initNoiseModellingPath(
      {
        "GROOVY_SCRIPT": os.path.join(os.path.dirname(__file__), "noisemodelling","hriskscript", "isosurface.groovy"),
        "LEVEL_RESULT": os.path.join("%nmtmp%", "LEVEL_RESULT.geojson"),
        "ISOSURFACE": os.path.join("%nmtmp%", "CONTOURING_NOISE_MAP.geojson")
        }
      )
    
    spl_input = self.parameterAsSource(parameters, "LEVEL_RESULT", context).materialize(QgsFeatureRequest(), feedback)
    pk_field = self.parameterAsFields(parameters, "LEVEL_RID", context)[0]
    level_field = self.parameterAsFields(parameters, "LEVEL_LID", context)[0]
    spl_ext = processing.run(
      "native:retainfields",
      {
        "INPUT": spl_input,
        "FIELDS": [pk_field, level_field],
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    
    spl_pk = processing.run(
      "native:renametablefield",
      {
        "INPUT": spl_ext,
        "FIELD": self.parameterAsFields(parameters, "LEVEL_RID", context)[0],
        "NEW_NAME": "PK",
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    
    spl_laeq = processing.run(
      "native:renametablefield",
      {
        "INPUT": spl_pk,
        "FIELD": self.parameterAsFields(parameters, "LEVEL_LID", context)[0],
        "NEW_NAME": "LAEQ",
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    self.saveVectorLayer(spl_laeq, self.NOISEMODELLING["LEVEL_RESULT"])
    
    self.initNoiseModellingArg(parameters, context, feedback)
    self.addNoiseModellingArg({"resultGeomPath": self.NOISEMODELLING["LEVEL_RESULT"]})
        
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)
    
    # import the result    
    dest_id = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT", self.NOISEMODELLING["ISOSURFACE"])
    
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
    
    col_map = getNoiseColorMap(100)
    
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
    