import os
import urllib.request
import json

class jameshpop(object):
  LAT_UNIT_1 = 40.0 / 60.0  
  LAT_UNIT_2 =  5.0 / 60.0  
  LAT_UNIT_3 = 30.0 / 3600.0
  LAT_UNIT_4 = 15.0 / 3600.0
  LAT_UNIT_5 =  7.5 / 3600.0
  LNG_UNIT_1 =  1.0          
  LNG_UNIT_2 =  7.5  / 60.0  
  LNG_UNIT_3 = 45.0  / 3600.0
  LNG_UNIT_4 = 22.5  / 3600.0
  LNG_UNIT_5 = 11.25 / 3600.0
  
  ESTAT_ID_MESH_FILE = os.path.join(os.path.dirname(__file__),"estatId_mesh_list.txt")
  ESTAT_ID_MESH_DICT = None
  
  ESTAT_API_URI = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"   
  ESTAT_API_PARAMS = {
    "appId": "b877fd89560ce21475681dba1a6681dd6426cbc3",
    "statsDataId": "",
    "statsCode": "00200521",
    "cdCat01": "0010",
    "cdArea": "",
    "metaGetFlg": "N"
  }
  
  def __init__(self):
    with open(self.ESTAT_ID_MESH_FILE) as f:
      self.ESTAT_ID_MESH_DICT = {key: value for line in f for (key, value) in [line.strip().split(None, 1)]}

  def coordsToMesh(self, lng, lat):
    mesh1 = str(int(lat / self.LAT_UNIT_1)) + str(int((lng - 100.0) / self.LNG_UNIT_1))
    (lat1, lng1) = (int(lat / self.LAT_UNIT_1) * self.LAT_UNIT_1, int(lng))
    (lat_resid, lng_resid) = (lat - lat1, lng - lng1)
    mesh2 = str(int(lat_resid / self.LAT_UNIT_2)) + str(int(lng_resid / self.LNG_UNIT_2))
    (lat2, lng2) = (int(lat_resid / self.LAT_UNIT_2) * self.LAT_UNIT_2, int(lng_resid / self.LNG_UNIT_2) * self.LNG_UNIT_2)
    (lat_resid, lng_resid) = (lat_resid - lat2, lng_resid - lng2)
    mesh3 = str(int(lat_resid / self.LAT_UNIT_3)) + str(int(lng_resid / self.LNG_UNIT_3))
    (lat3, lng3) = (int(lat_resid / self.LAT_UNIT_3) * self.LAT_UNIT_3, int(lng_resid / self.LNG_UNIT_3) * self.LNG_UNIT_3)
    (lat_resid, lng_resid) = (lat_resid - lat3, lng_resid - lng3)
    mesh4 = str((int(lng_resid / self.LNG_UNIT_4) + 1) + 2 * int(lat_resid / self.LAT_UNIT_4))
    (lat4, lng4) = (int(lat_resid / self.LAT_UNIT_4) * self.LAT_UNIT_4, int(lng_resid / self.LNG_UNIT_4) * self.LNG_UNIT_4)
    (lat_resid, lng_resid) = (lat_resid - lat4, lng_resid - lng4)
    mesh5 = str((int(lng_resid / self.LNG_UNIT_5) + 1) + 2 * int(lat_resid / self.LAT_UNIT_5))
    (lat5, lng5) = ((int(lat_resid / self.LAT_UNIT_5) + 0.5) * self.LAT_UNIT_5, (int(lng_resid / self.LNG_UNIT_5) + 0.5) * self.LNG_UNIT_5)
    
    mesh_str = mesh1 + mesh2 + mesh3 + mesh4 + mesh5
    lng_center = lng1 + lng2 + lng3 + lng4 + lng5
    lat_center = lat1 + lat2 + lat3 + lat4 + lat5
    
    return (mesh_str, [lng_center, lat_center])
  
  def meshToCoords(self, mesh):
    lat = int(mesh[:2])  * self.LAT_UNIT_1
    lng = int(mesh[2:4]) * self.LNG_UNIT_1 + 100
    if len(mesh) >= 6:
      lat = lat + int(mesh[4]) * self.LAT_UNIT_2
      lng = lng + int(mesh[5]) * self.LNG_UNIT_2
      if len(mesh) >= 8:
        lat = lat + int(mesh[6]) * self.LAT_UNIT_3
        lng = lng + int(mesh[7]) * self.LNG_UNIT_3
        if len(mesh) >= 9:
          lat = lat + (int(mesh[8]) >= 3) * self.LAT_UNIT_4
          lng = lng + (int(mesh[8]) % 2 == 0) * self.LNG_UNIT_4
          if len(mesh) == 10:
            lat = lat + ((int(mesh[9]) >= 3) + 0.5) * self.LAT_UNIT_5
            lng = lng + ((int(mesh[9]) % 2 == 0) + 0.5) * self.LNG_UNIT_5
          else:
            lat = lat + 0.5 * self.LAT_UNIT_4
            lng = lng + 0.5 * self.LNG_UNIT_4
        else:
          lat = lat + 0.5 * self.LAT_UNIT_3
          lng = lng + 0.5 * self.LNG_UNIT_3
      else:
        lat = lat + 0.5 * self.LAT_UNIT_2
        lng = lng + 0.5 * self.LNG_UNIT_2
    else:
      lat = lat + 0.5 * self.LAT_UNIT_1
      lng = lng + 0.5 * self.LNG_UNIT_1
    
    return (lng, lat)
        
          
  
  def fetchPop(self, mesh1, mesh5_list):
    
    params_estat = self.ESTAT_API_PARAMS
    params_estat["statsDataId"] = self.ESTAT_ID_MESH_DICT.get(mesh1)
    
    size = 20    
    pop_dict = {}
    for mesh5_list_short in [mesh5_list[i:i+size] for i in range(0, len(mesh5_list), size)]:
      params_estat["cdArea"] = ",".join(mesh5_list_short)

      req = urllib.request.Request(f"{self.ESTAT_API_URI}?{urllib.parse.urlencode(params_estat)}")
      # with urllib.request.urlopen(req) as res:
      body = json.load(urllib.request.urlopen(req))
      if body.get("GET_STATS_DATA", {}).get("STATISTICAL_DATA", {}).get("DATA_INF") != None:
        if isinstance(body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"], list):
          results = body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]
        else:
          results = [body["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]]
        
        for stat_dict in results:
          pop_dict[stat_dict["@area"]] = {"pop": stat_dict["$"]}
        
    return pop_dict
  