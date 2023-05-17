from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterBoolean,
  QgsField,
  QgsFeature
  )

from .algabstract import algabstract

class initabstract(algabstract):
  FIELDS_ADD = {    
    "PK":        {"TYPE": QVariant.Int, "DEFAULT_VALUE": None}
  }
  
  FIELDS_INIT = None
  FIELDS_FROM = {}
    

  # set the fields that are added / overwritten / not changed
  def setFields(self, parameters, context, feedback):
    self.FIELDS_FROM = {}
    input_layer = self.parameterAsSource(parameters, "INPUT", context)
    fields_init = input_layer.fields()
    
    for fld_name in fields_init.names():
      self.FIELDS_FROM.update({fld_name: "INPUT"})
    
    fld_names_added = []
    fld_names_overwritten = []
    for fld_name, fld_info in self.FIELDS_ADD.items():
      if fld_name.lower() not in map(lambda x: x.lower(), fields_init.names()):
        fields_init.append(QgsField(fld_name, fld_info["TYPE"]))
        self.FIELDS_FROM.update({fld_name: "ADD"})
        fld_names_added.append(fld_name)
      else:
        if self.parameterAsBoolean(parameters, "OVERWRITE", context):
          self.FIELDS_FROM.update({fld_name: "ADD"})
          fld_names_overwritten.append(fld_name)
    
    if len(fld_names_added) > 0:
      feedback.pushInfo(self.tr("Field was added: ") + ",".join(fld_names_added))
    if len(fld_names_overwritten) > 0:
      feedback.pushInfo(self.tr("Field was overwrite: ") + ",".join(fld_names_overwritten))
    
    self.FIELDS_INIT = fields_init
  
  # create a sink that contains necessary fields
  def createVectorLayerAsSink(self, parameters, context, feedback):
        
    input_layer = self.parameterAsSource(parameters, "INPUT", context)
    # define the feature sink
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context, 
      self.FIELDS_INIT, 
      input_layer.wkbType(), 
      input_layer.sourceCrs()
    )
    
    # add features
    for fid, ft in enumerate(input_layer.getFeatures(), start = 1):
      # initialize the feature
      new_ft = QgsFeature(self.FIELDS_INIT)
      new_ft.setGeometry(ft.geometry())
      
      for fld_name, source in self.FIELDS_FROM.items():
        if source == "INPUT":
          new_ft[fld_name] = ft[fld_name]
        else:
          if fld_name.lower() == "pk":
            new_ft[fld_name] = fid
          else:
            new_ft[fld_name] = self.FIELDS_ADD[fld_name]["DEFAULT_VALUE"]
      sink.addFeatures([new_ft])
          
    return dest_id
