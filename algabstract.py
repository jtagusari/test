from qgis.PyQt.QtCore import (
  QCoreApplication
  )
from qgis.core import (
  QgsVectorLayer,
  QgsProcessingAlgorithm,
  QgsProcessingParameterDefinition, 
  QgsProcessingParameterNumber,
  QgsProcessingUtils,
  QgsVectorFileWriter,
  QgsCoordinateTransformContext,
  QgsFeatureRequest,
  QgsProcessingParameterString,
  QgsProcessingParameterBoolean,
  QgsCoordinateReferenceSystem,
  QgsRasterFileWriter
  )

import os
import sys
import asyncio

class algabstract(QgsProcessingAlgorithm):
  NOISEMODELLING = {}
  
  def initNoiseModelling(self, groovy_script_str):
    self.NOISEMODELLING["HOME"] = os.environ["NoiseModelling"]
    self.NOISEMODELLING["SCRIPT"] = os.path.join(os.path.dirname(__file__), "groovy", groovy_script_str)
  
    # folder where the files are saved
    self.NOISEMODELLING["TEMP_DIR"] = os.path.normpath(os.path.dirname(QgsProcessingUtils.generateTempFilename("")))
    if not os.path.exists(self.NOISEMODELLING["TEMP_DIR"]):
      os.mkdir(self.NOISEMODELLING["TEMP_DIR"])
    
    self.addPathNoiseModelling()
  
  def addPathNoiseModelling(self):
    pass
  
  def initWpsArgs(self, parameters, context, feedback, additional_wps = None):   
    self.NOISEMODELLING["WPS_ARGS"] = {
      "w": self.NOISEMODELLING["TEMP_DIR"], 
      "s": self.NOISEMODELLING["SCRIPT"],
      "exportDir": self.NOISEMODELLING["TEMP_DIR"]
    }
    
    if additional_wps is not None:
      self.NOISEMODELLING["WPS_ARGS"].update(additional_wps)
    
    # get CRS
    crs_key = [key for key, value in self.PARAMETERS.items() if value.get("crs_referrence") != None and value.get("crs_referrence") == True]
    crs_referrence = self.parameterAsSource(parameters, crs_key[0], context).sourceCrs()
    self.NOISEMODELLING["WPS_ARGS"]["inputSRID"] = crs_referrence.authid().replace("EPSG:","")
    
    # set other arguments
    for key, value in self.PARAMETERS.items():
      if value.get("n_mdl") != None:
        if value.get("save_layer_get_path") != None and value.get("save_layer_get_path") == True:
          src = self.parameterAsSource(parameters, key, context)
          if src != None:
            if src.sourceCrs() != crs_referrence:
              sys.exit(self.tr("CRS is not the same among input features!"))
            vl = src.materialize(QgsFeatureRequest(), feedback)
            vl_path = os.path.join(self.NOISEMODELLING["TEMP_DIR"], key + ".geojson")
            self.saveVectorLayer(vl, vl_path)
            self.NOISEMODELLING["WPS_ARGS"][value.get("n_mdl")] = vl_path
        else:
          if value.get("ui_func") == QgsProcessingParameterString:
            value_input = self.parameterAsString(parameters, key, context)
          if value.get("ui_func") == QgsProcessingParameterBoolean:
            value_input = self.parameterAsInt(parameters, key, context)
          if value.get("ui_func") == QgsProcessingParameterNumber:
            if value.get("ui_args").get("type") == QgsProcessingParameterNumber.Integer:
              value_input = self.parameterAsInt(parameters, key, context)
            else:
              value_input = self.parameterAsDouble(parameters, key, context)
            
          self.NOISEMODELLING["WPS_ARGS"][value.get("n_mdl")] = value_input
    self.genCmd()
  
  # method just to generate the command to execute a groovy script
  def genCmd(self):
    self.NOISEMODELLING["CMD"] = os.path.join("bin","wps_scripts") + \
      "".join([" -" + k + " " + str(v) for k, v in self.NOISEMODELLING["WPS_ARGS"].items()])
  
  # add parameters using PARAMETERS attribute
  def initParameters(self):    
    for key, value in self.PARAMETERS.items():
      args = value.get("ui_args")
      args["name"] = key
      args["description"] = self.tr(args["description"])
              
      ui = value.get("ui_func")(**args)
      
      if value.get("advanced") != None and value.get("advanced") == True:
        ui.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
        
      self.addParameter(ui)  
  
  # to save a vector layer
  def saveVectorLayer(self, vector_layer, path):
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "GeoJSON"
    QgsVectorFileWriter.writeAsVectorFormatV3(
      vector_layer, path, QgsCoordinateTransformContext(), save_options
    )
  
  
  # to save a raster layer
  def saveRasterLayer(self, raster_layer, path):
    file_writer = QgsRasterFileWriter(path)
    file_writer.writeRaster(
      raster_layer.pipe(), 
      raster_layer.width(), raster_layer.height(),
      raster_layer.dataProvider().extent(),
      raster_layer.crs()
      )
  
  # execution of the NoiseModelling scrript
  def execNoiseModelling(self, parameters, context, feedback):
    loop = asyncio.ProactorEventLoop()      
    loop.run_until_complete(
      self.streamNoiseModelling(self.NOISEMODELLING["CMD"], feedback)
    )
    
  async def streamNoiseModelling(self, cmd, feedback):
    proc = await asyncio.create_subprocess_shell(
      cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
      cwd = self.NOISEMODELLING["HOME"]
    )

    while True:
      if proc.stdout.at_eof() and proc.stderr.at_eof():
        break  

      stderr_raw = await proc.stderr.readline() # for debugging
      stderr = stderr_raw.decode()
      
      if stderr:
        feedback.pushInfo(stderr.replace("\n",""))
  
  # import the results of the NoiseModelling as a sink
  def importNoiseModellingResultsAsSink(self, parameters, context, attribute, path):

    dest_id = None
    if os.path.exists(path):
      layer = QgsVectorLayer(path, "layer_from_NoiseModelling")
      if layer.featureCount() > 0:
        (sink, dest_id) = self.parameterAsSink(
          parameters, attribute, context,
          layer.fields(), layer.wkbType(), QgsCoordinateReferenceSystem("EPSG:" + self.NOISEMODELLING["WPS_ARGS"]["inputSRID"])
        )
        sink.addFeatures(layer.getFeatures())
          
    return dest_id

  def name(self):
    return self.__class__.__name__

  def tr(self, string):
    return QCoreApplication.translate(self.__class__.__name__, string)
