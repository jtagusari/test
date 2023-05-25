from qgis.PyQt.QtCore import (
  QT_TRANSLATE_NOOP,
  )
from qgis.core import (
  QgsProcessingParameterBoolean,
  )

import os
import subprocess

from .algabstract import algabstract

class installcomponents(algabstract):
  
  PARAMETERS = {                  
    "EXEC_INSTALLER": {
      "ui_func": QgsProcessingParameterBoolean,
      "ui_args": {
        "description": QT_TRANSLATE_NOOP("installcomponents","Exec components installer" )
      }
    }
  }
  
  def initAlgorithm(self, config):
    self.initParameters()
    
  def processAlgorithm(self, parameters, context, feedback):     
    if self.parameterAsBoolean(parameters, "EXEC_INSTALLER", context):
      subprocess.run(os.path.join(os.path.dirname(__file__), "installer", "hrisk-setup.exe"))
    else:
      feedback.pushInfo("Installer not executed")
    
    paths = {
      "NOISEMODELLING_HOME": os.environ['NOISEMODELLING_HOME'],
      "JAVA_FOR_NOISEMODELLING": os.environ['JAVA_FOR_NOISEMODELLING']
    }
    
    feedback.pushInfo(f"NoiseModelling is at: {paths['NOISEMODELLING_HOME']}")
    feedback.pushInfo(f"Java is at: {paths['JAVA_FOR_NOISEMODELLING']}")
    return paths
  
  def createInstance(self):
    return installcomponents()


  def displayName(self):
    return self.tr("Install required components")

  def group(self):
    return self.tr("Configurations")

  def groupId(self):
    return "config"

  def createInstance(self):
    return installcomponents()
