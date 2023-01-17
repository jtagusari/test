import urllib.request
import json
import re

url_list = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList"

params_list = {
  "appId": "b877fd89560ce21475681dba1a6681dd6426cbc3",
  "statsCode": "00200521",
  "searchWord": "平成27年 AND 国勢調査 AND 人口等基本集計 AND 250m",
  "searchKind": "2"
}


req_list = urllib.request.Request(f"{url_list}?{urllib.parse.urlencode(params_list)}")
with urllib.request.urlopen(req_list) as res_list:
    body_list = json.load(res_list)
        
    f = open("estatId_mesh_list.txt", "a")
    for tab_info in body_list["GET_STATS_LIST"]["DATALIST_INF"]["TABLE_INF"]:
      f.write(
        re.search(r"[0-9]{4}", tab_info["TITLE"]["$"]).group() + " " + tab_info["@id"] + "\n"
      )
    f.close()


url_data = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"

params_data = {
  "appId": "b877fd89560ce21475681dba1a6681dd6426cbc3",
  "statsDataId": "8003001606",
  "statsCode": "00200521",
  "cdCat01": "0010",
  "cdArea": "3622572741",
  "metaGetFlg": "N"
}

req_data = urllib.request.Request(f"{url_data}?{urllib.parse.urlencode(params_data)}")
with urllib.request.urlopen(req_data) as res_data:
    body_data = json.load(res_data)
    body_data["GET_STATS_DATA"]["STATISTICAL_DATA"]["DATA_INF"]["VALUE"]["$"]
