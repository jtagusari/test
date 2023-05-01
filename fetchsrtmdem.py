from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsCoordinateReferenceSystem,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsProcessingParameterCrs, 
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterRasterDestination,
  QgsProperty,
  QgsProcessingUtils,
  QgsProcessingParameterString,
  QgsRasterLayer
  )
from qgis import processing

from .fetchabstract import fetchabstract

import sys
import math
import os
import requests
import shutil
import re

class fetchsrtmdem(fetchabstract):
  
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Extent of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Target CRS")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Buffer of the calculation area based on Target CRS"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "MAP_BASEURL": {
      "ui_func": QgsProcessingParameterString,
      "advanced": True,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Base url to find SRTM data"),
        "defaultValue": "https://e4ftl01.cr.usgs.gov/DP133/SRTM/SRTMGL1.003/2000.02.11/"
      }
    },
    "USERNAME": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Username to login SRTM data system")
      }
    },
    "PASSWORD": {
      "ui_func": QgsProcessingParameterString,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Password to login SRTM data system")
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","Output")
      }
    },
    "OUTPUT_RASTER": {
      "ui_func": QgsProcessingParameterRasterDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchsrtmdem","DEM (Raster output)" )
      }
    }
  }  
  
  def checkCalcArea(self):
    # check whether the CRS is long-lat coordinates
    if self.CALC_AREA.crs().isGeographic() is not True:
      sys.exit(self.tr("The Set CRS is NOT a Geographic Coordinate System"))
      
    if self.CALC_AREA.yMinimum() < -56 or self.CALC_AREA.yMaximum() > 59 : 
      sys.exit(self.tr("The Box is out of SRTM-covered area"))

  def setMapUrlMeta(self, parameters, context, feedback):
    
    # set url and file names
    lat_min = math.floor(self.CALC_AREA.yMinimum())
    lat_max = math.ceil(self.CALC_AREA.yMaximum())
    lng_min = math.floor(self.CALC_AREA.xMinimum())
    lng_max = math.ceil(self.CALC_AREA.xMaximum())
    
    self.MAP_URL["BASEURL"] = self.parameterAsString(parameters, "MAP_BASEURL", context)
    self.MAP_URL["URL"] = []
    self.MAP_URL["DIR"] = os.path.normpath(os.path.dirname(QgsProcessingUtils.generateTempFilename("")))
    self.MAP_URL["FILE"] = []
    for lat in range(lat_min, lat_max):
      for lng in range(lng_min, lng_max):
        lng_str = f"{lng:+04}".replace("+","E").replace("-","W")
        lat_str = f"{lat:+03}".replace("+","N").replace("-","S")
        self.MAP_URL["URL"].append(
          self.MAP_URL["BASEURL"] + f"{lat_str}{lng_str}.SRTMGL1.hgt.zip"
        )    
        self.MAP_URL["FILE"].append(
          os.path.join(self.MAP_URL["DIR"], f"{lat_str}{lng_str}.SRTMGL1.hgt.zip")
        )
    
    # set login data
    login_url = "https://urs.earthdata.nasa.gov"
    session = requests.Session()
    login_html = session.get(login_url).text
    token = re.search(
      r'<form[^>]*id="login".*?>[\s\S]*?<input[^>]*name="authenticity_token"[^>]*value="([^"]*)"[^>]*>', 
      login_html
    ).group(1)
    
    self.MAP_URL["LOGIN"] = {
      "URL": login_url + "/login",
      "PARAMETERS": {
        "utf8": "✓",
        "authenticity_token": token,
        "username": self.parameterAsString(parameters, "USERNAME", context),
        "password": self.parameterAsString(parameters, "PASSWORD", context),      
      }
    }
    
    session.post(
      url = self.MAP_URL["LOGIN"]["URL"], 
      data = self.MAP_URL["LOGIN"]["PARAMETERS"]
    )
    
    # set that it is zipped file
    self.MAP_URL["ZIPPED"] = True
    
    if self.MAP_URL["URL"] is not None and self.MAP_URL["FILE"] is not None and \
      self.MAP_URL["LOGIN"] is not None:
          self.MAP_URL["SET"] = True
    
    # return session, which will be used at downloading the data
    return session
  
  
  # create the raster from downloaded hgt files
  def createMergedFeature(self, parameters, context, feedback):
    # list the files that has hgt extension
    files_to_be_merged = []
    for file in self.MAP_URL["DOWNLOADED_FILE"]:
      if re.search(".hgt", file):
        files_to_be_merged.append(file)
    
    # if there are no files
    if len(files_to_be_merged) == 0:
      sys.exit(self.tr("No SRTM files were downloaded!"))
    
    # if there are only a file
    elif len(files_to_be_merged) == 1:
      return QgsRasterLayer(files_to_be_merged[0], "SRTM")
    
    # if there are multiple files
    else:
      rasters = []
      for file in files_to_be_merged:
        rasters.append(QgsRasterLayer(file + "|layername=1", "SRTM"))
      raster_layer = processing.run(
        "gdal:merge",{
          "INPUT": rasters,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      return raster_layer
    
  # initialize of the algorithm  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()

  # execution of the algorithm
  def processAlgorithm(self, parameters, context, feedback):
    # set the calculation area, of which CRS is the same as SRTM's
    self.setCalcArea(parameters,context,feedback,QgsCoordinateReferenceSystem("EPSG:4326"))
    self.checkCalcArea()
    
    # set the meta information for obtaining SRTM data
    session = self.setMapUrlMeta(parameters, context, feedback)
    
    # download files using the session info
    self.fetchFeaturesFromURL(parameters, context, feedback, session)
    
    # create raster from file(s)
    dem_raster = self.createMergedFeature(parameters, context, feedback)
    
    # clip the raster because it is too large as a point vector
    dem_raster_clipped = processing.run(
      "gdal:cliprasterbyextent", 
      {
        "INPUT": dem_raster,
        "PROJWIN": self.CALC_AREA,
        "OUTPUT": self.parameterAsOutputLayer(parameters, "OUTPUT_RASTER", context)
      }
    )["OUTPUT"]
    
    # create vector layer from the raster
    dem_raw = processing.run(
      "native:pixelstopoints",{
        "INPUT_RASTER": dem_raster_clipped,
        "RASTER_BAND": 1,
        "FIELD_NAME": "alti",
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    # CRS transform    
    dem_transformed = self.transformToTargetCrs(parameters,context,feedback,dem_raw)
       
    # substitute self constant with the fetched vector layer
    dem_final = dem_transformed    
    
    (sink, dest_id) = self.parameterAsSink(
          parameters, "OUTPUT", context,
          dem_final.fields(), dem_final.wkbType(), dem_final.sourceCrs()
          )
    sink.addFeatures(dem_final.getFeatures())
    
    return {"OUTPUT": dest_id, "OUTPUT_RASTER": dem_raster}   
    
  
  def displayName(self):
    return self.tr("Elevation points (DEM)")

  def group(self):
    return self.tr('Fetch geometries (SRTM)')

  def groupId(self):
    return 'fetchsrtmgeometry'

  def createInstance(self):
    return fetchsrtmdem()
