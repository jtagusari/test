from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterCrs,
  QgsProcessingParameterDistance,
  QgsProcessingParameterFeatureSink
  )
from qgis import processing

from .fetchabstract import fetchabstract

import re

class fetchjaroad(fetchabstract):
  
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Extent of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Target CRS")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Buffer of the calculation area based on Target CRS"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjaroad","Output")
      }
    }
  }
  DEFAULT_SPD = {
    "LV_D": 60,
    "LV_E": 60,
    "LV_N": 60,
    "HV_D": 60,
    "HV_E": 60,
    "HV_N": 60
  }
  DEFEALT_PVMT = "DEF" # reference, without correction
    
    
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  def processAlgorithm(self, parameters, context, feedback):
    self.setCalcArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setMapTileMeta(
      "https://cyberjapandata.gsi.go.jp/xyz/experimental_rdcl/{z}/{x}/{y}.geojson",
      QgsCoordinateReferenceSystem("EPSG:6668"),
      "Linestring", 16
    )
    
    road_raw = self.fetchFeaturesFromTile()
    
    # post processing if there are features
    if road_raw is not None and road_raw.featureCount() > 0:
      
      road_transformed = self.transformToTargetCrs(parameters,context,feedback,road_raw)
      road_dissolve = self.dissolveFeatures(road_transformed)

      # Set road traffic fields
      road_with_fields = processing.run(
        "hrisk:sourceroadtrafficfield",
        {
          "INPUT": road_dissolve,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      road_layer_final = road_with_fields
      
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_layer_final.fields(), road_layer_final.wkbType(), road_layer_final.sourceCrs()
      )
      
      for ft in road_layer_final.getFeatures():
        (lv_d, hv_d, lv_e, hv_e, lv_n, hv_n) = self.cmptDefaultTrafficVolumeJa(ft)
        ft["lv_d"] = lv_d
        ft["hv_d"] = hv_d
        ft["lv_e"] = lv_e
        ft["hv_e"] = hv_e
        ft["lv_n"] = lv_n
        ft["hv_n"] = hv_n
        ft["lv_spd_d"] = self.DEFAULT_SPD["LV_D"]
        ft["lv_spd_e"] = self.DEFAULT_SPD["LV_E"]
        ft["lv_spd_n"] = self.DEFAULT_SPD["LV_N"]
        ft["hv_spd_d"] = self.DEFAULT_SPD["HV_D"]
        ft["hv_spd_e"] = self.DEFAULT_SPD["HV_E"]
        ft["hv_spd_n"] = self.DEFAULT_SPD["HV_N"]
        ft["pvmt"] = self.DEFEALT_PVMT
        sink.addFeature(ft)
      
    else:  
      # set sink and add features with values
      (sink, dest_id) = self.parameterAsSink(
        parameters, "OUTPUT", context,
        road_raw.fields(), road_raw.wkbType(), road_raw.sourceCrs()
      )
      
    return {"OUTPUT": dest_id}
  
  
  def cmptDefaultTrafficVolumeJa(self, roadFeature):
    
    # return zero if the road width is not set
    if roadFeature["Width"] == None and roadFeature["rnkWidth"] == None:
      return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
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
      lv_d = -44.34 + 8.74 + (41.13 + 47.10) * road_width
      hv_d = -22.52 -464.23 + (6.51 + 43.30) * road_width
      lv_e = -166.53 -99.14 + (23.13 + 7.88) * road_width
      hv_e = -7.07 - 120.40 + (1.10 + 11.92) * road_width
      lv_n = -49.15 - 38.195 + (6.887 + 3.221) * road_width
      hv_n = -4.55 -124.43 + (0.99 + 11.40) * road_width
    elif roadFeature["rdCtg"] == "国道":
      lv_d = -44.34 + 183.62 + (41.13 + 3.19) * road_width
      hv_d = -22.52 + 12.60 + (6.51 + 3.26) * road_width
      lv_e = -166.53 +16.81 + (23.13 + 4.70) * road_width
      hv_e = -7.07 +4.93 + (1.10 + 0.96) * road_width
      lv_n = -49.15 +9.24 + (6.887 + 1.48) * road_width
      hv_n = -4.55 +4.88 + (0.99 + 1.29) * road_width
    elif roadFeature["rdCtg"] == "都道府県道" or roadFeature["rdCtg"] == "市区町村道等" :
      lv_d = -44.34 + 41.13 * road_width
      hv_d = -22.52 + 6.51 * road_width
      lv_e = -166.53 + 23.13 * road_width
      hv_e = -7.07 + 1.10 * road_width
      lv_n = -49.15 + 6.887 * road_width
      hv_n = -4.55 + 0.99 * road_width
    
    # check results
    lv_d = 0 if lv_d < 0 else round(lv_d, 1)
    hv_d = 0 if hv_d < 0 else round(hv_d, 1)
    lv_e = 0 if lv_e < 0 else round(lv_e, 1)
    hv_e = 0 if hv_e < 0 else round(hv_e, 1)
    lv_n = 0 if lv_n < 0 else round(lv_n, 1)
    hv_n = 0 if hv_n < 0 else round(hv_n, 1)
    
    return (lv_d, hv_d, lv_e, hv_e, lv_n, hv_n)
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Road centerlines")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjaroad()
