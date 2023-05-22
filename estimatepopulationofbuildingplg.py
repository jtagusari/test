from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsFeatureRequest,
  QgsProcessingParameterField,
  QgsFeature,
  QgsField,
  QgsFields
  )

from qgis import processing
from .algabstract import algabstract
import sys

class estimatepopulationofbuildingplg(algabstract):
  PARAMETERS = {
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuildingplg","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "POP": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuildingplg","Population layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "PK_FIELD": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuildingplg","Primary key field"),
        "parentLayerParameterName": "POP"
      }
    },
    "POP_FIELD": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuildingplg","Population field"),
        "parentLayerParameterName": "POP"
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("estimatepopulationofbuildingplg","Building with population")
      }
    }
  }
  
  FIELDS = {
    "pkPlg":{"type": None},
    "nBldgPlg": {"type": QVariant.Int},
    "areaBldg": {"type": QVariant.Double},
    "areaBldgPlg": {"type": QVariant.Double},
    "popPlg": {"type": QVariant.Int},
    "popEst": {"type": QVariant.Double}
  }
  
  def initAlgorithm(self, config):
    self.initParameters()
    

  def cmptBldgPntLayer(self, bldg_layer, pop_plg, join_fields):
    
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
        "TARGET_CRS" : pop_plg.crs(),
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    # sampling the population from polygon
    bldg_cent_pnt_pop = processing.run(
      "native:joinattributesbylocation",
      {
        "DISCARD_NONMATCHING": False,
        "INPUT": bldg_cent_pnt_transformed,
        "JOIN": pop_plg,
        "JOIN_FIELDS": join_fields,
        "METHOD": 0, # intersect
        "PREDICATE": [0], # equals
        "PREFIX": "plg",
        "OUTPUT" : "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    
    return bldg_cent_pnt_pop
  
  
  def processAlgorithm(self, parameters, context, feedback):   
    pop = self.parameterAsSource(parameters, "POP", context).materialize(QgsFeatureRequest(), feedback) 
    bldg_plg = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback) 
    plg_pk_fld = self.parameterAsString(parameters, "PK_FIELD", context)
    plg_pop_fld = self.parameterAsString(parameters, "POP_FIELD", context)
    self.FIELDS["pkPlg"]["type"] = pop.fields().field(plg_pk_fld).type()
    
    bldg_pnt = self.cmptBldgPntLayer(bldg_plg, pop, [plg_pk_fld, plg_pop_fld])
    
    plg_pk_fld = "plg" + plg_pk_fld
    plg_pop_fld = "plg" + plg_pop_fld
    
    # initialize the fields
    bldg_fields = QgsFields(bldg_plg.fields())
    for key, arg in self.FIELDS.items():
      if key in bldg_fields.names():
        bldg_fields.remove(bldg_fields.lookupField(key))
      bldg_fields.append(QgsField(key, arg["type"]))
          
    # create sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context,
      bldg_fields, bldg_plg.wkbType(), bldg_plg.sourceCrs()
    )
    
      
    # first loop is to get the mesh information from ft_pnt
    plg_pk_ft = []
    plg_info = {}    
    for ft_plg, ft_pnt in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures()):
      
      plg_pk = ft_pnt[plg_pk_fld]
      plg_pk_ft.append(plg_pk)
      
      # accumlate the information regarding the mesh
      if plg_info.get(plg_pk) == None:
        plg_info[plg_pk] = {"popPlg": ft_pnt[plg_pop_fld], "nBldgPlg": 0,"areaBldgPlg": 0.0}
      plg_info[plg_pk]["nBldgPlg"] += 1
      plg_info[plg_pk]["areaBldgPlg"] += ft_plg.geometry().area()
    
    # second loop is to set the information to the output layer      
    for ft_plg, ft_pnt, plg_pk in zip(bldg_plg.getFeatures(), bldg_pnt.getFeatures(), plg_pk_ft):
      ft_new = QgsFeature(bldg_fields)
      ft_new.setGeometry(ft_plg.geometry())
      for field_name in ft_plg.fields().names():
        if not field_name in list(self.FIELDS.keys()):
          ft_new[field_name] = ft_plg[field_name]
          
      ft_new["pkPlg"]        = ft_pnt[plg_pk_fld]
      ft_new["nBldgPlg"]    = plg_info[plg_pk]["nBldgPlg"]
      ft_new["areaBldgPlg"] = plg_info[plg_pk]["areaBldgPlg"]
      ft_new["areaBldg"]     = ft_new.geometry().area()
      ft_new["popPlg"]      = ft_pnt[plg_pop_fld]
      if ft_pnt[plg_pop_fld] is not None:
        ft_new["popEst"]     = float(ft_pnt[plg_pop_fld]) / ft_new["areaBldgPlg"] * ft_new["areaBldg"]
      sink.addFeature(ft_new)    
              
    return {"OUTPUT": dest_id}
  
  def displayName(self):
    return self.tr("Estimate populations of buildings using Polygon")

  def group(self):
    return self.tr("Evaluate health risk")

  def groupId(self):
    return "healthrisk"
  
  def createInstance(self):
    return estimatepopulationofbuildingplg()
