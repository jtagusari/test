from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.PyQt.QtGui import QColor
from qgis.core import (
  QgsProcessingParameterCrs,
  QgsCoordinateReferenceSystem,
  QgsVectorLayer,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsFeature,
  QgsPoint,
  QgsFeature,
  QgsProcessingParameterRasterDestination,
  QgsSingleBandPseudoColorRenderer,
  QgsRasterShader,
  QgsColorRampShader,
  QgsProcessingLayerPostProcessorInterface,
  QgsRasterBandStats,
  QgsProcessingParameterString
  )
from qgis import processing

import itertools
import urllib
import sys
import json
import os
from .fetchabstract import fetchabstract
from .worldmesh import (
  cal_meshcode5,
  meshcode_to_latlong
)

class fetchjapop(fetchabstract):
  
  PARAMETERS = {  
    "FETCH_EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjapop","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjapop","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjapop","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "WEBFETCH_URL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjapop","Base-URL of the vector-tile map"),
        "defaultValue": "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
      }
    },
    "FETCH_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjapop","CRS of the vector-tile map"),
        "defaultValue": QgsCoordinateReferenceSystem("EPSG:6668")
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterRasterDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjapop","Population" )
      }
    }
  }  
  
  
  ESTAT_ID_MESH_FILE = os.path.join(os.path.dirname(__file__),"estatId_mesh_list.txt")
  ESTAT_ID_MESH_DICT = {}
  
  ESTAT_API_URL = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"   
  ESTAT_API_PARAMS = {
    "appId": "b877fd89560ce21475681dba1a6681dd6426cbc3",
    "statsDataId": "",
    "statsCode": "00200521",
    "cdCat01": "0010",
    "cdArea": "",
    "metaGetFlg": "N"
  }
  
  
  LAT_UNIT_5 =  7.5 / 3600.0
  LNG_UNIT_5 = 11.25 / 3600.0
  
  def __init__(self) -> None:
    super().__init__()
    self.WEBFETCH_ARGS.update(
      {"MESH": {}}
    )
    with open(self.ESTAT_ID_MESH_FILE) as f:
      self.ESTAT_ID_MESH_DICT = {key: value for line in f for (key, value) in [line.strip().split(None, 1)]}
      
  
  # set information about the map tile
  def setWebFetchArgs(self, parameters, context, feedback):
        
    self.WEBFETCH_ARGS["CRS"] = self.parameterAsCrs(parameters, "FETCH_CRS", context)
    self.WEBFETCH_ARGS["GEOM_TYPE"] = "Point"
      
    lng_min = self.FETCH_AREA.xMinimum()
    lng_max = self.FETCH_AREA.xMaximum()
    lat_min = self.FETCH_AREA.yMinimum()
    lat_max = self.FETCH_AREA.yMaximum()
    
    lat_grid = [lat_min + self.LAT_UNIT_5 * i for i in range(0, 2 + int((lat_max - lat_min) / self.LAT_UNIT_5))]
    lng_grid = [lng_min + self.LNG_UNIT_5 * i for i in range(0, 2 + int((lng_max - lng_min) / self.LNG_UNIT_5))]
    
    mesh_code_1 = None
    mesh_dict = {}
    for lat, lng in itertools.product(lat_grid, lng_grid):
      mesh_code_5 = cal_meshcode5(lat, lng)[2:]
      coords_mesh = meshcode_to_latlong("20" + mesh_code_5)
      lat_mesh = coords_mesh["lat"] - self.LAT_UNIT_5 / 2
      lng_mesh = coords_mesh["long"] +  self.LNG_UNIT_5 / 2
      if mesh_code_1 is not None and mesh_code_1 != mesh_code_5[:4]:
        self.WEBFETCH_ARGS["MESH"][mesh_code_1] = mesh_dict
        mesh_dict = {}
      else:
        mesh_code_1 = mesh_code_5[:4]
        mesh_dict[mesh_code_5] = {"LONG": lng_mesh, "LAT": lat_mesh}
    
    if len(mesh_dict) > 0:
      self.WEBFETCH_ARGS["MESH"][mesh_code_1] = mesh_dict
    
    
    for mesh_code_1, mesh_dict in self.WEBFETCH_ARGS["MESH"].items():
      params_estat = self.ESTAT_API_PARAMS
      params_estat["statsDataId"] = self.ESTAT_ID_MESH_DICT.get(mesh_code_1)
    
      for mesh_code_5_shortlist in [list(mesh_dict.keys())[i:i+20] for i in range(0, len(mesh_dict), 20)]:
        params_estat["cdArea"] = ",".join(mesh_code_5_shortlist)

        self.WEBFETCH_ARGS["URL"].append(
          self.parameterAsString(parameters, "WEBFETCH_URL", context) + f"?{urllib.parse.urlencode(params_estat)}"
        )

    if self.WEBFETCH_ARGS["CRS"] is not None and self.WEBFETCH_ARGS["MESH"] is not None:
        self.WEBFETCH_ARGS["SET"] = True
  
  # fetch features from the map tile
  def mergeFetchedFeatures(self, parameters, context, feedback):
    
    init_string = self.WEBFETCH_ARGS["GEOM_TYPE"] + "?crs=" + self.WEBFETCH_ARGS["CRS"].authid() + "&index=yes&field=population:integer"
    vec_layer = QgsVectorLayer(init_string,baseName = "layer_from_tile", providerLib = "memory")
    vec_pr = vec_layer.dataProvider()
    
    # if there are no files
    if len(self.WEBFETCH_ARGS["DOWNLOADED_FILE"]) == 0:
      sys.exit(self.tr("No population results were obtained!"))
    
    
    for file in self.WEBFETCH_ARGS["DOWNLOADED_FILE"]:
      with open(file, 'r') as f:
        body = json.load(f)
      if body.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {}).get("DATA_INF") != None:
        if isinstance(body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"], list):
          results = body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
        else:
          results = [body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]]
        
        for stat_dict in results:
          lnglat = self.WEBFETCH_ARGS["MESH"].get(stat_dict["@area"][:4], {}).get(stat_dict["@area"])
          if lnglat is not None:
            ft = QgsFeature(vec_layer.fields())
            ft.setGeometry(QgsPoint(lnglat.get("LONG"), lnglat.get("LAT")))
            ft["population"] = stat_dict["$"]
            vec_pr.addFeatures([ft])
    
    return vec_layer
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  
  def processAlgorithm(self, parameters, context, feedback):  
    self.setFetchArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setWebFetchArgs(parameters, context, feedback)
    
    self.fetchFeaturesFromWeb(parameters, context, feedback)
    pop_raw = self.mergeFetchedFeatures(parameters, context, feedback)
    pop_raster = processing.run(
      "gdal:rasterize",
      {
        "INPUT": pop_raw,
        "FIELD": "population",
        "UNITS": 1,
        "WIDTH": 11.25 / 3600.0,
        "HEIGHT": 7.5 / 3600.0,
        "DATA_TYPE": 2,
        "INIT": 0,
        "OUTPUT": self.parameterAsOutputLayer(parameters, "OUTPUT", context)
      }
    )["OUTPUT"]
        
    return {"OUTPUT":pop_raster}
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    global pop_postprocessors
    pop_postprocessors = []
    for path, layer_detail in context.layersToLoadOnCompletion().items():
      if layer_detail.name == self.PARAMETERS["OUTPUT"]["ui_args"]["description"]:
        pop_postprocessors.append(popPostProcessor())
        context.layerToLoadOnCompletionDetails(path).setPostProcessor(pop_postprocessors[-1])
    return {}

  def displayName(self):
    return self.tr("Population (Ja)")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjapop()

class popPostProcessor (QgsProcessingLayerPostProcessorInterface):
    
  def postProcessLayer(self, layer, context, feedback):
    stats = layer.dataProvider().bandStatistics(1, QgsRasterBandStats.All) 
    
    cr_fcn = QgsColorRampShader(
      minimumValue = 1,
      maximumValue = stats.maximumValue
    )
    cr_fcn.setColorRampItemList(
      [
        QgsColorRampShader.ColorRampItem(1, QColor("#f1eef6")),
        QgsColorRampShader.ColorRampItem(stats.maximumValue, QColor("#980043"))
      ]
    )
    cr_fcn.setClip(True)
    shader = QgsRasterShader()
    shader.setRasterShaderFunction(cr_fcn)
    
    pop_renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
    layer.setRenderer(pop_renderer)
    layer.setOpacity(0.5)
    layer.triggerRepaint()        
  