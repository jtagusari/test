from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP
  )
from qgis.core import (
  QgsApplication,
  QgsCoordinateTransform,
  QgsVectorLayer,
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsProcessingParameterCrs, 
  QgsProcessingParameterFeatureSink,
  QgsRectangle,
  QgsGeometry,
  QgsFeature,
  QgsReferencedRectangle,
  QgsProject
  )
from qgis import processing

from qgis.utils import iface
import sys
import math
import itertools
import os
import shutil
import glob

from .algabstract import algabstract

# abstract class for fetching information from web
class fetchabstract(algabstract):
  
  # input UIs
  PARAMETERS = {}
  
  # calculation area
  CALC_AREA = None
    
  # parameters for fetching data from map tile
  MAP_TILE = {
    "SET": False,
    "URL": None,
    "CRS": None,
    "GEOM_TYPE": None,
    "Z": None,
    "XMIN": None, "XMAX": None, "YMIN": None, "YMAX": None
    }
  
  # parameters for fetching data from OpenStreetMap
  MAP_OSM = {
    "SET": False,
    "URL": "https://lz4.overpass-api.de/api/interpreter",
    "CRS": QgsCoordinateReferenceSystem("EPSG:4326"),
    "GEOM_TYPE": None,
    "QUICKOSM_ARGS": {
      "KEY": None,
      "VALUE": None,
      "EXTENT": None,
      "TIMEOUT": 25
    }
  }
  
  # parameters for fetching data from other URL (e.g. SRTM)
  MAP_URL = {
    "SET": False,
    "URL": None,
    "FILE": None,
    "CRS": None,
    "GEOM_TYPE": None,
    "LOGIN": None,
    "ZIPPED": None
  }
  
  # initialize extent and CRS using the canvas
  def initUsingCanvas(self):
    map_rectangle = iface.mapCanvas().extent()
    map_crs = iface.mapCanvas().mapSettings().destinationCrs()
    if map_crs.isGeographic():
      default_crs = self.getUtmCrs(map_rectangle.center().x(), map_rectangle.center().y())
    else:
      default_crs = map_crs
      
    self.PARAMETERS["EXTENT"]["ui_args"]["defaultValue"] = map_rectangle
    self.PARAMETERS["TARGET_CRS"]["ui_args"]["defaultValue"] = default_crs
      
  
  # get CRS of the UTM using longitude and latitude
  def getUtmCrs(self, lng, lat):
    epsg_code = 32600 + 100 * (lat < 0) + int((lng + 180) / 6) + 1
    crs = QgsCoordinateReferenceSystem(f'EPSG:{epsg_code}')
    if crs.isValid():
        return crs
    else:
        return None
    
  # set calc_area
  # it is used mainly for fetching the data, 
  # so the crs for fetching the data should be used
  def setCalcArea(self, parameters, context, feedback, new_crs = None):
    
    # get target x-y CRS, to apply the buffer and determine the calculation area
    target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    
    # check whether the target CRS is x-y coordinates
    if target_crs.isGeographic():
      sys.exit(self.tr("The Buffer of the fetch area (using Target CRS) is NOT a Cartesian Coordinate System"))
    
    # get the extent, using the target CRS
    extent = self.parameterAsExtent(
      parameters, "EXTENT", context, 
      self.parameterAsCrs(parameters, "TARGET_CRS", context)
      )
    
    # get the buffer
    buffer = self.parameterAsDouble(parameters, "BUFFER",context)
    
    # get the calculation area, using the extent and buffer
    calc_area = QgsReferencedRectangle(
      QgsRectangle(
        extent.xMinimum() - buffer,
        extent.yMinimum() - buffer,
        extent.xMaximum() + buffer,
        extent.yMaximum() + buffer
      ),
      target_crs
    )
    
    # if the crs is specified, transform the area
    if new_crs is not None:
      transform = QgsCoordinateTransform(target_crs, new_crs, QgsProject.instance())
      self.CALC_AREA = QgsReferencedRectangle(transform.transformBoundingBox(calc_area), new_crs)
    else:
      self.CALC_AREA = calc_area
  
  # get the calculation area as a polygon vector layer
  def calcAreaAsVectorLayer(self):
    vec_layer = QgsVectorLayer("Polygon?crs=" + self.CALC_AREA.crs().authid(), "calc_area", "memory")
    ft = QgsFeature()
    ft.setGeometry(QgsGeometry.fromRect(self.CALC_AREA))
    vec_layer.dataProvider().addFeatures([ft])    
    return(vec_layer)
      
  # set information about the map tile
  def setMapTileMeta(self, parameters, context, feedback, geom_type):
    # set parameters (from UIs)
    self.MAP_TILE["URL"] = self.parameterAsString(parameters,"MAPTILE_URL", context)
    self.MAP_TILE["CRS"] = self.parameterAsCrs(parameters,"MAPTILE_CRS", context)
    z = self.parameterAsInt(parameters, "MAPTILE_ZOOM", context) #used later
    self.MAP_TILE["Z"] = z
    self.MAP_TILE["GEOM_TYPE"] = geom_type
    
    # set the extent using self.CALC_AREA
    if self.CALC_AREA is not None:
      lng_min = self.CALC_AREA.xMinimum()
      lng_max = self.CALC_AREA.xMaximum()
      lat_min = self.CALC_AREA.yMinimum()
      lat_max = self.CALC_AREA.yMaximum()
      
      # Note that YMIN is obtained from lat_max / YMAX is from lat_min
      self.MAP_TILE["XMIN"] = int(2**(z+7) * (lng_min / 180 + 1) / 256)
      self.MAP_TILE["XMAX"] = int(2**(z+7) * (lng_max / 180 + 1) / 256)
      self.MAP_TILE["YMIN"] = int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat_max)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
      self.MAP_TILE["YMAX"] = int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat_min)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
    
    # finally check if there are values in required fields
    if self.MAP_TILE["URL"] is not None and self.MAP_TILE["CRS"] is not None and\
      self.MAP_TILE["GEOM_TYPE"] is not None and self.MAP_TILE["Z"] is not None and \
      self.CALC_AREA is not None:
        self.MAP_TILE["SET"] = True
  
  
  # set information about the map tile
  def setOsmMeta(self, parameters, context, feedback, geom_type=None):
    self.MAP_TILE["URL"] = self.parameterAsString(parameters, "OSM_URL", context)
    self.MAP_OSM["GEOM_TYPE"] = geom_type
    self.MAP_OSM["QUICKOSM_ARGS"]["KEY"] = self.parameterAsString(parameters, "OSM_KEY", context)
    self.MAP_OSM["QUICKOSM_ARGS"]["VALUE"] = self.parameterAsString(parameters, "OSM_VALUE", context)
    self.MAP_OSM["QUICKOSM_ARGS"]["TIMEOUT"] = self.parameterAsDouble(parameters, "OSM_TIMEOUT", context)
    
    if self.CALC_AREA is not None:
      lng_min_str = str(self.CALC_AREA.xMinimum())
      lng_max_str = str(self.CALC_AREA.xMaximum())
      lat_min_str = str(self.CALC_AREA.yMinimum())
      lat_max_str = str(self.CALC_AREA.yMaximum())
      crs_str = self.CALC_AREA.crs().authid()
      self.MAP_OSM["QUICKOSM_ARGS"]["EXTENT"] = f"{lng_min_str},{lng_max_str},{lat_min_str},{lat_max_str} [{crs_str}]"
      
    if self.MAP_OSM["GEOM_TYPE"] is not None and self.MAP_OSM["QUICKOSM_ARGS"]["EXTENT"] is not None and \
      self.MAP_OSM["QUICKOSM_ARGS"]["KEY"] is not None and self.MAP_OSM["QUICKOSM_ARGS"]["VALUE"] is not None:
        self.MAP_OSM["SET"] = True
  
  # to set the parameters for using data over the Internet
  def setMapUrlMeta(self, parameters, context, feedback):
    pass
  
  # fetch features from the map tile
  def fetchFeaturesFromTile(self, parameters, context, feedback):
    
    # if not all the parameters were set, stop
    if self.MAP_TILE["SET"] is not True:
      sys.exit(self.tr("NOT required parameters are filled"))
    
    # initialize the vector layer  
    vec_layer = QgsVectorLayer(
      self.MAP_TILE["GEOM_TYPE"] + "?crs=" + self.MAP_TILE["CRS"].authid() + "&index=yes",
      baseName = "layer_from_tile", 
      providerLib = "memory"
      )
    vec_pr = vec_layer.dataProvider()
  
    # fetch features for each tx and ty
    for tx, ty in itertools.product(list(range(self.MAP_TILE["XMIN"], self.MAP_TILE["XMAX"]+1)), list(range(self.MAP_TILE["YMIN"],self.MAP_TILE["YMAX"]+1))):
      # get URL
      url = self.MAP_TILE["URL"].replace("{z}", str(self.MAP_TILE["Z"])).replace("{x}", str(tx)).replace("{y}",str(ty))
      # get tile data
      vec_from_tile = QgsVectorLayer(url, "v", "ogr")
      
      # if there are features
      if vec_from_tile.featureCount() > 0:
        # modify the feature (if necessary)
        vec_from_tile_rev = self.modifyFeaturesFromTile(vec_from_tile, self.MAP_TILE["Z"], tx, ty)
        
        # features added using the data provider
        for ft in vec_from_tile_rev.getFeatures():
          # set the fields if it is not set 
          if vec_layer.fields().count() == 0:
            vec_pr.addAttributes([ft.fields().at(idx) for idx in range(ft.fields().count())])
            vec_layer.updateFields()
          vec_pr.addFeatures([ft])
    
    return vec_layer
    
  # fetch features from the URL
  # note that it only downloads file(s)
  def fetchFeaturesFromURL(self, parameters, context, feedback, session = None):
    if self.MAP_URL["SET"]:
      
      # if login is needed, session is also needed
      if self.MAP_URL["LOGIN"] is not None:
        if session is None:
          sys.exit(self.tr("Session must be given for Log-in procedure"))
          
      # start downloading
      self.MAP_URL["DOWNLOADED_FILE"] = []
      for url, file in zip(self.MAP_URL["URL"], self.MAP_URL["FILE"]):
        feedback.pushInfo(self.tr("Downloading ") + url)
        response = session.get(url)
        
        # if download was succeeded, save as a file
        if response.status_code == 200:
          feedback.pushInfo(self.tr("... Succeeded!"))
          with open(file, "wb") as f:
            f.write(response.content)
          
          # if it is a zip file, unpack it
          if self.MAP_URL["ZIPPED"]:
            zip_dir = os.path.splitext(file)[0]
            shutil.unpack_archive(file, zip_dir)
            archived_files = glob.glob(os.path.join(zip_dir, "*"))
            for afile in archived_files:
              self.MAP_URL["DOWNLOADED_FILE"].append(afile)
          else:
            self.MAP_URL["DOWNLOADED_FILE"].append(file)
            
        # if the download was not succeeded
        else:
          feedback.pushInfo(self.tr("... ERROR!"))
      
      if len(self.MAP_URL["DOWNLOADED_FILE"]) == 0:
        sys.exit(self.tr("No Files were downloaded!"))
      
      self.createMergedFeature(parameters, context, feedback)
  
  # function to create a feature from the downloaded file(s)
  def createMergedFeature(self, parameters, context, feedback):
    pass
  
  
  # fetch features from the map tile
  def fetchFeaturesFromOsm(self, context, feedback):
    if self.MAP_OSM["SET"]:
      
      quickosm_results = processing.run(
        "quickosm:downloadosmdataextentquery", 
        {
          "KEY": self.MAP_OSM["QUICKOSM_ARGS"]["KEY"],
          "VALUE": self.MAP_OSM["QUICKOSM_ARGS"]["VALUE"],
          "EXTENT": self.MAP_OSM["QUICKOSM_ARGS"]["EXTENT"],
          "TIMEOUT": self.MAP_OSM["QUICKOSM_ARGS"]["TIMEOUT"],
          "SERVER": self.MAP_OSM["URL"],
          "FILE": "TEMPORARY_OUTPUT"
        },
        # context = context, # not pass the context, so as not to show the warnings
        feedback = feedback
      )
      
      
      if self.MAP_OSM["GEOM_TYPE"] == "Point":
        vec_layer = quickosm_results["OUTPUT_POINTS"]
      elif self.MAP_OSM["GEOM_TYPE"] == "Linestring":
        vec_layer = quickosm_results["OUTPUT_LINES"]
      elif self.MAP_OSM["GEOM_TYPE"] == "Multilinestring":
        vec_layer = quickosm_results["OUTPUT_MULTILINESTRINGS"]
      elif self.MAP_OSM["GEOM_TYPE"] == "Polygon":
        vec_layer = quickosm_results["OUTPUT_MULTIPOLYGONS"]
      else:
        vec_layer = None
      
      return vec_layer
    else:
      return None
  
  
  def modifyFeaturesFromTile(self, fts, z, tx, ty):
    return(fts)
    
  def dissolveFeatures(self, fts):
      # Dissolve
      fts_dissolve = processing.run(
        "native:dissolve", 
        {
          "INPUT": fts,
          "FIELD": fts.fields().names(),
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      # Multipart to Single parts
      fts_single = processing.run(
        "native:multiparttosingleparts", 
        {
          "INPUT": fts_dissolve,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      return fts_single
  
  # transform to the target CRS
  def transformToTargetCrs(self, parameters, context, feedback, fts):
    target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    fts_transformed = processing.run(
        "native:reprojectlayer", 
        {
          "INPUT": fts,
          "TARGET_CRS": target_crs,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]      
    return fts_transformed
