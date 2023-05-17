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
from .algabstract import algabstract
from .worldmesh import (
  cal_meshcode_ex1m_16  
)

class estimatepopulationofbuilding(algabstract):
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
    "meshIdx":{"type": QVariant.Int},
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
    
    bldg_cent_pnt = processing.run(
      "native:centroids",
      {
        "INPUT": bldg_layer,
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    bldg_cent_pnt_transformed = processing.run(
      "native:reprojectlayer",
      {
        "INPUT": bldg_cent_pnt,
        "TARGET_CRS" : pop_raster.crs(),
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    # sampling the population from raster
    # the population is stored in the first band (1)
    bldg_cent_pnt_pop = processing.run(
      "native:rastersampling",
      {
        "INPUT": bldg_cent_pnt_transformed,
        "RASTERCOPY": pop_raster,
        "COLUMN_PREFIX": "pop",
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    
    return bldg_cent_pnt_pop
  
  
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
      
    # define a function to get the mesh index
    def getMeshIdx(x, y):
      x_idx = (x - pop.extent().xMinimum()) // pop.rasterUnitsPerPixelX()
      y_idx = (y - pop.extent().yMinimum()) // pop.rasterUnitsPerPixelY()
      idx = y_idx * pop.width() + x_idx
      return idx
    
    # create sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context,
      bldg_fields, bldg_plg.wkbType(), bldg_plg.sourceCrs()
    )
    
      
    # first loop is to get the mesh information from ft_pnt
    mesh_idx_ft = []
    mesh_info = {}    
    for ft_plg, ft_pnt in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures()):
      
      mesh_idx = getMeshIdx(ft_pnt.geometry().vertexAt(0).x(), ft_pnt.geometry().vertexAt(0).y())
      mesh_idx_ft.append(mesh_idx)
      
      # accumlate the information regarding the mesh
      if mesh_info.get(mesh_idx) == None:
        mesh_info[mesh_idx] = {"meshCode":None, "popMesh": ft_pnt["pop1"], "nBldgMesh": 0,"areaBldgMesh": 0.0}
        if pop.crs().isGeographic():
          mesh_info[mesh_idx]["meshCode"] = cal_meshcode_ex1m_16(ft_pnt.geometry().vertexAt(0).y(), ft_pnt.geometry().vertexAt(0).x())
      mesh_info[mesh_idx]["nBldgMesh"] += 1
      mesh_info[mesh_idx]["areaBldgMesh"] += ft_plg.geometry().area()
    
    # second loop is to set the information to the output layer      
    for ft_plg, ft_pnt, mesh_idx in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures(), mesh_idx_ft):
      ft_new = QgsFeature(bldg_fields)
      ft_new.setGeometry(ft_plg.geometry())
      for field_name in ft_plg.fields().names():
        if not field_name in list(self.FIELDS.keys()):
          ft_new[field_name] = ft_plg[field_name]
          
      ft_new["meshIdx"]      = mesh_idx
      ft_new["meshCode"]     = mesh_info[mesh_idx]["meshCode"]
      ft_new["nBldgMesh"]    = mesh_info[mesh_idx]["nBldgMesh"]
      ft_new["areaBldgMesh"] = mesh_info[mesh_idx]["areaBldgMesh"]
      ft_new["areaBldg"]     = ft_new.geometry().area()
      ft_new["popMesh"]      = ft_pnt["pop1"]
      if ft_pnt["pop1"] is not None:
        ft_new["popEst"]     = float(ft_pnt["pop1"]) / ft_new["areaBldgMesh"] * ft_new["areaBldg"]
      sink.addFeature(ft_new)    
              
    return {"OUTPUT": dest_id}
  
  def displayName(self):
    return self.tr("Estimate populations of buildings using Raster")

  def group(self):
    return self.tr("Evaluate health risk")

  def groupId(self):
    return "healthrisk"
  
  def createInstance(self):
    return estimatepopulationofbuilding()
