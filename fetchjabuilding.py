from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterCrs, 
  QgsProcessingParameterString,
  QgsProcessingParameterNumber
  )
from qgis import processing

from .fetchabstract import fetchabstract

class fetchjabuilding(fetchabstract):
  
  # UIs
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "MAPTILE_URL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Base-URL of the vector-tile map"),
        "defaultValue": "https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{z}/{x}/{y}.pbf|layername=building|geometrytype=Polygon"
      }
    },
    "MAPTILE_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","CRS of the vector-tile map"),        
        "defaultValue": "EPSG:3857" # must be specified as string, because optional parameter cannot be set as QgsCoordinateReferenceSystem
      }
    },
    "MAPTILE_ZOOM": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Zoom level of the vector-tile map"),
        "type": QgsProcessingParameterNumber.Integer,
        "defaultValue": 16
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjabuilding","Building")
      }
    }
  }  
  
  # initialization of the algorithm
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
    
  
  # modification of the feature obtained from the map tile
  def modifyFeaturesFromTile(self, fts, z, tx, ty):    
    if fts.featureCount() <= 0:
      return(fts)
    else:
      # constants
      EQUATOR_M = 40075016.68557849
      N_PIXELS_IN_GSI_VTILE = 4096
      n_pixels_all = N_PIXELS_IN_GSI_VTILE * 2 ** z
      meter_per_tile  = EQUATOR_M / 2 ** z
      meter_per_pixel = EQUATOR_M / n_pixels_all
      
      # affine transformation to obtain x and y for a given CRS
      affine_parameters = {        
        "INPUT": fts,
        "DELTA_X":    tx    * meter_per_tile - EQUATOR_M / 2,
        "DELTA_Y": - (ty+1) * meter_per_tile + EQUATOR_M / 2,
        "SCALE_X": meter_per_pixel,
        "SCALE_Y": meter_per_pixel,
        "OUTPUT": "TEMPORARY_OUTPUT"
      }        
      fts_modified = processing.run("native:affinetransform", affine_parameters)["OUTPUT"]
      return(fts_modified)
        
  # execution of the algorithm
  def processAlgorithm(self, parameters, context, feedback):    
    
    self.setCalcArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setMapTileMeta(parameters, context, feedback, "Polygon")
    
    # fetch the data from vector map tile
    bldg_raw = self.fetchFeaturesFromTile(parameters, context, feedback)
    
    # post processing if there are any features
    if bldg_raw.featureCount() > 0:
      
      # transform
      bldg_transformed = self.transformToTargetCrs(parameters,context,feedback,bldg_raw)
      
      # snap geometry
      bldg_snap = processing.run(
        "native:snapgeometries", 
        {
          "INPUT": bldg_transformed,
          "REFERENCE_LAYER": bldg_transformed,
          "TOLERANCE": 0.1,
          "BEHAVIOR": 0,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # dissolve
      bldg_dissolve = self.dissolveFeatures(bldg_snap)
            
      bldg_final = processing.run(
        "hrisk:initbuilding",{
          "INPUT": bldg_dissolve,
          "OVERWRITE": True,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        bldg_final.fields(), bldg_final.wkbType(), bldg_final.sourceCrs()
      )
      
      sink.addFeatures(bldg_final.getFeatures())
      
      return {"OUTPUT": dest_id}
      
    else:  
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        bldg_raw.fields(), bldg_raw.wkbType(), bldg_raw.sourceCrs()
      )
      
    return {"OUTPUT": dest_id}
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Buildings (Ja)")
  
  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjabuilding()
