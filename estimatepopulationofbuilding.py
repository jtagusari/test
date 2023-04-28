from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsFeatureRequest,
  QgsProcessingParameterRasterLayer,
  QgsFeature,
  QgsField,
  QgsFields
  )

from qgis import processing
from .jameshpop import jameshpop
from .algabstract import algabstract

class estimatepopulationofbuilding(algabstract, jameshpop):
  PARAMETERS = {
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuilding","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "POP": {
      "ui_func": QgsProcessingParameterRasterLayer,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuilding","Population layer"),
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuilding","Building with population")
      }
    }
  }
  
  FIELDS = {
    "meshCode":{"type": QVariant.String},
    "nBldgMesh": {"type": QVariant.Int},
    "areaBldg": {"type": QVariant.Double},
    "areaBldgMesh": {"type": QVariant.Double},
    "popMesh": {"type": QVariant.Int},
    "popEst": {"type": QVariant.Double}
  }
  
  def initAlgorithm(self, config):
    self.initParameters()

  def cmptBldgPntLayer(self, bldg_layer, pop_raster):
    
    building_cent_pnt = processing.run(
      "native:centroids",
      {
        "INPUT": bldg_layer,
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    building_cent_pnt_transformed = processing.run(
      "native:reprojectlayer",
      {
        "INPUT": building_cent_pnt,
        "TARGET_CRS" : pop_raster.crs(),
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    # sampling the population from raster
    # the population is stored in the first band (1)
    building_cent_pnt_pop = processing.run(
      "native:rastersampling",
      {
        "INPUT": building_cent_pnt_transformed,
        "RASTERCOPY": pop_raster,
        "COLUMN_PREFIX": "",
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    return(building_cent_pnt_pop)

  def processAlgorithm(self, parameters, context, feedback):
    pop = self.parameterAsRasterLayer(parameters, "POP", context)
    bldg_plg = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback) 
    bldg_pnt = self.cmptBldgPntLayer(bldg_plg, pop)
    
    # initialize the fields
    bldg_fields = QgsFields(bldg_plg.fields())
    for key, arg in self.FIELDS.items():
      if key in bldg_fields.names():
        bldg_fields.remove(bldg_fields.lookupField(key))
      bldg_fields.append(QgsField(key, arg["type"]))
      
    # check the sum of the population and the area of buildings of each mesh
    mesh_info = {}
    for ft_plg, ft_pnt in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures()):
      # get the mesh information from ft_pnt and update ft_plg
      (mesh_str, lng_lat_coords) = self.coordsToMesh(ft_pnt.geometry().vertexAt(0).x(), ft_pnt.geometry().vertexAt(0).y())
      
      # accumlate the information regarding the mesh
      if mesh_info.get(mesh_str) == None:
        mesh_info[mesh_str] = {"popMesh": ft_pnt["1"], "nBldgMesh": 0,"areaBldgMesh": 0.0}
      mesh_info[mesh_str]["nBldgMesh"] += 1
      mesh_info[mesh_str]["areaBldgMesh"] += ft_plg.geometry().area()
    
    # then create sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context,
      bldg_fields, bldg_plg.wkbType(), bldg_plg.sourceCrs()
    )
    
    # add Features
    for ft_plg, ft_pnt in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures()):
      ft_new = QgsFeature(bldg_fields)
      ft_new.setGeometry(ft_plg.geometry())
      for field_name in ft_plg.fields().names():
        if not field_name in list(self.FIELDS.keys()):
          ft_new[field_name] = ft_plg[field_name]
      (mesh_str, lng_lat_coords) = self.coordsToMesh(ft_pnt.geometry().vertexAt(0).x(), ft_pnt.geometry().vertexAt(0).y())
      ft_new["meshCode"]     = mesh_str
      ft_new["nBldgMesh"]    = mesh_info[mesh_str]["nBldgMesh"]
      ft_new["areaBldgMesh"] = mesh_info[mesh_str]["areaBldgMesh"]
      ft_new["areaBldg"]     = ft_new.geometry().area()
      ft_new["popMesh"]      = ft_pnt["1"]
      if ft_pnt["1"] is not None:
        ft_new["popEst"]     = float(ft_pnt["1"]) / ft_new["areaBldgMesh"] * ft_new["areaBldg"]
      sink.addFeature(ft_new)    
              
    return {"OUTPUT": dest_id}
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Estimate populations of buildings")

  def group(self):
    return self.tr("Noise prediction / evaluation")

  def groupId(self):
    return "noisepredictionevaluation"
  
  def createInstance(self):
    return estimatepopulationofbuilding()
