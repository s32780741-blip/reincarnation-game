"""Kingdom loader."""
import json, os
from config import DATA_DIR

_K = None

def load_kingdoms():
    global _K
    if _K is not None:
        return _K
    path = os.path.join(DATA_DIR, "kingdoms.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _K = json.load(f).get("kingdoms", [])
    except Exception:
        _K = []
    return _K

def get_kingdom(kid):
    for k in load_kingdoms():
        if k["id"] == kid:
            return k
    return None

def kingdom_name(kid):
    k = get_kingdom(kid)
    return k["name"] if k else kid
