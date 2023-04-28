from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP
  )
from qgis.core import (
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

from .algabstract import algabstract

# abstract class for fetching information from web
class fetchabstract(algabstract):
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchabstract","Extent of the calculation area")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchabstract","Target CRS")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchabstract","Buffer of the calculation area based on Target CRS"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchabstract","Output")
      }
    }
  }
  
  CALC_AREA = None
    
  MAP_TILE = {
    "SET": False,
    "URI": None,
    "CRS": None,
    "GEOM_TYPE": None,
    "Z": None,
    "XMIN": None, "XMAX": None, "YMIN": None, "YMAX": None
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
    
  # set calc_area, using new_crs (e.g. QgsCoordinateReferenceSystem('EPSG:4326'))
  def setCalcArea(self, parameters, context, feedback, new_crs = None):
    # get CRS
    target_crs = self.parameterAsCrs(parameters, "TARGET_CRS", context)
    
    # check whether the CRS is x-y coordinates
    if target_crs.isGeographic():
      sys.exit(self.tr("The Set CRS is NOT a Cartesian Coordinate System"))
    
    extent = self.parameterAsExtent(
      parameters, "EXTENT", context, 
      self.parameterAsCrs(parameters, "TARGET_CRS", context)
      )
    
    buffer = self.parameterAsDouble(parameters, "BUFFER",context)
    
    calc_area = QgsReferencedRectangle(
      QgsRectangle(
        extent.xMinimum() - buffer,
        extent.yMinimum() - buffer,
        extent.xMaximum() + buffer,
        extent.yMaximum() + buffer
      ),
      target_crs
    )
    
    if new_crs is not None:
      transform = QgsCoordinateTransform(target_crs, new_crs, QgsProject.instance())
      self.CALC_AREA = QgsReferencedRectangle(transform.transformBoundingBox(calc_area), new_crs)
    else:
      self.CALC_AREA = calc_area
  
  
  def calcAreaAsVectorLayer(self):
    vec_layer = QgsVectorLayer("Polygon?crs=" + self.CALC_AREA.crs().authid(), "calc_area", "memory")
    ft = QgsFeature()
    ft.setGeometry(QgsGeometry.fromRect(self.CALC_AREA))
    vec_layer.dataProvider().addFeatures([ft])
    
    return(vec_layer)
      
  # set information about the map tile
  def setMapTileMeta(self, uri, crs, geom_type, z):
    self.MAP_TILE["URI"] = uri
    self.MAP_TILE["CRS"] = crs
    self.MAP_TILE["GEOM_TYPE"] = geom_type
    self.MAP_TILE["Z"] = z
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
    
    if self.MAP_TILE["URI"] is not None and self.MAP_TILE["CRS"] is not None and\
      self.MAP_TILE["GEOM_TYPE"] is not None and self.MAP_TILE["Z"] is not None and \
      self.MAP_TILE["XMIN"] is not None and self.MAP_TILE["XMAX"] is not None and \
      self.MAP_TILE["YMIN"] is not None and self.MAP_TILE["YMAX"] is not None:
        self.MAP_TILE["SET"] = True
  
  # fetch features from the map tile
  def fetchFeaturesFromTile(self):
    if self.MAP_TILE["SET"]:
      init_string = self.MAP_TILE["GEOM_TYPE"] + "?crs=" + self.MAP_TILE["CRS"].authid() + "&index=yes"
      vec_layer = QgsVectorLayer(init_string,baseName = "layer_from_tile", providerLib = "memory")
      vec_pr = vec_layer.dataProvider()
    
      # fetch features for each tx and ty
      for tx, ty in itertools.product(list(range(self.MAP_TILE["XMIN"], self.MAP_TILE["XMAX"]+1)), list(range(self.MAP_TILE["YMIN"],self.MAP_TILE["YMAX"]+1))):
        uri = self.MAP_TILE["URI"].replace("{z}", str(self.MAP_TILE["Z"])).replace("{x}", str(tx)).replace("{y}",str(ty))
        vec_from_tile = QgsVectorLayer(uri, "v", "ogr")
        
        if vec_from_tile.featureCount() > 0:
          vec_from_tile_rev = self.modifyFeaturesFromTile(vec_from_tile, self.MAP_TILE["Z"], tx, ty)
          for ft in vec_from_tile_rev.getFeatures():
            # set the fields if it is not set 
            if vec_layer.fields().count() == 0:
              vec_pr.addAttributes([ft.fields().at(idx) for idx in range(ft.fields().count())])
              vec_layer.updateFields()
            vec_pr.addFeatures([ft])
      
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
