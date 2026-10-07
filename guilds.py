"""Guild loader."""
import json, os
from config import DATA_DIR

_G = None

def load_guilds():
    global _G
    if _G is not None:
        return _G
    path = os.path.join(DATA_DIR, "guilds.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _G = json.load(f).get("guilds", [])
    except Exception:
        _G = []
    return _G

def get_guild(gid):
    for g in load_guilds():
        if g["id"] == gid:
            return g
    return None

def guild_name(gid):
    g = get_guild(gid)
    return g["name"] if g else gid

def by_rank():
    return sorted(load_guilds(), key=lambda g: g["rank_global"])

def guild_color(gid):
    from ui import C
    g = get_guild(gid)
    if not g:
        return C.WHITE
    return {
        "cyan": C.CYAN, "red": C.RED, "white": C.WHITE,
        "magenta": C.MAGENTA, "yellow": C.YELLOW,
    }.get(g.get("color", "white"), C.WHITE)
