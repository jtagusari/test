from qgis.PyQt.QtCore import (QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessingContext,
  QgsProcessingFeedback,
  QgsCoordinateReferenceSystem
  )


from .algabstract import algabstract
from qgis import processing
import os

class receiverabstract(algabstract):
  def fenceExtentAsLayer(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None:
    fence_extent = self.parameterAsString(parameters, "FENCE_EXTENT", context)
    try:
      crs_referrence = self.NOISEMODELLING["WPS_ARGS"]["inputSRID"]
      fence_layer = processing.run(
        "native:extenttolayer",
        {
          "INPUT": fence_extent,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      fence_transformed = processing.run(
        "native:reprojectlayer",
        {
          "INPUT": fence_layer,
          "TARGET_CRS": QgsCoordinateReferenceSystem(f"EPSG:{crs_referrence}"),
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      fence_path = os.path.join(self.NOISEMODELLING["TEMP_DIR"], "FENCE.geojson")
      self.saveVectorLayer(fence_transformed, fence_path)
      self.NOISEMODELLING["WPS_ARGS"]["fenceGeomPath"] = '"' + fence_path + '"'
      
    except:
      pass
  
  def fenceExtentAsWkt(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback) -> None:
    fence_extent = self.parameterAsString(parameters, "FENCE_EXTENT", context)
    try:
      fence_layer = processing.run(
        "native:extenttolayer",
        {
          "INPUT": fence_extent,
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      fence_wgs = processing.run(
        "native:reprojectlayer",
        {
          "INPUT": fence_layer,
          "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:4326"),
          "OUTPUT": "TEMPORARY_OUTPUT"
        }
      )["OUTPUT"]
      
      self.NOISEMODELLING["WPS_ARGS"]["fence"] = '"' + fence_wgs.getFeature(1).geometry().asWkt() + '"'
      
    except:
      pass