"""City loader."""
import json, os
from config import DATA_DIR

_C = None

def load_cities():
    global _C
    if _C is not None:
        return _C
    path = os.path.join(DATA_DIR, "cities.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _C = json.load(f).get("cities", [])
    except Exception:
        _C = []
    return _C

def get_city(cid):
    for c in load_cities():
        if c["id"] == cid:
            return c
    return None

def city_name(cid):
    c = get_city(cid)
    return c["name"] if c else cid

def cities_in_kingdom(kid):
    return [c for c in load_cities() if c["kingdom"] == kid]

def danger_label(d):
    if d <= 1: return "Peaceful"
    if d <= 2: return "Low"
    if d <= 3: return "Moderate"
    if d <= 4: return "High"
    if d <= 5: return "Dangerous"
    if d <= 6: return "Very Dangerous"
    if d <= 7: return "Extreme"
    return "Deadly"
