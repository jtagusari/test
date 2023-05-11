from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsProcessingParameterCrs, 
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterRasterDestination,
  QgsProperty,
  QgsProcessingParameterString,
  QgsProcessingParameterNumber
  )
from qgis import processing

from .fetchabstract import fetchabstract

class fetchjadem(fetchabstract):
  
  PARAMETERS = {  
    "FETCH_EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjadem","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjadem","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjadem","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "TILEMAP_URL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjadem","Base-URL of the vector-tile map"),
        "defaultValue": "https://cyberjapandata.gsi.go.jp/xyz/experimental_dem10b/{z}/{x}/{y}.geojson"
      }
    },
    "TILEMAP_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjadem","CRS of the vector-tile map"),        
        "defaultValue": "EPSG:6668" # must be specified as string, because optional parameter cannot be set as QgsCoordinateReferenceSystem
      }
    },
    "TILEMAP_ZOOM": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjadem","Zoom level of the vector-tile map"),
        "type": QgsProcessingParameterNumber.Integer,
        "defaultValue": 18
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjadem","Elevation point (DEM)")
      }
    },
    "OUTPUT_RASTER": {
      "ui_func": QgsProcessingParameterRasterDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjadem","Elevation raster (DEM)" )
      }
    }
  }  
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()

  def processAlgorithm(self, parameters, context, feedback):
    
    self.setFetchArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setTileMapArgs(parameters, context, feedback, "Point")
    
    dem_raw = self.fetchFeaturesFromTile(parameters, context, feedback)
    
    # CRS transform    
    dem_transformed = self.transformToTargetCrs(parameters,context,feedback,dem_raw)
    
    # set z value
    dem_z = processing.run(
      "native:setzvalue",
      {
        "INPUT": dem_transformed,
        "Z_VALUE": QgsProperty.fromExpression('"alti"'),
        "OUTPUT": "memory:dem"
      }
    )["OUTPUT"]
    
    # substitute self constant with the fetched vector layer
    dem_final = dem_z    
    
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context,
      dem_final.fields(), dem_final.wkbType(), dem_final.sourceCrs()
    )
    sink.addFeatures(dem_final.getFeatures())
    
    dem_raster = processing.run(
      "gdal:rasterize",
      {
        "INPUT": dem_raw,
        "FIELD": "alti",
        "UNITS": 1,
        "WIDTH": 0.4 / 3600.0,
        "HEIGHT": 0.4 / 3600.0,
        "DATA_TYPE": 2,
        "INIT": 0,
        "OUTPUT": self.parameterAsOutputLayer(parameters, "OUTPUT_RASTER", context)
      }
    )["OUTPUT"]
    
    return {"OUTPUT": dest_id, "OUTPUT_RASTER": dem_raster}   
    
  
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Elevation points (Ja)")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjadem()
