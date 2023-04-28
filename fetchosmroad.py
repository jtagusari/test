from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsVectorLayer,
  QgsProcessingParameterExtent,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterCrs, 
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterString,
  QgsRectangle
  )
from qgis import processing

import re
import math
import itertools

class fetchosmroad(QgsProcessingAlgorithm):
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Extent, of which center is used as the center of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Target CRS")
      }
    },
    "LONG_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Width of the longitude of the calculation area (degree)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 0.0125, "maxValue": 1.0
      }
    },
    "LAT_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Width of the latitude of the calculation area (degree)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.005, "defaultValue": 0.0083, "maxValue": 1.0
      }
    },
    "TIMEOUT": {
      "ui_func": QgsProcessingParameterNumber,
      "advanced": True,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Time-out limit for fetching osm data (second)"),
        "type": QgsProcessingParameterNumber.Integer,
        "minValue": 1, "defaultValue": 25, "maxValue": 60
      }
    },
    "SERVER": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Time-out limit for fetching osm data (second)"),
        "type": QgsProcessingParameterString,
        "defaultValue": "https://lz4.overpass-api.de/api/interpreter"
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchosmroad","Roads" )
      }
    }
  }
      
  LV_SPD_D_DEFAULT = 60
  LV_SPD_E_DEFAULT = 60
  LV_SPD_N_DEFAULT = 60
  HV_SPD_D_DEFAULT = 60
  HV_SPD_E_DEFAULT = 60
  HV_SPD_N_DEFAULT = 60
  PVMT_DEFAULT = "DEF" # reference, without correction
    
    
  def initAlgorithm(self, config):
    
    for key, value in self.PARAMETERS.items():
      args = value.get("ui_args")
      args["name"] = key
      args["description"] = self.tr(args["description"])
              
      ui = value.get("ui_func")(**args)
      
      if value.get("advanced") != None and value.get("advanced") == True:
        ui.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        
      self.addParameter(ui)  


  def cmptRectangle(self, extent_c, longwidth, latwidth):
    (lng_c, lat_c) = (extent_c.center().x(), extent_c.center().y())
    (lng_min , lng_max, lat_min, lat_max) = (
      lng_c - longwidth / 2.0,
      lng_c + longwidth / 2.0,
      lat_c - latwidth / 2.0,
      lat_c + latwidth / 2.0
    )
    return QgsRectangle(lng_min, lat_min, lng_max, lat_max)  
  
  def processAlgorithm(self, parameters, context, feedback):
    import ptvsd
    ptvsd.debug_this_thread()
    
    extent_input = self.parameterAsExtent(parameters, "EXTENT", context, QgsCoordinateReferenceSystem("EPSG:6668"))
    target_crs_input = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    longwidth_input = self.parameterAsDouble(parameters, "LONG_WIDTH", context)
    latwidth_input = self.parameterAsDouble(parameters, "LAT_WIDTH", context)
    server_input = self.parameterAsString(parameters, "SERVER", context)
    timeout_input = self.parameterAsInt(parameters, "TIMEOUT", context)
    
    rec_lnglat = self.cmptRectangle(extent_input, longwidth_input, latwidth_input)
    
    
    # run OSM query and fetch features
    road_layer_raw = processing.run(
      "quickosm:downloadosmdataextentquery", 
      {
        "EXTENT": extent_input,
        "KEY": "highway",
        "VALUE": "trunk",
        "SERVER": server_input,
        "TIMEOUT": timeout_input,
        "FILE": "TEMPORARY_OUTPUT"
      }
    )["FILE"]
    
    # post processing if there are features
    if road_layer_raw.featureCount() > 0:
      
      # CRS transform
      road_transform = processing.run(
        "native:reprojectlayer", 
        {
          "INPUT": road_layer_raw,
          "TARGET_CRS": target_crs_input,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]      
      
      # Dissolve
      road_dissolve = processing.run(
        "native:dissolve", 
        {
          "INPUT": road_transform,
          "FIELD": road_transform.fields().names(),
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # Multipart to Single parts
      road_single = processing.run(
        "native:multiparttosingleparts", 
        {
          "INPUT": road_dissolve,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # Set road traffic fields
      road_with_fields = processing.run(
        "hrisk:sourceroadtrafficfield",
        {
          "INPUT": road_single,
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
        ft["lv_spd_d"] = self.LV_SPD_D_DEFAULT
        ft["lv_spd_e"] = self.LV_SPD_E_DEFAULT
        ft["lv_spd_n"] = self.LV_SPD_N_DEFAULT
        ft["hv_spd_d"] = self.HV_SPD_D_DEFAULT
        ft["hv_spd_e"] = self.HV_SPD_E_DEFAULT
        ft["hv_spd_n"] = self.HV_SPD_N_DEFAULT
        ft["pvmt"] = self.PVMT_DEFAULT
        sink.addFeature(ft)
      
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
    
  def cmptTileXY(self, z, lng, lat):
    return (
      int(2**(z+7) * (lng / 180 + 1) / 256),
      int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
    )
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def name(self):
    return 'fetchosmroad'

  def displayName(self):
    return self.tr("Road centerlines")

  def group(self):
    return self.tr('Fetch geometries (OSM)')

  def groupId(self):
    return 'fetchosmgeometry'

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return fetchosmroad()
