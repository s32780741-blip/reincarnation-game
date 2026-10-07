"""Weather system — random per region, affects gameplay."""
import json, os, random, time
from config import DATA_DIR

_W = None


def load_weathers():
    global _W
    if _W is not None:
        return _W
    path = os.path.join(DATA_DIR, "weather.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _W = json.load(f)
    except Exception:
        _W = {"weathers": [], "biome_weather": {}}
    return _W


def get_weather(wid):
    for w in load_weathers().get("weathers", []):
        if w["id"] == wid:
            return w
    return None


def roll_weather(biome):
    """Random weather untuk biome tertentu. Berubah tiap 30 menit."""
    bw = load_weathers().get("biome_weather", {})
    options = bw.get(biome, bw.get("plains", ["clear"]))
    if not options:
        return get_weather("clear")
    wid = random.choice(options)
    return get_weather(wid)


def current_weather_for_region(region_id):
    """Weather berdasarkan jam (deterministik per jam)."""
    from world import get_region
    r = get_region(region_id)
    biome = r.get("biome", "plains") if r else "plains"

    # Seed berdasarkan jam → weather berubah tiap jam
    hour_seed = int(time.time() // 3600)
    random.seed(hash((region_id, hour_seed)) & 0xFFFFFFFF)
    wid = random.choice(load_weathers().get("biome_weather", {}).get(biome, ["clear"]))
    random.seed()
    return get_weather(wid)


def weather_modifier(weather, key, default=1.0):
    if not weather:
        return default
    return weather.get(key, default)


def weather_line(weather):
    if not weather:
        return ""
    from ui import C, color
    col = getattr(C, weather.get("color", "white").upper(), C.WHITE)
    return f"{color(weather.get('icon',''), col)} {color(weather.get('name','?'), col)}"
