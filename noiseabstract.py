
from qgis.PyQt.QtCore import (QCoreApplication, QT_TRANSLATE_NOOP, QVariant)
from qgis.core import (
  QgsProject,
  QgsVectorLayer,
  QgsGraduatedSymbolRenderer,
  QgsRendererRange,
  QgsClassificationRange,
  QgsMarkerSymbol,
  QgsFillSymbol,
  QgsLineSymbol,
  QgsProcessingContext,
  QgsReferencedRectangle,
  QgsWkbTypes,
  QgsProcessingLayerPostProcessorInterface,
  QgsField,
  QgsFields,
  QgsFeature,
  QgsGeometry,
  QgsProcessingFeedback
  )

from qgis import processing

import os
import uuid

from .algabstract import algabstract
from .noisecolor import getNoiseColorMap

class noiseabstract(algabstract):
  
  BLDG_LEVEL_ARGS = {
    "BUILDING_BID": "PK", # primary key of the buildings
    "RECEIVER_BID": "BUILD_PK", # primary key of the buildings, written in receiver layer
    "RECEIVER_RID": "PK", # primary key of the receivers
    "LEVEL_RID": "IDRECEIVER", #primary key of the receivers, written in level layer    
    "LEVEL_ASSIGN": ["LAEQ"] # which attribute(s) to be assined
  }
  
  ISOSURFACE_ARGS = {
    "LEVEL_RID": "IDRECEIVER" #primary key of the receivers, written in level layer        
  }
    
  PROC_RESULTS = {}
  

  def initNoiseModellingPath(self, paths={}):
    paths.update(
      {
        "TRIANGLE": os.path.join("%nmtmp%", "TRIANGLES.geojson"),
        "LEVEL_RESULTS":  {
          "LDAY":     os.path.join("%nmtmp%", "LDAY_GEOM.geojson"),
          "LEVENING": os.path.join("%nmtmp%", "LEVENING_GEOM.geojson"),
          "LNIGHT":   os.path.join("%nmtmp%", "LNIGHT_GEOM.geojson"),
          "LDEN":     os.path.join("%nmtmp%", "LDEN_GEOM.geojson"),
        },
        "BUILDING_RESULTS": {
          "BUILDING_WITH_LEVEL": os.path.join("%nmtmp%", "BUILDING_WITH_LEVEL.geojson")
        }
      }
    )
    super().initNoiseModellingPath(paths)
    
  # output a polygon (sink and output the `dest_id`) 
  # that stores arguments of the calculation
  def outputWpsArgs(self, parameters:dict, context:QgsProcessingContext, extent_rec: QgsReferencedRectangle) -> str:  
    args_fields = QgsFields()
    for key, value in self.NOISEMODELLING["WPS_ARGS"].items():
      if type(value) in [int, bool]:
        args_fields.append(QgsField(key, QVariant.Int))
      elif type(value) in [float]:
        args_fields.append(QgsField(key, QVariant.Double))
      elif type(value) in [str]:
        args_fields.append(QgsField(key, QVariant.String))
        
    (sink, dest_id) = self.parameterAsSink(
      parameters, "WPS_ARGS", context, args_fields, QgsWkbTypes.Polygon, extent_rec.crs()
      )
    
    ft = QgsFeature(args_fields)
    ft.setGeometry(QgsGeometry.fromRect(extent_rec))
    for key, value in self.NOISEMODELLING["WPS_ARGS"].items():
      ft[key] = value
    sink.addFeature(ft)
    
    return dest_id
  
  # create sound-level assigned buildings
  def cmptBuildingLevel(self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback, bldg_layer: QgsVectorLayer, rcv_layer: QgsVectorLayer) -> None:
    
    for noise_idx, file_path in self.NOISEMODELLING["LEVEL_RESULTS"].items():          
      # overwrite building layer
      estimate_level_args = {
          "BUILDING": bldg_layer,
          "RECEIVER": rcv_layer,
          "LEVEL": QgsVectorLayer(file_path, noise_idx),
          "LEVEL_PREFIX": noise_idx + "_",
          "OVERWRITE": True,
          "OUTPUT": "TEMPORARY_OUTPUT"
          }
      estimate_level_args.update(self.BLDG_LEVEL_ARGS)
      
      bldg_layer = processing.run(
        "hrisk:estimatelevelofbuilding",
        estimate_level_args
      )["OUTPUT"]
    
    # estimate the health risk
    bldg_layer = processing.run(
      "hrisk:estimateriskofbuilding",
      {
        "BUILDING": bldg_layer,
        "LDEN": "LDEN_LAEQ_maximum",
        "LNIGHT": "LNIGHT_LAEQ_maximum",
        "POP": "popEst",
        "OVERWRITE": True,
        "OUTPUT": "TEMPORARY_OUTPUT"
      }
    )["OUTPUT"]
    
    # save the result
    self.saveVectorLayer(bldg_layer, self.NOISEMODELLING["BUILDING_RESULTS"]["BUILDING_WITH_LEVEL"] )

  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    # use postprocessor class, defined below
    global splcalc_postprocessors
    
    # prepare blank list for the instances
    splcalc_postprocessors = []
    
    # add a group in QGIS
    grp_name = "result_ft_" + str(uuid.uuid4())[:6]
    QgsProject.instance().layerTreeRoot().insertGroup(0, grp_name)
    
    # get the dict of the layers
    layer_dict = context.layersToLoadOnCompletion()
    for i, path in enumerate(layer_dict.keys()):
      # based on the layername, attributes for the colors are determined
      layer_name = context.layerToLoadOnCompletionDetails(path).outputName
      if layer_name in ["LDAY","LEVENING", "LNIGHT", "LDEN"]:
        spl_attribute_name = "LAEQ"
      elif layer_name == "BUILDING_WITH_LEVEL":
        spl_attribute_name = "LDEN_LAEQ_maximum"
      else:
        spl_attribute_name = "NO_RENDERING"
      
      # make (in)visible, according to the argument
      if len([k for k, v in self.PROC_RESULTS.items() if v == path]) == 1:
        vis = self.PARAMETERS.get([k for k, v in self.PROC_RESULTS.items() if v == path][0]).get("visibleByDefault")
      
      # append an instance to be usef for the post-processing and set it
      splcalc_postprocessors.append(splcalcPostProcessor(grp_name, vis, spl_attribute_name))
      context.layerToLoadOnCompletionDetails(path).setPostProcessor(splcalc_postprocessors[i])
    return {}
  

