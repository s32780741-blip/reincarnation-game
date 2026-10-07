"""Element chart & damage modifier."""
import json, os
from config import DATA_DIR

_E = None

def _load():
    global _E
    if _E is not None:
        return _E
    path = os.path.join(DATA_DIR, "elements.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _E = json.load(f)
    except Exception:
        _E = {"advantage": {}, "resistant": {}, "colors": {}}
    return _E

def is_weak(attacker_elem, defender_elem):
    e = _load()
    return defender_elem in e.get("advantage", {}).get(attacker_elem, [])

def is_resisted(attacker_elem, defender_elem):
    e = _load()
    return defender_elem in e.get("resistant", {}).get(attacker_elem, [])

def damage_multiplier(attacker_elem, defender_elem):
    if not attacker_elem or attacker_elem == "none":
        return 1.0
    if is_weak(attacker_elem, defender_elem):
        return 1.5
    if is_resisted(attacker_elem, defender_elem):
        return 0.75
    return 1.0

def element_color(elem):
    from ui import C
    e = _load().get("colors", {})
    name = e.get(elem, "gray")
    return {
        "red": C.RED, "blue": C.BLUE, "green": C.GREEN, "yellow": C.YELLOW,
        "cyan": C.CYAN, "magenta": C.MAGENTA, "white": C.WHITE, "gray": C.GRAY,
    }.get(name, C.WHITE)

def element_label(elem):
    return elem.capitalize() if elem else "None"
