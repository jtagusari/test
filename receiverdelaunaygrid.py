from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP)
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterNumber,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterExtent
  )


from .receiverabstract import receiverabstract
import os

class receiverdelaunaygrid(receiverabstract):
  PARAMETERS = { 
    "BUILDING": {
      "crs_referrence": True, # this parameter is used as CRS referrence
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "buildingGeomPath",
      "save_layer_get_path": True
    },    
    "SOURCE": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Source layer"),
        "types": [QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine,QgsProcessing.TypeVectorPolygon]
      },
      "n_mdl": "sourceGeomPath",
      "save_layer_get_path": True
    },    
    "FENCE_EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("receiverfacade","Calculation extent"),
        "defaultValue": None,
        "optional": True,
      }
    },
    "MAX_PROP_DIST": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum propagation distance between sources and receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 500.0, "maxValue": 2000.0
      },
      "n_mdl": "maxPropDist"
    },
    "ROAD_WIDTH": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Road width (m), where no receivers will be set closer than it"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 2.0, "maxValue": 20.0
      },
      "n_mdl": "roadWidth"
    },
    "MAX_AREA": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Maximum trianglar area (m2)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 10.0, "defaultValue": 500.0, "maxValue": 10000.0
      },
      "n_mdl": "maxArea"
    },
    "HEIGHT": {
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Height of receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 0.01, "defaultValue": 4.0, "maxValue": 100.0
      },
      "n_mdl": "height"
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Receivers of delaunay" )
      }
    },
    "TRIANGLE": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Triangles of delaunay" )
      }
    }

  }
  
    
  def initAlgorithm(self, config):
    self.initParameters()

  def processAlgorithm(self, parameters, context, feedback):    
    self.initNoiseModellingPath(
      {
        "GROOVY_SCRIPT": os.path.join(os.path.dirname(__file__), "noisemodelling","hriskscript", "receiverdelaunaygrid.groovy"),
        "RECEIVER": os.path.join("%nmtmp%", "RECEIVERS.geojson"),
        "TRIANGLE": os.path.join("%nmtmp%", "TRIANGLES.geojson")
      }
    )
    self.initNoiseModellingArg(parameters, context, feedback)
    self.fenceExtentAsWkt(parameters, context, feedback)
    
    # execute groovy script using wps_scripts
    self.execNoiseModellingCmd(parameters, context, feedback)
      
    dest_id_rcv = self.importNoiseModellingResultsAsSink(parameters, context, "OUTPUT",self.NOISEMODELLING["RECEIVER"])
    dest_id_tri = self.importNoiseModellingResultsAsSink(parameters, context, "TRIANGLE",self.NOISEMODELLING["TRIANGLE"])
        
    return {"OUTPUT": dest_id_rcv, "TRIANGLE": dest_id_tri}
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):   
    return {}

  def displayName(self):
    return self.tr("Delaunay grid")

  def group(self):
    return self.tr('Set receivers')

  def groupId(self):
    return 'receiver'

  def createInstance(self):
    return receiverdelaunaygrid()
