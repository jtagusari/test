import os
from .algabstract import algabstract

class receiverabstract(algabstract):  
  def addPathNoiseModelling(self):
    self.NOISEMODELLING["RECEIVER_PATH"] = os.path.join(self.NOISEMODELLING["TEMP_DIR"], "RECEIVERS.geojson")
    self.NOISEMODELLING["TRIANGLE_PATH"] = os.path.join(self.NOISEMODELLING["TEMP_DIR"], "TRIANGLES.geojson")
    