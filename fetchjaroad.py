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

import re

class fetchjaroad(fetchabstract):
  
  # UIs
  PARAMETERS = {  
    "FETCH_EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "TILEMAP_URL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Base-URL of the vector-tile map"),
        "defaultValue": "https://cyberjapandata.gsi.go.jp/xyz/experimental_rdcl/{z}/{x}/{y}.geojson"
      }
    },
    "TILEMAP_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjaroad","CRS of the vector-tile map"),
        "defaultValue": "EPSG:6668" # must be specified as string, because optional parameter cannot be set as QgsCoordinateReferenceSystem
      }
    },
    "TILEMAP_ZOOM": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Zoom level of the vector-tile map"),
        "type": QgsProcessingParameterNumber.Integer,
        "defaultValue": 16
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Road")
      }
    }
  }
  
  # initialization of the algorithm
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  # execution of the algorithm
  def processAlgorithm(self, parameters, context, feedback):    
    self.setFetchArea(parameters, context, feedback, QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setTileMapArgs(parameters, context, feedback, "Linestring")
    
    # fetch the data from vector map tile
    self.fetchFeaturesFromTile(parameters, context, feedback)
    road_raw = self.FETCH_FEATURE
    
    # post processing if there are features
    if road_raw.featureCount() > 0:
      
      # transform and dissolve
      road_transformed = self.transformToTargetCrs(parameters,context,feedback,road_raw)
      road_dissolve = self.dissolveFeatures(road_transformed)

      road_final = processing.run(
        "hrisk:initroad",{
          "INPUT": road_dissolve,
          "OVERWRITE": True,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_final.fields(), road_final.wkbType(), road_final.sourceCrs()
      )
      
      # set attributes values
      for ft in road_final.getFeatures():
        self.setDefaultTrafficVolumeJa(ft)
        sink.addFeature(ft)
      
    else:  
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_raw.fields(), road_raw.wkbType(), road_raw.sourceCrs()
      )
      
    return {"OUTPUT": dest_id}
  
  
  # default traffic volume in Ja
  def setDefaultTrafficVolumeJa(self, roadFeature):
    
    # return zero if the road width is not set
    if roadFeature["Width"] == None and roadFeature["rnkWidth"] == None:
      return
    
    # get road width
    if roadFeature["Width"] != None and roadFeature["Width"] != "":
      road_width = float(roadFeature["Width"])
    else:
      road_width_list = [float(s) for s in re.findall(r"\d+\.*\d*", roadFeature["rnkWidth"])]
      if len(road_width_list) == 1 and road_width_list[0] < 5.0:
        road_width_list.append(0.0)
      road_width = sum(road_width_list) / len(road_width_list)
    
    # compute the traffic volume
    if roadFeature["rdCtg"] == "高速自動車国道等":
      LV_d = -44.34 + 8.74 + (41.13 + 47.10) * road_width
      HV_d = -22.52 -464.23 + (6.51 + 43.30) * road_width
      LV_e = -166.53 -99.14 + (23.13 + 7.88) * road_width
      HV_e = -7.07 - 120.40 + (1.10 + 11.92) * road_width
      LV_n = -49.15 - 38.195 + (6.887 + 3.221) * road_width
      HV_n = -4.55 -124.43 + (0.99 + 11.40) * road_width
    elif roadFeature["rdCtg"] == "国道":
      LV_d = -44.34 + 183.62 + (41.13 + 3.19) * road_width
      HV_d = -22.52 + 12.60 + (6.51 + 3.26) * road_width
      LV_e = -166.53 +16.81 + (23.13 + 4.70) * road_width
      HV_e = -7.07 +4.93 + (1.10 + 0.96) * road_width
      LV_n = -49.15 +9.24 + (6.887 + 1.48) * road_width
      HV_n = -4.55 +4.88 + (0.99 + 1.29) * road_width
    elif roadFeature["rdCtg"] == "都道府県道" or roadFeature["rdCtg"] == "市区町村道等" :
      LV_d = -44.34 + 41.13 * road_width
      HV_d = -22.52 + 6.51 * road_width
      LV_e = -166.53 + 23.13 * road_width
      HV_e = -7.07 + 1.10 * road_width
      LV_n = -49.15 + 6.887 * road_width
      HV_n = -4.55 + 0.99 * road_width
    
    # check results
    roadFeature["LV_d"] = 0 if LV_d < 0 else round(LV_d, 1)
    roadFeature["HV_d"] = 0 if HV_d < 0 else round(HV_d, 1)
    roadFeature["LV_e"] = 0 if LV_e < 0 else round(LV_e, 1)
    roadFeature["HV_e"] = 0 if HV_e < 0 else round(HV_e, 1)
    roadFeature["LV_n"] = 0 if LV_n < 0 else round(LV_n, 1)
    roadFeature["HV_n"] = 0 if HV_n < 0 else round(HV_n, 1)
    
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Road centerline (Ja)")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjaroad()
