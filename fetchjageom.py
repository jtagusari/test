from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProject,
  QgsCoordinateReferenceSystem,
  QgsVectorLayer,
  QgsProcessing,
  QgsProcessingParameterExtent,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterCrs, 
  QgsProcessingParameterBoolean,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFolderDestination,
  QgsRectangle,
  QgsField,
  QgsFields,
  QgsFeature,
  QgsGeometry,
  edit,
  QgsPoint,
  QgsFeature,
  QgsRasterLayer
  )
from qgis import processing

import os
import re
import math
import itertools
import urllib.request
import json

class fetchjageom(QgsProcessingAlgorithm):
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjageom","Extent, of which center is used as the center of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Target CRS")
      }
    },
    "LONG_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Width of the longitude of the calculation area (degree)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 0.0125, "maxValue": 1.0
      }
    },
    "LAT_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Width of the latitude of the calculation area (degree)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.005, "defaultValue": 0.0083, "maxValue": 1.0
      }
    },
    "FENCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjageom","Fence layer, within which receivers are generated"),
        "types": [QgsProcessing.TypeVectorPolygon],
        "optional": True,
        "defaultValue": None
      }
    },    
    "DELTA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Distance between receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 10.0, "maxValue": 100.0
      },
      "n_mdl": "delta"
    },
    "HEIGHT": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Height of receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 4.0, "maxValue": 100.0
      },
      "n_mdl": "height"
    },    
    "MAX_PROP_DIST": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum propagation distance between sources and receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 500.0, "maxValue": 2000.0
      },
      "n_mdl": "maxPropDist"
    },
    "ROAD_WIDTH": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Road width (m), where no receivers will be set closer than it"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 2.0, "maxValue": 20.0
      },
      "n_mdl": "roadWidth"
    },
    "MAX_AREA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum trianglar area (m2)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 10.0, "defaultValue": 500.0, "maxValue": 10000.0
      },
      "n_mdl": "maxArea"
    },
    "ISO_SURFACE": {
      "advanced": True,
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Whether isosurfaces will be visible at the location of buildings"),
        "defaultValue": False
      },
      "n_mdl": "isoSurfaceInBuildings"
    }
  }
  
  OUTPUT = {
    "OUTPUT_DIRECTORY": {
      "ui_func": QgsProcessingParameterFolderDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Output directory" )
      }
    }
  }
  
  ROAD_LAYER     = None
  DEM_LAYER      = None
  BUILDING_LAYER = None 
  RECEIVER_LAYER = None
  FENCE_LAYER    = None
  OUTPUT_DIR     = None
  CALCAREA_LAYER = None
  
  EQUATOR_M = 40075016.68557849
  N_PIXELS_IN_GSI_VTILE = 4096
  
  BUILDING_HEIGHT_DEFAULT = 6.0
  
  LV_SPD_D_DEFAULT = 60
  LV_SPD_E_DEFAULT = 60
  LV_SPD_N_DEFAULT = 60
  HV_SPD_D_DEFAULT = 60
  HV_SPD_E_DEFAULT = 60
  HV_SPD_N_DEFAULT = 60
  PVMT_DEFAULT = "DEF" # reference, without correction
    
    
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
    
    feedback.pushInfo(self.tr("Configurations"))
    feedback.setProgress(0)    
    
    extent_input = self.parameterAsExtent(parameters, "EXTENT", context, QgsCoordinateReferenceSystem("EPSG:6668"))
    target_crs_input = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    longwidth_input = self.parameterAsDouble(parameters, "LONG_WIDTH", context)
    latwidth_input = self.parameterAsDouble(parameters, "LAT_WIDTH", context)

    
    (lng_c, lat_c) = (extent_input.center().x(), extent_input.center().y())
    (lng_min , lng_max, lat_min, lat_max) = (
      lng_c - longwidth_input / 2.0,
      lng_c + longwidth_input / 2.0,
      lat_c - latwidth_input / 2.0,
      lat_c + latwidth_input / 2.0
    )
    
    extent_lnglat = QgsRectangle(lng_min, lat_min, lng_max, lat_max)  
                   
    # folder where the files are saved
    self.OUTPUT_DIR = os.path.normpath(self.parameterAsOutputLayer(parameters, "OUTPUT_DIRECTORY", context))
    if not os.path.exists(self.OUTPUT_DIR):
      os.mkdir(self.OUTPUT_DIR)
    
    # set calculation area
    calcarea_layer = QgsVectorLayer("Polygon?crs=EPSG:6668", "calculation_area", "memory")
    feat = QgsFeature()
    feat.setGeometry(QgsGeometry.fromRect(extent_lnglat))
    calcarea_layer.dataProvider().addFeatures([feat])
    
    self.CALCAREA_LAYER = processing.run(
      "native:reprojectlayer",
      {
        "INPUT": calcarea_layer,
        "TARGET_CRS": target_crs_input,
        "OUTPUT": "memory:calculation_area"
      }
    )["OUTPUT"]

    feedback.setProgress(5)    
    
    self.setPopulationLayer(extent_lnglat, target_crs_input)
    
    feedback.pushInfo(self.tr("Setting a layer for roads"))
    # self.setRoadLayer(extent_lnglat, target_crs_input)        
    feedback.setProgress(25)
    
    feedback.pushInfo(self.tr("Setting a layer for buildings"))
    # self.setBuildingLayer(extent_lnglat, target_crs_input)
    feedback.setProgress(50)

    feedback.pushInfo(self.tr("Setting a layer for receivers"))
    # self.setReceiverLayer(parameters, context, feedback)
    feedback.setProgress(75)
    
    feedback.pushInfo(self.tr("Setting a layer for elevation points"))
    # self.setDemLayer(extent_lnglat, target_crs_input)    
    feedback.setProgress(100)
    
    return {}
  
  
  def cmptDefaultTrafficVolumeJa(self, roadFeature):
    
    if roadFeature["Width"] != "":
      road_width = roadFeature["Width"]
    else:
      road_width_list = [float(s) for s in re.findall(r"\d+\.*\d*", roadFeature["rnkWidth"])]
      road_width = sum(road_width_list) / len(road_width_list)
    
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
    
    lv_d = 0 if lv_d < 0 else lv_d
    hv_d = 0 if hv_d < 0 else hv_d
    lv_e = 0 if lv_e < 0 else lv_e
    hv_e = 0 if hv_e < 0 else hv_e
    lv_n = 0 if lv_n < 0 else lv_n
    hv_n = 0 if hv_n < 0 else hv_n
    
    return (lv_d, hv_d, lv_e, hv_e, lv_n, hv_n)
  
  def setRoadLayer(self, extent_lnglat, target_crs):
    
    # initialize road layer (and data provider) to which vector features added
    road_layer = QgsVectorLayer("LineString?crs=EPSG:6668&index=yes",baseName = "road_from_web", providerLib = "memory")
    road_pr = road_layer.dataProvider()
    
    # fetch vector features from GSI
    
    # set zoom level, tile x and y
    z = 16 #fixed zoom level of 16
    (tx_min, ty_min) = self.cmptTileXY(z, extent_lnglat.xMinimum(),extent_lnglat.yMaximum())
    (tx_max, ty_max) = self.cmptTileXY(z, extent_lnglat.xMaximum(),extent_lnglat.yMinimum())
    
    # fetch features for each tx and ty
    for tx, ty in itertools.product(list(range(tx_min, tx_max+1)), list(range(ty_min,ty_max+1))):
      uri = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_rdcl/{z}/{tx}/{ty}.geojson"
      vlayer = QgsVectorLayer(uri, "road", "ogr")
      
      if vlayer.featureCount() > 0:
        for ft in vlayer.getFeatures():
          # set the fields of roads if it is not set 
          if road_layer.fields().count() == 0:
            road_pr.addAttributes([ft.fields().at(idx) for idx in range(ft.fields().count())])
            road_layer.updateFields()
          road_pr.addFeatures([ft])
    
    # post processing if there are features
    if road_layer.featureCount() > 0:
      
      # CRS transform
      road_transform = processing.run(
        "native:reprojectlayer", 
        {
          "INPUT": road_layer,
          "TARGET_CRS": target_crs,
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
          "OUTPUT": "memory:road"
        }
      )["OUTPUT"]
      
      # substitute self constant with the fetched vector layer
      self.ROAD_LAYER = road_single
      
      # add fields and values
      with edit(self.ROAD_LAYER):
        self.ROAD_LAYER.addAttribute(QgsField("PK", QVariant.Int))
        self.ROAD_LAYER.addAttribute(QgsField("lv_d", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("lv_e", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("lv_n", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_d", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_e", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_n", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("lv_spd_d", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("lv_spd_e", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("lv_spd_n", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_spd_d", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_spd_e", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("hv_spd_n", QVariant.Double))
        self.ROAD_LAYER.addAttribute(QgsField("pvmt", QVariant.String))
        self.ROAD_LAYER.updateFields()
        for fid, ft in enumerate(self.ROAD_LAYER.getFeatures(), start = 1):
          (lv_d, hv_d, lv_e, hv_e, lv_n, hv_n) = self.cmptDefaultTrafficVolumeJa(ft)
          ft["PK"] = fid
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
          self.ROAD_LAYER.updateFeature(ft)
        
    return None

  def setPopulationLayer(self, extent_lnglat, target_crs):
    
    pop_point = QgsVectorLayer("Point?crs=EPSG:6668", "pop", "memory")
    pop_pr = pop_point.dataProvider()
    pop_fld = QgsFields()
    pop_fld.append(QgsField("mesh_code", QVariant.String))
    pop_fld.append(QgsField("population", QVariant.Int))
    
    with open(os.path.join(os.path.dirname(__file__),"estatId_mesh_list.txt")) as f:
      estatId_mesh = {key: value for line in f for (key, value) in [line.strip().split(None, 1)]}
    
    (lng_unit_1, lat_unit_1) = ( 1.0          , 40.0 / 60.0  )
    (lng_unit_2, lat_unit_2) = ( 7.5  / 60.0  ,  5.0 / 60.0  )
    (lng_unit_3, lat_unit_3) = (45.0  / 3600.0, 30.0 / 3600.0)
    (lng_unit_4, lat_unit_4) = (22.5  / 3600.0, 15.0 / 3600.0)
    (lng_unit_5, lat_unit_5) = (11.25 / 3600.0,  7.5 / 3600.0)
    
    (lng_min, lng_max) = (extent_lnglat.xMinimum(), extent_lnglat.xMaximum())
    (lat_min, lat_max) = (extent_lnglat.yMinimum(), extent_lnglat.yMaximum())
    
    lng_grid = [lng_min + lng_unit_5 * i for i in range(0, 2 + int((lng_max - lng_min) / lng_unit_5))]
    lat_grid = [lat_min + lat_unit_5 * i for i in range(0, 2 + int((lat_max - lat_min) / lat_unit_5))]
    
    mesh_1_list = []
    mesh_250m_list = []
    lat_center_list = []
    lng_center_list = []
    for lng, lat in itertools.product(lng_grid, lat_grid):
      mesh1 = str(int(lat / lat_unit_1)) + str(int((lng - 100.0) / lng_unit_1))
      (lat1, lng1) = (int(lat / lat_unit_1) * lat_unit_1, int(lng))
      (lat_resid, lng_resid) = (lat - lat1, lng - lng1)
      mesh2 = str(int(lat_resid / lat_unit_2)) + str(int(lng_resid / lng_unit_2))
      (lat2, lng2) = (int(lat_resid / lat_unit_2) * lat_unit_2, int(lng_resid / lng_unit_2) * lng_unit_2)
      (lat_resid, lng_resid) = (lat_resid - lat2, lng_resid - lng2)
      mesh3 = str(int(lat_resid / lat_unit_3)) + str(int(lng_resid / lng_unit_3))
      (lat3, lng3) = (int(lat_resid / lat_unit_3) * lat_unit_3, int(lng_resid / lng_unit_3) * lng_unit_3)
      (lat_resid, lng_resid) = (lat_resid - lat3, lng_resid - lng3)
      mesh4 = str((int(lng_resid / lng_unit_4) + 1) + 2 * int(lat_resid / lat_unit_4))
      (lat4, lng4) = (int(lat_resid / lat_unit_4) * lat_unit_4, int(lng_resid / lng_unit_4) * lng_unit_4)
      (lat_resid, lng_resid) = (lat_resid - lat4, lng_resid - lng4)
      mesh5 = str((int(lng_resid / lng_unit_5) + 1) + 2 * int(lat_resid / lat_unit_5))
      (lat5, lng5) = ((int(lat_resid / lat_unit_5) + 0.5) * lat_unit_5, (int(lng_resid / lng_unit_5) + 0.5) * lng_unit_5)
      
      mesh_1_list.append(mesh1)
      mesh_250m_list.append(mesh1 + mesh2 + mesh3 + mesh4 + mesh5)
      lng_center_list.append(lng1 + lng2 + lng3 + lng4 + lng5)
      lat_center_list.append(lat1 + lat2 + lat3 + lat4 + lat5)
    
      
    pop_dict = {}
    uri_estat = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"    
    for mesh1 in set(mesh_1_list):
      params_estat = {
        "appId": "b877fd89560ce21475681dba1a6681dd6426cbc3",
        "statsDataId": estatId_mesh.get(mesh1),
        "statsCode": "00200521",
        "cdCat01": "0010",
        "cdArea": ",".join(mesh_250m_list),
        "metaGetFlg": "N"
      }

      req = urllib.request.Request(f"{uri_estat}?{urllib.parse.urlencode(params_estat)}")
      with urllib.request.urlopen(req) as res:
        body = json.load(res)
        if body.get("GET_STATS_DATA").get("STATISTICAL_DATA").get("DATA_INF") != None:
          pop_dict.update({value["@area"]: int(value["$"]) for value in body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]})
      
    for mesh_250m, x, y in zip(mesh_250m_list, lng_center_list, lat_center_list):
      
      ft = QgsFeature(pop_fld)
      ft.setGeometry(QgsPoint(x, y))
      ft["mesh_code"] = mesh_250m
      if pop_dict.get(mesh_250m) != None:
        ft["population"] = pop_dict.get(mesh_250m)
      
      if pop_point.fields().count() == 0:
        pop_pr.addAttributes(pop_fld)
        pop_point.updateFields()
      pop_pr.addFeatures([ft])
      
    pop_rasterized = processing.run(
      "gdal:rasterize",
      {
        "INPUT": pop_point,
        "FIELD": "population",
        "UNITS": 1,
        "WIDTH": 11.25 / 3600.0,
        "HEIGHT": 7.5 / 3600.0,
        "DATA_TYPE": 2,
        "INIT": 0,
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    self.POP_LAYER = QgsRasterLayer(pop_rasterized, "population")
    
  def setBuildingLayer(self, extent_lnglat, target_crs):    
    
    # initialize building layer (and data provider) to which vector features added
    bldg_layer = QgsVectorLayer("Polygon?crs=EPSG:3857&index=yes", baseName = "building_from_web", providerLib = "memory")  
    bldg_pr = bldg_layer.dataProvider()

    # fetch vector features from GSI
    
    # set zoom level, tile x and y, and number of pixels in a tile
    z = 16 # maximum zoom level of 16
    (tx_min, ty_min) = self.cmptTileXY(z, extent_lnglat.xMinimum(),extent_lnglat.yMaximum())
    (tx_max, ty_max) = self.cmptTileXY(z, extent_lnglat.xMaximum(),extent_lnglat.yMinimum())
    
    n_pixels_all = self.N_PIXELS_IN_GSI_VTILE * 2 ** z
    meter_per_tile  = self.EQUATOR_M / 2 ** z
    meter_per_pixel = self.EQUATOR_M / n_pixels_all
    
    # fetch features for each tx and ty
    for tx, ty in itertools.product(list(range(tx_min, tx_max+1)), list(range(ty_min,ty_max+1))):
      uri = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{z}/{tx}/{ty}.pbf|layername=building|geometrytype=Polygon"
      vlayer_raw = QgsVectorLayer(uri, "building_raw", "ogr")
      # vlayer_raw.dataProvider.subLayer()
      # uri = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/{z}/{tx}/{ty}.pbf|layername=landforml|geometrytype=Polygon"
      
      if vlayer_raw.featureCount() > 0:
        # affine transformation to obtain x and y for a given CRS
        affine_parameters = {        
            "INPUT": vlayer_raw,
            "DELTA_X":    tx    * meter_per_tile - self.EQUATOR_M / 2,
            "DELTA_Y": - (ty+1) * meter_per_tile + self.EQUATOR_M / 2,
            "SCALE_X": meter_per_pixel,
            "SCALE_Y": meter_per_pixel,
            "OUTPUT": "TEMPORARY_OUTPUT"
        }        
        vlayer = processing.run("native:affinetransform", affine_parameters)["OUTPUT"]
        
        for ft in vlayer.getFeatures():
          if bldg_layer.featureCount() == 0:
            bldg_pr.addAttributes([ft.fields().at(idx) for idx in range(ft.fields().count())])
            bldg_layer.updateFields()
          bldg_pr.addFeatures([ft])
    
    # post processing if there are any features
    if bldg_layer.featureCount() > 0:
      
      # CRS transformation
      bldg_transform = processing.run(
        "native:reprojectlayer", 
        {
          "INPUT": bldg_layer,
          "TARGET_CRS": target_crs,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # Dissolve
      bldg_dissolve = processing.run(
        "native:dissolve", 
        {
          "INPUT": bldg_transform,
          "FIELD": bldg_transform.fields().names(),
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # Multipart to single parts
      bldg_single = processing.run(
        "native:multiparttosingleparts", 
        {
          "INPUT": bldg_dissolve,
          "OUTPUT": "memory:building"
        }
      )["OUTPUT"]
      
      # substitute self constant with the fetched vector layer
      self.BUILDING_LAYER = bldg_single
      
      # add fields and values
      with edit(self.BUILDING_LAYER):
        self.BUILDING_LAYER.addAttribute(QgsField("PK", QVariant.Int))
        self.BUILDING_LAYER.addAttribute(QgsField("height", QVariant.Double, "double", 3, 1))
        self.BUILDING_LAYER.updateFields()
        for fid, ft in enumerate(self.BUILDING_LAYER.getFeatures(), start = 0):
          ft["PK"] = fid
          ft["height"] = self.BUILDING_HEIGHT_DEFAULT
          self.BUILDING_LAYER.updateFeature(ft)     
      
    return None
  
  def setDemLayer(self, extent_lnglat, target_crs):
    
    # initialize dem layer (and data provider) to which vector features added
    dem_layer = QgsVectorLayer("Point?crs=EPSG:6668&index=yes",baseName = "dem_from_web", providerLib = "memory")
    dem_pr = dem_layer.dataProvider()
    
    # fetch vector features from GSI    
    # set zoom level, tile x and y, and number of pixels in a tile
    z = 18 # fixed zoom level of 18
    (tx_min, ty_min) = self.cmptTileXY(z, extent_lnglat.xMinimum(),extent_lnglat.yMaximum())
    (tx_max, ty_max) = self.cmptTileXY(z, extent_lnglat.xMaximum(),extent_lnglat.yMinimum())
    
    # fetch features for each tx and ty
    for tx, ty in itertools.product(list(range(tx_min, tx_max+1)), list(range(ty_min,ty_max+1))):
      uri = f"https://cyberjapandata.gsi.go.jp/xyz/experimental_dem10b/{z}/{tx}/{ty}.geojson"
      vlayer = QgsVectorLayer(uri, "dem", "ogr")
      
      for ft in vlayer.getFeatures():
        # set the fields of roads if it is not set 
        if dem_layer.fields().count() == 0:
          dem_pr.addAttributes([ft.fields().at(idx) for idx in range(ft.fields().count())])
          dem_layer.updateFields()
        dem_pr.addFeatures([ft])
    
    # CRS transform    
    dem_transform = processing.run(
      "native:reprojectlayer", 
      {
        "INPUT": dem_layer,
        "TARGET_CRS": target_crs,
        "OUTPUT": "memory:dem"
      }
      )["OUTPUT"]
    
    # substitute self constant with the fetched vector layer
    self.DEM_LAYER = dem_transform
    # add fields and values
    with edit(self.DEM_LAYER):
      self.DEM_LAYER.addAttribute(QgsField("height", QVariant.Int))
      self.DEM_LAYER.updateFields()
      for ft in self.DEM_LAYER.getFeatures():
        ft["height"] = ft["alti"]
    
    return None 
  
  def setReceiverLayer(self, parameters, context, feedback):
    receiversfacade_parameters = {
      "BUILDING": self.BUILDING_LAYER,
      "SOURCE": self.ROAD_LAYER,
      "FENCE": self.parameterAsVectorLayer(parameters, "FENCE", context),
      "DELTA": self.parameterAsDouble(parameters, "DELTA", context),
      "HEIGHT": self.parameterAsDouble(parameters, "HEIGHT", context),
      "OUTPUT_DIRECTORY": self.OUTPUT_DIR
    }
    
    receiversfacade_parameters = {k:v for k, v in receiversfacade_parameters.items() if v is not None}
    
    processing.run(
      "hrisk:receiverfacade", 
      receiversfacade_parameters,
      feedback = feedback
    )
    
    receiversgrid_parameters = {
      "BUILDING": self.BUILDING_LAYER,
      "SOURCE": self.ROAD_LAYER,
      "FENCE": self.parameterAsVectorLayer(parameters, "FENCE", context),
      "MAX_PROP_DIST": self.parameterAsDouble(parameters, "MAX_PROP_DIST", context),
      "ROAD_WIDTH": self.parameterAsDouble(parameters, "ROAD_WIDTH", context),
      "MAX_AREA": self.parameterAsDouble(parameters, "MAX_AREA", context),
      "HEIGHT": self.parameterAsDouble(parameters, "HEIGHT", context),
      "ISO_SURFACE": self.parameterAsBoolean(parameters, "ISO_SURFACE", context),
      "OUTPUT_DIRECTORY": self.OUTPUT_DIR
    }
    
    receiversgrid_parameters = {k:v for k, v in receiversgrid_parameters.items() if v is not None}
    
    processing.run(
      "hrisk:receiverdelaunaygrid", 
      receiversgrid_parameters,
      feedback = feedback
    )
    
    return None
  
  def cmptTileXY(self, z, lng, lat):
    return (
      int(2**(z+7) * (lng / 180 + 1) / 256),
      int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
    )
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    if self.CALCAREA_LAYER != None:
      QgsProject.instance().addMapLayer(self.CALCAREA_LAYER)
    if self.ROAD_LAYER != None:
      QgsProject.instance().addMapLayer(self.ROAD_LAYER)
    if self.BUILDING_LAYER != None:
      QgsProject.instance().addMapLayer(self.BUILDING_LAYER)
    if self.DEM_LAYER != None:
      QgsProject.instance().addMapLayer(self.DEM_LAYER)
    if self.POP_LAYER != None:
      QgsProject.instance().addMapLayer(self.POP_LAYER)
      
    return {}

  def name(self):
    return 'fetchjageom'

  def displayName(self):
    return self.tr("Fetch geometries and set receivers")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchgeometry'

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)

  def createInstance(self):
    return fetchjageom()
