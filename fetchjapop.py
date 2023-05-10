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
from .fetchabstract import fetchabstract
from .jameshpop import jameshpop

class fetchjapop(fetchabstract, jameshpop):
  
  PARAMETERS = {  
    "EXTENT": {
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
    "MAP_BASEURL": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "optional": True,
        "description": QT_TRANSLATE_NOOP("fetchjapop","Base-URL of the vector-tile map"),
        "defaultValue": "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"
      }
    },
    "MAP_CRS": {
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
  
  
  # set information about the map tile
  def setMapUrlMeta(self, parameters, context, feedback):
        
    self.MAP_URL["URL"] = self.parameterAsString(parameters, "MAP_BASEURL", context)
    self.MAP_URL["CRS"] = self.parameterAsCrs(parameters, "MAP_CRS", context)
    self.MAP_URL["GEOM_TYPE"] = "Point"
      
    lng_min = self.CALC_AREA.xMinimum()
    lng_max = self.CALC_AREA.xMaximum()
    lat_min = self.CALC_AREA.yMinimum()
    lat_max = self.CALC_AREA.yMaximum()
    
    lat_grid = [lat_min + self.LAT_UNIT_5 * i for i in range(0, 2 + int((lat_max - lat_min) / self.LAT_UNIT_5))]
    lng_grid = [lng_min + self.LNG_UNIT_5 * i for i in range(0, 2 + int((lng_max - lng_min) / self.LNG_UNIT_5))]
  
    self.MAP_URL["MESH"] = {}
    
    m1_str = None
    mesh_dict = {}
    for lat, lng in itertools.product(lat_grid, lng_grid):
      (mesh_str, lng_lat_coords) = self.coordsToMesh(lng, lat)
      if m1_str is not None and m1_str != mesh_str[:4]:
        self.MAP_URL["MESH"][m1_str] = mesh_dict
        mesh_dict = {}
      else:
        m1_str = mesh_str[:4]
        mesh_dict[mesh_str] = {"LONG": lng_lat_coords[0], "LAT": lng_lat_coords[1]}
    
    if len(mesh_dict) > 0:
      self.MAP_URL["MESH"][m1_str] = mesh_dict

    if self.MAP_URL["URL"] is not None and self.MAP_URL["CRS"] is not None and\
      self.MAP_URL["GEOM_TYPE"] is not None and self.MAP_URL["MESH"] is not None:
        self.MAP_URL["SET"] = True
  
  # fetch features from the map tile
  def fetchFeaturesFromTile(self, parameters, context, feedback):
    
    if self.MAP_URL["SET"]:
      init_string = self.MAP_URL["GEOM_TYPE"] + "?crs=" + self.MAP_URL["CRS"].authid() + "&index=yes&field=population:integer"
      vec_layer = QgsVectorLayer(init_string,baseName = "layer_from_tile", providerLib = "memory")
      vec_pr = vec_layer.dataProvider()
      
      for mesh1, mesh_dict in self.MAP_URL["MESH"].items():
        mesh_dict_pop = self.fetchPop(mesh1, list(mesh_dict.keys()))
        feedback.pushInfo(f"fetched from {mesh1}- " + ", ".join([mesh5_str[4:] for mesh5_str in mesh_dict.keys()]))
        for key, value in mesh_dict_pop.items():
          ft = QgsFeature(vec_layer.fields())
          ft.setGeometry(QgsPoint(mesh_dict[key]["LONG"], mesh_dict[key]["LAT"]))
          ft["population"] = value["pop"]
          vec_pr.addFeatures([ft])
                
      return vec_layer
    else:
      return None
  
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
  
  
  def processAlgorithm(self, parameters, context, feedback):   
    
    self.setCalcArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:6668"))
    self.setMapUrlMeta(parameters, context, feedback)
    
    pop_raw = self.fetchFeaturesFromTile(parameters, context, feedback)
    
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
  