from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP
  )
from qgis.core import (
  QgsApplication,
  QgsCoordinateTransform,
  QgsVectorLayer,
  QgsCoordinateReferenceSystem,
  QgsProcessingUtils,
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
import concurrent.futures
import requests
import uuid

from .algabstract import algabstract

# abstract class for fetching information from web
class fetchabstract(algabstract):
  
  # input UIs
  PARAMETERS = {}
  
  # fetch area
  FETCH_AREA = None
    
  # parameters for fetching data from map tile
  TILEMAP_ARGS = {
    "SET": False,
    "URL": None,
    "CRS": None,
    "GEOM_TYPE": None,
    "Z": None,
    "XMIN": None, "XMAX": None, "YMIN": None, "YMAX": None
    }
  
  # parameters for fetching data from OpenStreetMap
  OSM_ARGS = {
    "SET": False,
    "URL": "https://lz4.overpass-api.de/api/interpreter",
    "CRS": QgsCoordinateReferenceSystem("EPSG:4326"),
    "GEOM_TYPE": None,
    "QUICKOSM_ARGS": {
      "KEY": None,
      "VALUE": None,
      "FETCH_EXTENT": None,
      "TIMEOUT": 25
    }
  }
  
  # parameters for fetching data from other URL (e.g. SRTM)
  WEBFETCH_ARGS = {
    "SET": False,
    "URL": [],
    "DOWNLOADED_FILE": [],
    "CRS": None,
    "GEOM_TYPE": None,
    "LOGIN": None,
    "ARCHIVED": ""
  }
  
  # initialize extent and CRS using the canvas
  def initUsingCanvas(self):
    map_rectangle = iface.mapCanvas().extent()
    map_crs = iface.mapCanvas().mapSettings().destinationCrs()
    if map_crs.isGeographic():
      default_crs = self.getUtmCrs(map_rectangle.center().x(), map_rectangle.center().y())
    else:
      default_crs = map_crs
      
    self.PARAMETERS["FETCH_EXTENT"]["ui_args"]["defaultValue"] = map_rectangle
    self.PARAMETERS["TARGET_CRS"]["ui_args"]["defaultValue"] = default_crs
      
  
  # get CRS of the UTM using longitude and latitude
  def getUtmCrs(self, lng, lat):
    epsg_code = 32600 + 100 * (lat < 0) + int((lng + 180) / 6) + 1
    crs = QgsCoordinateReferenceSystem(f'EPSG:{epsg_code}')
    if crs.isValid():
        return crs
    else:
        return None
    
  # set fetch_area
  # it is used mainly for fetching the data, 
  # so the crs for fetching the data should be used
  def setFetchArea(self, parameters, context, feedback, new_crs = None):
    
    # get target x-y CRS, to apply the buffer and determine the fetch area
    target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    
    # check whether the target CRS is x-y coordinates
    if target_crs.isGeographic():
      sys.exit(self.tr("The Buffer of the fetch area (using Target CRS) is NOT a Cartesian Coordinate System"))
    
    # get the extent, using the target CRS
    fetch_extent = self.parameterAsExtent(
      parameters, "FETCH_EXTENT", context, 
      self.parameterAsCrs(parameters, "TARGET_CRS", context)
      )
    
    # get the buffer
    buffer = self.parameterAsDouble(parameters, "BUFFER",context)
    
    # get the fetch area, using the extent and buffer
    fetch_area = QgsReferencedRectangle(
      QgsRectangle(
        fetch_extent.xMinimum() - buffer,
        fetch_extent.yMinimum() - buffer,
        fetch_extent.xMaximum() + buffer,
        fetch_extent.yMaximum() + buffer
      ),
      target_crs
    )
    
    # if the crs is specified, transform the area
    if new_crs is not None:
      transform = QgsCoordinateTransform(target_crs, new_crs, QgsProject.instance())
      self.FETCH_AREA = QgsReferencedRectangle(transform.transformBoundingBox(fetch_area), new_crs)
    else:
      self.FETCH_AREA = fetch_area
  
  # get the fetch area as a polygon vector layer
  def fetchAreaAsVectorLayer(self):
    vec_layer = QgsVectorLayer("Polygon?crs=" + self.FETCH_AREA.crs().authid(), "fetch_area", "memory")
    ft = QgsFeature()
    ft.setGeometry(QgsGeometry.fromRect(self.FETCH_AREA))
    vec_layer.dataProvider().addFeatures([ft])    
    return(vec_layer)
      
  # set information about the map tile
  def setTileMapArgs(self, parameters, context, feedback, geom_type = None):
    # set parameters (from UIs)
    self.TILEMAP_ARGS["URL"] = self.parameterAsString(parameters,"TILEMAP_URL", context)
    self.TILEMAP_ARGS["CRS"] = self.parameterAsCrs(parameters,"TILEMAP_CRS", context)
    z = self.parameterAsInt(parameters, "TILEMAP_ZOOM", context) #used later
    self.TILEMAP_ARGS["Z"] = z
    self.TILEMAP_ARGS["GEOM_TYPE"] = geom_type
    
    # set the extent using self.FETCH_AREA
    if self.FETCH_AREA is not None:
      lng_min = self.FETCH_AREA.xMinimum()
      lng_max = self.FETCH_AREA.xMaximum()
      lat_min = self.FETCH_AREA.yMinimum()
      lat_max = self.FETCH_AREA.yMaximum()
      
      # Note that YMIN is obtained from lat_max / YMAX is from lat_min
      self.TILEMAP_ARGS["XMIN"] = int(2**(z+7) * (lng_min / 180 + 1) / 256)
      self.TILEMAP_ARGS["XMAX"] = int(2**(z+7) * (lng_max / 180 + 1) / 256)
      self.TILEMAP_ARGS["YMIN"] = int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat_max)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
      self.TILEMAP_ARGS["YMAX"] = int(2**(z+7) / math.pi * (-math.atanh(math.sin(math.pi/180*lat_min)) + math.atanh(math.sin(math.pi/180*85.05112878))) / 256)
    
    # finally check if there are values in required fields
    if self.TILEMAP_ARGS["URL"] is not None and self.TILEMAP_ARGS["CRS"] is not None and\
      self.TILEMAP_ARGS["Z"] is not None and self.FETCH_AREA is not None:
        self.TILEMAP_ARGS["SET"] = True
  
  
  # set information about the map tile
  def setOsmArgs(self, parameters, context, feedback, geom_type=None):
    self.TILEMAP_ARGS["URL"] = self.parameterAsString(parameters, "OSM_URL", context)
    self.OSM_ARGS["GEOM_TYPE"] = geom_type
    self.OSM_ARGS["QUICKOSM_ARGS"]["KEY"] = self.parameterAsString(parameters, "OSM_KEY", context)
    self.OSM_ARGS["QUICKOSM_ARGS"]["VALUE"] = self.parameterAsString(parameters, "OSM_VALUE", context)
    self.OSM_ARGS["QUICKOSM_ARGS"]["TIMEOUT"] = self.parameterAsDouble(parameters, "OSM_TIMEOUT", context)
    
    if self.FETCH_AREA is not None:
      lng_min_str = str(self.FETCH_AREA.xMinimum())
      lng_max_str = str(self.FETCH_AREA.xMaximum())
      lat_min_str = str(self.FETCH_AREA.yMinimum())
      lat_max_str = str(self.FETCH_AREA.yMaximum())
      crs_str = self.FETCH_AREA.crs().authid()
      self.OSM_ARGS["QUICKOSM_ARGS"]["FETCH_EXTENT"] = f"{lng_min_str},{lng_max_str},{lat_min_str},{lat_max_str} [{crs_str}]"
      
    if self.OSM_ARGS["GEOM_TYPE"] is not None and self.OSM_ARGS["QUICKOSM_ARGS"]["FETCH_EXTENT"] is not None and \
      self.OSM_ARGS["QUICKOSM_ARGS"]["KEY"] is not None and self.OSM_ARGS["QUICKOSM_ARGS"]["VALUE"] is not None:
        self.OSM_ARGS["SET"] = True
  
  # to set the parameters for using data over the Internet
  def setWebFetchArgs(self, parameters, context, feedback):
    pass
  
  # fetch features from the map tile
  def fetchFeaturesFromTile(self, parameters, context, feedback):
    
    # if not all the parameters were set, stop
    if self.TILEMAP_ARGS["SET"] is not True:
      sys.exit(self.tr("NOT required parameters are filled"))
    
    # initialize the vector layer  
    vec_layer = QgsVectorLayer(
      self.TILEMAP_ARGS["GEOM_TYPE"] + "?crs=" + self.TILEMAP_ARGS["CRS"].authid() + "&index=yes",
      baseName = "layer_from_tile", 
      providerLib = "memory"
      )
    vec_pr = vec_layer.dataProvider()
    
    # iterator and the number of tiles
    iter_obj = enumerate(itertools.product(list(range(self.TILEMAP_ARGS["XMIN"], self.TILEMAP_ARGS["XMAX"]+1)), list(range(self.TILEMAP_ARGS["YMIN"],self.TILEMAP_ARGS["YMAX"]+1))))
    n_tiles = (self.TILEMAP_ARGS["XMAX"] - self.TILEMAP_ARGS["XMIN"] + 1) * (self.TILEMAP_ARGS["YMAX"] - self.TILEMAP_ARGS["YMIN"] + 1)

    # fetch features from each tile
    # txy is a tuple of (tx, ty)
    def fetchFromSingleTile(i, txy):
      tx, ty = txy
      # set URL and fetch data
      url = self.TILEMAP_ARGS["URL"].replace("{z}", str(self.TILEMAP_ARGS["Z"])).replace("{x}", str(tx)).replace("{y}",str(ty))
      vec_from_tile = QgsVectorLayer(url, "v", "ogr")      
      
      # give feedback
      feedback.pushInfo(f"({i+1}/{n_tiles}) Fetched from: {url}")
      return tx, ty, vec_from_tile
    
    # fetch procedure is done in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
      results = executor.map(lambda args: fetchFromSingleTile(*args), iter_obj)
    
    # add features to the layer
    for tx, ty, vec_from_tile in results:
      
      # if there are features
      if vec_from_tile.featureCount() > 0:        
        vec_from_tile_rev = self.modifyFeaturesFromTile(vec_from_tile, self.TILEMAP_ARGS["Z"], tx, ty)
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
  def fetchFeaturesFromWeb(self, parameters, context, feedback):
    if not self.WEBFETCH_ARGS["SET"]:
      return
    # if login is needed, session is also needed
    if self.WEBFETCH_ARGS["LOGIN"] is not None:
      try:
        session = self.WEBFETCH_ARGS["LOGIN"]["SESSION"]
      except:
        sys.exit(self.tr("Session must be given for Log-in procedure"))
    else:
      session = requests.Session()
        
    # start downloading
    iter_obj = enumerate(self.WEBFETCH_ARGS["URL"])
    n_url = len(self.WEBFETCH_ARGS["URL"])
    def fetchFromSingleURL(i, url):
      
      feedback.pushInfo(f"({i+1}/{n_url}) Downloading " + url)
      response = session.get(url)
      
      # if download was succeeded, save as a file
      if response.status_code == 200:
        feedback.pushInfo(self.tr("... Succeeded!"))
        
        # write the contents in a temporary file
        tmp_file = os.path.join(
          os.path.normpath(os.path.dirname(QgsProcessingUtils.generateTempFilename(""))), 
          str(uuid.uuid4()) + self.WEBFETCH_ARGS["ARCHIVED"]
          )
        with open(tmp_file, "wb") as f:
          f.write(response.content)
        
        # if it is a zip file, unpack it
        if self.WEBFETCH_ARGS["ARCHIVED"]:
          zip_dir = os.path.splitext(tmp_file)[0]
          shutil.unpack_archive(tmp_file, zip_dir)
          archived_files = glob.glob(os.path.join(zip_dir, "*"))
          for a_file in archived_files:
            self.WEBFETCH_ARGS["DOWNLOADED_FILE"].append(a_file)
        else:
          self.WEBFETCH_ARGS["DOWNLOADED_FILE"].append(tmp_file)
          
      # if the download was not succeeded
      else:
        feedback.pushInfo(self.tr("... ERROR!"))
      return
      
    # fetch procedure is done in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
      executor.map(lambda args: fetchFromSingleURL(*args), iter_obj)
      
  
  # function to create a feature from the downloaded file(s)
  def mergeFetchedFeatures(self, parameters, context, feedback):
    pass
  
  
  # fetch features from the map tile
  def fetchFeaturesFromOsm(self, context, feedback):
    if self.OSM_ARGS["SET"]:
      
      quickosm_results = processing.run(
        "quickosm:downloadosmdataextentquery", 
        {
          "KEY": self.OSM_ARGS["QUICKOSM_ARGS"]["KEY"],
          "VALUE": self.OSM_ARGS["QUICKOSM_ARGS"]["VALUE"],
          "EXTENT": self.OSM_ARGS["QUICKOSM_ARGS"]["FETCH_EXTENT"],
          "TIMEOUT": self.OSM_ARGS["QUICKOSM_ARGS"]["TIMEOUT"],
          "SERVER": self.OSM_ARGS["URL"],
          "FILE": "TEMPORARY_OUTPUT"
        },
        # context = context, # not pass the context, so as not to show the warnings
        feedback = feedback
      )
      
      
      if self.OSM_ARGS["GEOM_TYPE"] == "Point":
        vec_layer = quickosm_results["OUTPUT_POINTS"]
      elif self.OSM_ARGS["GEOM_TYPE"] == "Linestring":
        vec_layer = quickosm_results["OUTPUT_LINES"]
      elif self.OSM_ARGS["GEOM_TYPE"] == "Multilinestring":
        vec_layer = quickosm_results["OUTPUT_MULTILINESTRINGS"]
      elif self.OSM_ARGS["GEOM_TYPE"] == "Polygon":
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