# class for post-processing
class splcalcPostProcessor (QgsProcessingLayerPostProcessorInterface):
  group_name = None
  spl_attribute_name = None
  visibility = None
  
  # constructor
  def __init__(self, group_name, visibility, spl_attribute_name):
    self.group_name = group_name
    self.spl_attribute_name = spl_attribute_name
    self.visibility = visibility
    super().__init__()
  
  
  # for post-processing
  def postProcessLayer(self, layer, context, feedback):
    
    # find the vector layer
    root = QgsProject.instance().layerTreeRoot()
    vl = root.findLayer(layer.id())
    
    if self.spl_attribute_name != "NO_RENDERING" and self.spl_attribute_name in vl.layer().fields().names():
      # set renderer
      renderer = QgsGraduatedSymbolRenderer(self.spl_attribute_name)
      col_map = getNoiseColorMap()
      
      # change symboller according to the wkb-type
      symb_fun = None
      if layer.wkbType() in [QgsWkbTypes.Point, QgsWkbTypes.PointZ]:
        symb_fun = QgsMarkerSymbol.createSimple
      elif layer.wkbType() == QgsWkbTypes.Polygon:
        symb_fun = QgsFillSymbol.createSimple
      elif layer.wkbType() == QgsWkbTypes.LineString:
        symb_fun = QgsLineSymbol.createSimple
      
      # set symbols
      if symb_fun != None:
        for key, value in col_map.items():
          renderer.addClassRange(
            QgsRendererRange(
              QgsClassificationRange(key, value.get("lower"), value.get("upper")), 
              symb_fun({"color":value.get("color")})
            )
          )
        # apply renderer
        vl.layer().setRenderer(renderer)
        vl.layer().triggerRepaint()   
    
    # assign the layer in the group
    vl.setItemVisibilityChecked(self.visibility)
    vl_clone = vl.clone()
    grp = root.findGroup(self.group_name)
    if grp != None:
      parent = vl.parent()
      grp.insertChildNode(0, vl_clone)
      parent.removeChildNode(vl)
  