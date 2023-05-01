from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP,QVariant)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterCrs,
  QgsProcessingParameterDistance,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterString,
  QgsProcessingParameterNumber
  )
from qgis import processing

from .fetchabstract import fetchabstract

class fetchosmbuilding(fetchabstract):
  
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Extent of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Target CRS")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Buffer of the calculation area based on Target CRS"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "OSM_URL": {
      "ui_func": QgsProcessingParameterString,
      "advanced": True,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","URL of the OpenStreetMap"),
        "defaultValue": "https://lz4.overpass-api.de/api/interpreter"
      }
    },
    "OSM_KEY": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Key of OpenStreetMap for buildings. By default, 'building'"),
        "defaultValue": "building",
        "optional": True
      }
    },
    "OSM_VALUE": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Value of OpenStreetMap for buildings. By default, '' (all buildings)"),
        "defaultValue": "",
        "optional": True
      }
    },
    "OSM_TIMEOUT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Value of OpenStreetMap for roads. By default, '' (all values)"),
        "type": QgsProcessingParameterNumber.Double,
        "defaultValue": 25,
        "optional": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmbuilding","Output")
      }
    }
  }
    
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  def processAlgorithm(self, parameters, context, feedback):
    self.setCalcArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setOsmMeta(parameters, context, feedback, geom_type="Polygon")
    
    bldg_raw = self.fetchFeaturesFromOsm(context, feedback)
    
    # post processing if there are features
    if bldg_raw is not None and bldg_raw.featureCount() > 0:
      
      bldg_transformed = self.transformToTargetCrs(parameters,context,feedback,bldg_raw)
      bldg_dissolve = self.dissolveFeatures(bldg_transformed)
      
      bldg_final = processing.run(
        "hrisk:initbuilding",{
          "INPUT": bldg_dissolve,
          "OVERWRITE_MODE": 0,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        bldg_final.fields(), bldg_final.wkbType(), bldg_final.sourceCrs()
      )
      
      sink.addFeatures(bldg_final.getFeatures())
            
    else:  
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        bldg_raw.fields(), bldg_raw.wkbType(), bldg_raw.sourceCrs()
      )
      
    return {"OUTPUT": dest_id}

  def displayName(self):
    return self.tr("Buildings")

  def group(self):
    return self.tr('Fetch geometries (OSM)')

  def groupId(self):
    return 'fetchosmgeometry'

  def createInstance(self):
    return fetchosmbuilding()
