# utils.py
import math

def haversine(p1, p2):
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 6371000 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

from math import radians, sin, cos, sqrt, asin

def haversine_(lat1, lon1, lat2, lon2, r=6371):
    φ1, φ2 = radians(lat1), radians(lat2)
    λ1, λ2 = radians(lon1), radians(lon2)
    a = sin((φ2 - φ1)/2)**2 + cos(φ1) * cos(φ2) * sin((λ2 - λ1)/2)**2
    return r * 2 * asin(sqrt(a))

def speed_to_color(speed_mps):
    if speed_mps is None:
        return "#888888"
    kmh = speed_mps * 3.6
    if kmh < 5:   return "#00ff00"
    if kmh < 15:  return "#88ff00"
    if kmh < 30:  return "#ffff00"
    if kmh < 50:  return "#ff8800"
    return "#ff0000"
