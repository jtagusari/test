from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP, QVariant
  )
from qgis.core import (
  QgsProcessing,
  QgsProcessingParameterFeatureSource,
  QgsProcessingParameterFeatureSink,
  QgsProcessingParameterBoolean,
  QgsFeatureRequest,
  QgsProcessingParameterField,
  QgsFeature,
  QgsField
  )

import sys
from .algabstract import algabstract

class estimateriskofbuilding(algabstract):
  PARAMETERS = {
    "BUILDING": {
      "ui_func": QgsProcessingParameterFeatureSource,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Building layer"),
        "types": [QgsProcessing.TypeVectorPolygon]
      }
    },
    "LDEN": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Lden field"),
        "parentLayerParameterName": "BUILDING"
      }
    },
    "LNIGHT": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Lnight field"),
        "parentLayerParameterName": "BUILDING"
      }
    },
    "POP": {
      "ui_func": QgsProcessingParameterField,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Population field"),
        "parentLayerParameterName": "BUILDING"
      }
    },
    "OVERWRITE": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args":{
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Overwrite fields if they already exist"),
        "defaultValue": True
      }
    },
    "OUTPUT": {
      "ui_func": QgsProcessingParameterFeatureSink,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("estimateriskofbuilding","Building with health risks")
      }
    }
  }
  
  FIELDS_ROAD = {
    "relRiskIHD":{
      "type": QVariant.Double,
      "formula": "1.08 ** ((ft['LDEN'] - 53.0) / 10) if ft['LDEN'] > 53.0 else 1.0"
      },
    "probHSD": {
      "type": QVariant.Double,
      "formula": "0.194312 - 0.009336 * ft['LNIGHT'] + 0.000126 * ft['LNIGHT'] ** 2 if ft['LNIGHT'] > 40.0 else 0.0"
      },
    "nHSD": {
      "type": QVariant.Double,
      "formula": "ft_new['probHSD'] * ft['POP'] if ft['POP'] != None else 0"
      },
    "riskPatientIHDJa": {
      "type": QVariant.Double,
      "formula": "ft_new['relRiskIHD'] * 1282000.0 / 126227000.0" # from Patients survey 2020 and National Census 2020
      },
    "nPatientIHDJa": {
      "type": QVariant.Double,
      "formula": "ft_new['relRiskIHD'] * 1282000.0 / 126227000.0 * ft['POP'] if ft['POP'] != None else 0" # from Patients survey 2020 and National Census 2020
      },
    "riskDeathIHDJa": {
      "type": QVariant.Double,
      "formula": "ft_new['relRiskIHD'] * 129.2012 / 100000.0" # from WHO-GHE 2019
      },
    "nDeathIHDJa": {
      "type": QVariant.Double,
      "formula": "ft_new['relRiskIHD'] * 129.2012 / 100000.0 * ft['POP'] if ft['POP'] != None else 0" # from WHO-GHE 2019
      },
  }
  
  def initAlgorithm(self, config):
    self.initParameters()

  def processAlgorithm(self, parameters, context, feedback):    
    bldg_layer = self.parameterAsSource(parameters, "BUILDING", context).materialize(QgsFeatureRequest(), feedback)
    bldg_fields = bldg_layer.fields()
    field_Lden = self.parameterAsFields(parameters, "LDEN", context)[0]
    field_Lnight = self.parameterAsFields(parameters, "LNIGHT", context)[0]
    field_pop = self.parameterAsFields(parameters, "POP", context)[0]
    
    for existing_field_name in bldg_fields.names():
      if existing_field_name.lower() in map(lambda x: x.lower(), self.FIELDS_ROAD.keys()):
        if self.parameterAsBoolean(parameters, "OVERWRITE", context):
          bldg_fields.remove(bldg_fields.indexOf(existing_field_name))
        else:
          sys.exit(self.tr("The field name is duplicated:") + existing_field_name)
        
    for key, value in self.FIELDS_ROAD.items():
      bldg_fields.append(QgsField(key, value["type"]))
    
    (sink, dest_id) = self.parameterAsSink(
      parameters, "OUTPUT", context,
      bldg_fields, bldg_layer.wkbType(), bldg_layer.crs()
    )
    
    for ft in bldg_layer.getFeatures():
      
      ft_new = QgsFeature(bldg_fields)
      ft_new.setGeometry(ft.geometry())
      for field_name in ft.fields().names():
        if field_name in bldg_fields.names():
          ft_new[field_name] = ft[field_name]
      
      for key, value in self.FIELDS_ROAD.items():
        fml = value.get("formula")
        if fml != None:
          fml = fml.replace("LDEN", field_Lden)
          fml = fml.replace("LNIGHT", field_Lnight)
          fml = fml.replace("POP", field_pop)
          ft_new[key] = eval(fml)
          
      sink.addFeature(ft_new)

          
    return {"OUTPUT": dest_id}
  
  # Post processing; append layers
  def postProcessAlgorithm(self, context, feedback):
    return {}

  def displayName(self):
    return self.tr("Estimate health risk of buildings")

  def group(self):
    return self.tr("Noise prediction / evaluation")

  def groupId(self):
    return "noisepredictionevaluation"
  
  def createInstance(self):
    return estimateriskofbuilding()