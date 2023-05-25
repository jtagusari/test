def getNoiseColorMap(opacity:int=255) -> dict:
  if opacity < 0 or opacity > 255:
    opacity = 255
  col_map = {
    "< 35 dB":    {"lower": -999, "upper":  35, "color": f"255,255,255,{opacity}"},
    "35 - 40 dB": {"lower":   35, "upper":  40, "color": f"160,186,191,{opacity}"},
    "40 - 45 dB": {"lower":   40, "upper":  45, "color": f"184,214,209,{opacity}"},
    "45 - 50 dB": {"lower":   45, "upper":  50, "color": f"206,228,204,{opacity}"},
    "50 - 55 dB": {"lower":   50, "upper":  55, "color": f"226,242,191,{opacity}"},
    "55 - 60 dB": {"lower":   55, "upper":  60, "color": f"243,198,131,{opacity}"},
    "60 - 65 dB": {"lower":   60, "upper":  65, "color": f"232,126,77,{opacity}" },
    "65 - 70 dB": {"lower":   65, "upper":  70, "color": f"205,70,62,{opacity}"  },
    "70 - 75 dB": {"lower":   70, "upper":  75, "color": f"161,26,77,{opacity}"  },
    "75 - 80 dB": {"lower":   75, "upper":  80, "color": f"117,8,92,{opacity}"   },
    "> 80 dB":    {"lower":   80, "upper": 999, "color": f"67,10,74,{opacity}"   }
  }
  
  return col_map
      