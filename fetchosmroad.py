from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
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

class fetchosmroad(fetchabstract):
  
  PARAMETERS = {  
    "FETCH_EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "OSM_URL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Query URL of the OpenStreetMap"),
        "defaultValue": "https://lz4.overpass-api.de/api/interpreter"
      }
    },
    "OSM_KEY": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Key of OpenStreetMap for roads. By default, 'highway'"),
        "defaultValue": "highway",
        "optional": True
      }
    },
    "OSM_VALUE": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Value of OpenStreetMap for roads. By default, '' (all values)"),
        "defaultValue": "",
        "optional": True
      }
    },
    "OSM_TIMEOUT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Value of OpenStreetMap for roads. By default, '' (all values)"),
        "type": QgsProcessingParameterNumber.Double,
        "defaultValue": 25,
        "optional": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Road")
      }
    }
  }
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  def processAlgorithm(self, parameters, context, feedback):
    self.setFetchArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:4326"))
    self.setOsmArgs(parameters, context, feedback, geom_type="Linestring")
    
    self.fetchFeaturesFromOsm(parameters, context, feedback)
    road_raw = self.FETCH_FEATURE
    
    # post processing if there are features
    if road_raw is not None and road_raw.featureCount() > 0:
      
      road_transformed = self.transformToTargetCrs(parameters,context,feedback,road_raw)
      road_dissolve = self.dissolveFeatures(road_transformed)

      # Set road traffic fields
      road_final = processing.run(
        "hrisk:initroad",{
          "INPUT": road_dissolve,
          "OVERWRITE_MODE": 0,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_final.fields(), road_final.wkbType(), road_final.sourceCrs()
      )
      
      sink.addFeatures(road_final.getFeatures())
      
    else:  
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_raw.fields(), road_raw.wkbType(), road_raw.sourceCrs()
      )
      
    return {"OUTPUT": dest_id}
  

  def displayName(self):
    return self.tr("Road centerline (OSM)")

  def group(self):
    return self.tr('Fetch geometries')

  def groupId(self):
    return 'fetchgeometry'

  def createInstance(self):
    return fetchosmroad()
