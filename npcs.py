"""NPC loader."""
import json, os
from config import DATA_DIR

_N = None

def load_npcs():
    global _N
    if _N is not None:
        return _N
    path = os.path.join(DATA_DIR, "npcs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _N = json.load(f).get("npcs", [])
    except Exception:
        _N = []
    return _N

def get_npc(nid):
    for n in load_npcs():
        if n["id"] == nid:
            return n
    return None

def npc_name(nid):
    n = get_npc(nid)
    return n["name"] if n else nid
