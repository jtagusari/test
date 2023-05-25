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
  QgsRasterFileWriter,
  QgsProcessingFeedback,
  QgsProcessingContext,
  QgsRasterLayer
  )

import os
import sys
import asyncio
import re

class algabstract(QgsProcessingAlgorithm):
  NOISEMODELLING = {
    "CMD": None,
    "GROOVY_SCRIPT": None,
    "TEMP_DIR":None,
    "WPS_ARGS":None
    }
  
  PARAMETERS = {}
  
  def initNoiseModellingPath(self, paths:dict) -> None:
    if paths.get("GROOVY_SCRIPT") is None:
      sys.exit(self.tr("Groovy script is not specified"))
    self.NOISEMODELLING["GROOVY_SCRIPT"] = os.path.join(os.path.dirname(__file__), "noisemodelling","hriskscript", paths["GROOVY_SCRIPT"])
  
    # folder where the files are saved
    self.NOISEMODELLING["TEMP_DIR"] = os.path.normpath(os.path.dirname(QgsProcessingUtils.generateTempFilename("")))
    if not os.path.exists(self.NOISEMODELLING["TEMP_DIR"]):
      os.mkdir(self.NOISEMODELLING["TEMP_DIR"])
    
    if paths is not None and isinstance(paths, dict):
      for key, value in paths.items():
        if isinstance(value, str):
          paths[key] = value.replace("%nmtmp%", self.NOISEMODELLING["TEMP_DIR"])
        elif isinstance(value, dict):
          for key2, value2 in value.items():
            paths[key][key2] = value2.replace("%nmtmp%", self.NOISEMODELLING["TEMP_DIR"])
      self.NOISEMODELLING.update(paths)

    
  def initNoiseModellingArg(
    self, parameters:dict, context: QgsProcessingContext, feedback:QgsProcessingFeedback
    ) -> None:   
    
    self.NOISEMODELLING["WPS_ARGS"] = {
      "w": self.NOISEMODELLING["TEMP_DIR"], 
      "s": self.NOISEMODELLING["GROOVY_SCRIPT"],
      "noiseModellingHome": '"' + os.path.normpath(os.environ["NOISEMODELLING_HOME"]) + '"',
      "exportDir": '"' + self.NOISEMODELLING["TEMP_DIR"]+ '"'
    }
    
    # get CRS
    try:
      crs_key = [key for key, value in self.PARAMETERS.items() if value.get("crs_referrence") != None and value.get("crs_referrence") == True]
      crs_referrence = self.parameterAsSource(parameters, crs_key[0], context).sourceCrs()
      self.NOISEMODELLING["WPS_ARGS"]["inputSRID"] = crs_referrence.authid().replace("EPSG:","")
    except:
      sys.exit(self.tr("CRS is not specified by EPSG code!"))
    
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
            self.NOISEMODELLING["WPS_ARGS"][value.get("n_mdl")] = '"' + vl_path + '"'
        else:
          if value.get("ui_func") == QgsProcessingParameterString:
            value_input = '"' + self.parameterAsString(parameters, key, context) + '"'
          if value.get("ui_func") == QgsProcessingParameterBoolean:
            value_input = self.parameterAsInt(parameters, key, context)
          if value.get("ui_func") == QgsProcessingParameterNumber:
            if value.get("ui_args").get("type") == QgsProcessingParameterNumber.Integer:
              value_input = self.parameterAsInt(parameters, key, context)
            else:
              value_input = self.parameterAsDouble(parameters, key, context)
            
          self.NOISEMODELLING["WPS_ARGS"][value.get("n_mdl")] = value_input
  
  def addNoiseModellingArg(self, args:dict=None) -> None:
    if (isinstance(args, dict)):
      self.NOISEMODELLING["WPS_ARGS"].update(args)
  
  # add parameters using PARAMETERS attribute
  def initParameters(self) -> None:    
    for key, value in self.PARAMETERS.items():
      try:
        args = value.get("ui_args")
        args["name"] = key
        args["description"] = self.tr(args["description"])
                
        ui = value.get("ui_func")(**args)
        
        if value.get("advanced") != None and value.get("advanced") == True:
          ui.setFlags(QgsProcessingParameterDefinition.FlagAdvanced)
          
        self.addParameter(ui)  
      except:
        pass
  
  # to save a vector layer
  def saveVectorLayer(self, vector_layer: QgsVectorLayer, path: str) -> None:
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "GeoJSON"
    QgsVectorFileWriter.writeAsVectorFormatV3(
      vector_layer, path, QgsCoordinateTransformContext(), save_options
    )
  
  
  # to save a raster layer
  def saveRasterLayer(self, raster_layer:QgsRasterLayer, path: str) -> None:
    file_writer = QgsRasterFileWriter(path)
    file_writer.writeRaster(
      raster_layer.pipe(), 
      raster_layer.width(), raster_layer.height(),
      raster_layer.dataProvider().extent(),
      raster_layer.crs()
      )
  
  # execution of the NoiseModelling script
  def execNoiseModellingCmd(
    self, parameters: dict, context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> None:    
    
    self.NOISEMODELLING["CMD"] = os.path.join(os.path.dirname(__file__), "noisemodelling","bin","wps_scripts") + \
      "".join([" -" + k + " " + str(v) for k, v in self.NOISEMODELLING["WPS_ARGS"].items()])
    feedback.pushCommandInfo(self.NOISEMODELLING["CMD"])   
    
    loop = asyncio.new_event_loop()
    loop.run_until_complete(
      self.streamNoiseModellingCmd(self.NOISEMODELLING["CMD"], feedback)
    )
    loop.close()
    
    
  async def streamNoiseModellingCmd(self, cmd: str, feedback: QgsProcessingFeedback) -> None:
    proc = await asyncio.create_subprocess_shell(
      cmd,
      stdout=asyncio.subprocess.PIPE,
      stderr=asyncio.subprocess.PIPE,
      cwd = self.NOISEMODELLING["TEMP_DIR"]
    )

    while True:
      if proc.stdout.at_eof() or proc.stderr.at_eof():
        break  

      stderr_raw = await proc.stderr.readline() # for debugging
      try:
        stderr = stderr_raw.decode()
      except:
        stderr = ""
        sys.exit(self.tr("Error in NoiseModelling script!"))
      
      if stderr:
        feedback.pushInfo(stderr.replace("\n",""))
        
        
      prg_match = re.search(r".*[0-9]+\.[0-9]+.*%", stderr)
      if prg_match:                
        feedback.setProgress(
          int(float(re.search(r"[0-9]+\.[0-9]+", prg_match.group()).group()))
        )
  
  # import the results of the NoiseModelling as a sink
  def importNoiseModellingResultsAsSink(self, parameters: dict, context: QgsProcessingContext, attribute: str, path: str) -> None:

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
