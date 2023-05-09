from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProject,
  QgsProcessingLayerPostProcessorInterface,
  QgsProcessingParameterExtent,
  QgsProcessingParameterDistance,
  QgsProcessingParameterEnum, 
  QgsProcessingParameterCrs, 
  QgsProcessingParameterVectorDestination,
  QgsProcessingParameterRasterDestination,
  QgsProcessingParameterNumber,
  QgsCoordinateReferenceSystem
  )
from qgis import processing

from .fetchabstract import fetchabstract
import uuid


from .fetchabstract import fetchabstract
from .receiverabstract import receiverabstract

class fetchjageom(fetchabstract, receiverabstract):
  PARAMETERS = {  
    "EXTENT": {
      "ui_func": QgsProcessingParameterExtent,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("fetchjageom","Extent for fetching data")
      }
    },
    "TARGET_CRS": {
      "ui_func": QgsProcessingParameterCrs,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Target CRS (Cartesian coordinates)")
      }
    },
    "BUFFER": {
      "ui_func": QgsProcessingParameterDistance,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Buffer of the fetch area (using Target CRS)"),
        "defaultValue": 0.0,
        "parentParameterName": "TARGET_CRS"
      }
    },
    "RECEIVER_TYPE": {
      "ui_func": QgsProcessingParameterEnum,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Set receiver points?"),
        "options":[
          QT_TRANSLATE_NOOP("fetchjageom","None"),
          QT_TRANSLATE_NOOP("fetchjageom","Receivers at facade"),
          QT_TRANSLATE_NOOP("fetchjageom","Receivers at delaunary grid"),
          QT_TRANSLATE_NOOP("fetchjageom","Receivers at regular grid")
        ],
        "defaultValue": 0,
        "allowMultiple": True
      }
    },
    
    # "FENCE": {
    #   "ui_func": QgsProcessingParameterFeatureSource,
    #   "ui_args":{
    #     "description": QT_TRANSLATE_NOOP("fetchjageom","Fence layer, within which receivers are generated"),
    #     "types": [QgsProcessing.TypeVectorPolygon],
    #     "optional": True,
    #     "defaultValue": None
    #   }
    # },    
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
        "description": QT_TRANSLATE_NOOP("fetchjageom","Maximum propagation distance between sources and receivers (m)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 100.0, "defaultValue": 500.0, "maxValue": 2000.0
      },
      "n_mdl": "maxPropDist"
    },
    "ROAD_WIDTH": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Road width (m), where no receivers will be set closer than it"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 1.0, "defaultValue": 2.0, "maxValue": 20.0
      },
      "n_mdl": "roadWidth"
    },
    "MAX_AREA": {
      "advanced": True,
      "ui_func": QgsProcessingParameterNumber,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Maximum trianglar area (m2)"),
        "type": QgsProcessingParameterNumber.Double,
        "minValue": 10.0, "defaultValue": 500.0, "maxValue": 10000.0
      },
      "n_mdl": "maxArea"
    },
    # "ISO_SURFACE": {
    #   "advanced": True,
    #   "ui_func": QgsProcessingParameterBoolean,
    #   "ui_args": {
    #     "description": QT_TRANSLATE_NOOP("receiverdelaunaygrid","Whether isosurfaces will be visible at the location of buildings"),
    #     "defaultValue": False
    #   },
    #   "n_mdl": "isoSurfaceInBuildings"
    # }
    "CALC_AREA": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Calculation area" )
      },
      "visibleByDefault": False
    },
    "ROAD": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Roads" )
      },
      "visibleByDefault": True
    },
    "BUILDING": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Buildings" )
      },
      "visibleByDefault": True
    },    
    "RECEIVER_FACADE": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Receivers at facade" )
      }     ,
      "visibleByDefault": False
    },    
    "RECEIVER_DELAUNAY": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Receivers of delaunay" )
      },
      "visibleByDefault": False
    },
    "TRIANGLE_DELAUNAY": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Triangles of delaunay" )
      },
      "visibleByDefault": False
    },    
    "DEM": {
      "ui_func": QgsProcessingParameterVectorDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Elevation point (DEM)" )
      },
      "visibleByDefault": False
    },    
    "DEM_RASTER": {
      "ui_func": QgsProcessingParameterRasterDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Elevation raster (DEM)" )
      },
      "visibleByDefault": False
    },
    "POP": {
      "ui_func": QgsProcessingParameterRasterDestination,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("fetchjageom","Population" )
      },
      "visibleByDefault": True
    }
  }
  
  PROC_RESULTS = {}
  GRP_ID = ""
    
  
  def initAlgorithm(self, config):    
    self.initUsingCanvas()
    self.initParameters()
    
  
  def fetchPopulation(self, parameters, context, feedback):
    self.PROC_RESULTS["POP"] = processing.run(
      "hrisk:fetchjapop",
      {
        "EXTENT": self.parameterAsString(parameters, "EXTENT", context), # Note that parameterAsExtent is NG because CRS is not included
        "TARGET_CRS": self.parameterAsCrs(parameters, "TARGET_CRS", context),
        "BUFFER": self.parameterAsDouble(parameters, "BUFFER",context),
        "OUTPUT": self.parameterAsOutputLayer(parameters, "POP", context)
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
  
  
  def fetchRoad(self, parameters, context, feedback):
    self.PROC_RESULTS["ROAD"] = processing.run(
      "hrisk:fetchjaroad",
      {
        "EXTENT": self.parameterAsString(parameters, "EXTENT", context),# Note that parameterAsExtent is NG because CRS is not included
        "TARGET_CRS": self.parameterAsCrs(parameters, "TARGET_CRS", context),
        "BUFFER": self.parameterAsDouble(parameters, "BUFFER",context),
        "OUTPUT": self.parameterAsOutputLayer(parameters, "ROAD", context)
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
    
    
  def fetchBuilding(self, parameters, context, feedback):
    
    bldg_raw = processing.run(
      "hrisk:fetchjabuilding",
      {
        "EXTENT": self.parameterAsString(parameters, "EXTENT", context),# Note that parameterAsExtent is NG because CRS is not included
        "TARGET_CRS": self.parameterAsCrs(parameters, "TARGET_CRS", context),
        "BUFFER": self.parameterAsDouble(parameters, "BUFFER",context),
        "OUTPUT": "TEMPORARY_OUTPUT"
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
    
    self.PROC_RESULTS["BUILDING"] = processing.run(
      "hrisk:estimatepopulationofbuilding",
      {
        "BUILDING": bldg_raw,
        "POP": self.PROC_RESULTS["POP"],
        "OUTPUT": self.parameterAsOutputLayer(parameters, "BUILDING", context)
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
    
  def fetchDem(self, parameters, context, feedback):
    dem_processing = processing.run(
      "hrisk:fetchjadem",
      {
        "EXTENT": self.parameterAsString(parameters, "EXTENT", context),
        "TARGET_CRS": self.parameterAsCrs(parameters, "TARGET_CRS", context),
        "BUFFER": self.parameterAsDouble(parameters, "BUFFER",context),
        "OUTPUT": self.parameterAsOutputLayer(parameters, "DEM", context),
        "OUTPUT_RASTER": self.parameterAsOutputLayer(parameters, "DEM_RASTER", context)
      },
      context = context,
      feedback = feedback
    )
    self.PROC_RESULTS["DEM"] = dem_processing["OUTPUT"]
    self.PROC_RESULTS["DEM_RASTER"] = dem_processing["OUTPUT_RASTER"]
    
  def setReceiverFacade(self, parameters, context, feedback):
    self.PROC_RESULTS["RECEIVER_FACADE"] = processing.run(
      "hrisk:receiverfacade",
      {
        "BUILDING": self.PROC_RESULTS["BUILDING"],
        "SOURCE": self.PROC_RESULTS["ROAD"],
        "DELTA": self.parameterAsDouble(parameters, "DELTA", context),
        "HEIGHT": self.parameterAsDouble(parameters, "HEIGHT", context),
        "OUTPUT": self.parameterAsOutputLayer(parameters, "RECEIVER_FACADE", context)
      },
      context = context,
      feedback = feedback
    )["OUTPUT"]
  

  def setReceiverDelaunayGrid(self, parameters, context, feedback):
    delaunay_processing = processing.run(
      "hrisk:receiverdelaunaygrid",
      {
        "BUILDING": self.PROC_RESULTS["BUILDING"],
        "SOURCE": self.PROC_RESULTS["ROAD"],
        "MAX_PROP_DIST": self.parameterAsDouble(parameters, "MAX_PROP_DIST", context),
        "ROAD_WIDTH": self.parameterAsDouble(parameters, "ROAD_WIDTH", context),
        "MAX_AREA": self.parameterAsDouble(parameters, "MAX_AREA", context),
        "HEIGHT": self.parameterAsDouble(parameters, "HEIGHT", context),
        "OUTPUT": self.parameterAsOutputLayer(parameters, "RECEIVER_DELAUNAY", context),
        "TRIANGLE": self.parameterAsOutputLayer(parameters, "TRIANGLE_DELAUNAY", context)
      },
      context = context,
      feedback = feedback
    )
    
    self.PROC_RESULTS["RECEIVER_DELAUNAY"] = delaunay_processing["OUTPUT"]
    self.PROC_RESULTS["TRIANGLE_DELAUNAY"] = delaunay_processing["TRIANGLE"]

  def processAlgorithm(self, parameters, context, feedback):
    feedback.pushInfo(self.tr("Configurations"))
    feedback.setProgress(0)    
    
    self.GRP_ID = "ja_geom_" + str(uuid.uuid4())[:6]
    
    feedback.pushInfo(self.tr("Set calculation area"))
    self.setCalcArea(parameters,context,feedback)
    self.PROC_RESULTS["CALC_AREA"] = self.calcAreaAsVectorLayer()
    feedback.setProgress(5)      
    
    feedback.pushInfo(self.tr("Fetch geometry of population"))
    self.fetchPopulation(parameters, context, feedback)
    feedback.setProgress(10)    
    
    feedback.pushInfo(self.tr("Fetch geometry of roads"))
    self.fetchRoad(parameters, context, feedback)
    feedback.setProgress(15)    
    
    feedback.pushInfo(self.tr("Fetch geometry of buildings and Assign the population"))
    self.fetchBuilding(parameters, context, feedback)
    feedback.setProgress(25)
    
    feedback.pushInfo(self.tr("Fetch geometry of DEM"))
    self.fetchDem(parameters, context, feedback)
    feedback.setProgress(50)    
    
    if 1 in self.parameterAsEnums(parameters, "RECEIVER_TYPE", context):
    
      feedback.pushInfo(self.tr("Set receivers at building facade"))
      self.setReceiverFacade(parameters, context, feedback)
      feedback.setProgress(75) 
         
    if 2 in self.parameterAsEnums(parameters, "RECEIVER_TYPE", context):
    
      feedback.pushInfo(self.tr("Set receivers of delaunay grid"))
      
    feedback.setProgress(100)
      
    return self.PROC_RESULTS
    
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    global jageom_postprocessors
    jageom_postprocessors = []
    
    QgsProject.instance().layerTreeRoot().insertGroup(0, self.GRP_ID)
    
    layer_dict = context.layersToLoadOnCompletion()
    for i, path in enumerate(layer_dict.keys()):
      if len([k for k, v in self.PROC_RESULTS.items() if v == path]) == 1:
        vis = self.PARAMETERS.get([k for k, v in self.PROC_RESULTS.items() if v == path][0]).get("visibleByDefault")
        jageom_postprocessors.append(jageomPostProcessor(self.GRP_ID, vis, context.layerToLoadOnCompletionDetails(path).postProcessor()))
        context.layerToLoadOnCompletionDetails(path).setPostProcessor(jageom_postprocessors[i])
    return {}


  def displayName(self):
    return self.tr("All geometries and set receivers")

  def group(self):
    return self.tr('Fetch geometries (Ja)')

  def groupId(self):
    return 'fetchjageometry'

  def createInstance(self):
    return fetchjageom()

class jageomPostProcessor (QgsProcessingLayerPostProcessorInterface):
  def __init__(self, group_name, visibility = True, existing_postprocessor = None):
    self.group_name = group_name
    self.visibility = visibility
    self.existing_pp = existing_postprocessor
    super().__init__()
    
  def postProcessLayer(self, layer, context, feedback):
    if self.existing_pp != None:
      self.existing_pp.postProcessLayer(layer, context, feedback)
    root = QgsProject.instance().layerTreeRoot()
    vl = root.findLayer(layer.id())
    vl.setItemVisibilityChecked(self.visibility)
    vl_clone = vl.clone()
    grp = root.findGroup(self.group_name)
    if grp != None:
      parent = vl.parent()
      grp.insertChildNode(0, vl_clone)
      parent.removeChildNode(vl)