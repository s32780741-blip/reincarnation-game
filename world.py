"""World — regions + travel logic."""
import json, os, random
from config import DATA_DIR

_R = None

def load_regions():
    global _R
    if _R is not None:
        return _R
    path = os.path.join(DATA_DIR, "regions.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _R = json.load(f).get("regions", [])
    except Exception:
        _R = []
    return _R

def get_region(rid):
    for r in load_regions():
        if r["id"] == rid:
            return r
    return None

def regions_in_kingdom(kid):
    return [r for r in load_regions() if r["kingdom"] == kid]

def random_travel_event():
    """Random event saat perjalanan."""
    events = [
        {"type": "encounter", "text": "Sekelompok bandit menghadang di jalan!"},
        {"type": "merchant",  "text": "Pedagang keliling menawarkan barang langka."},
        {"type": "traveler",  "text": "Musafir meminta bantuan menunjukkan arah."},
        {"type": "weather",   "text": "Badai tiba-tiba menerjang perjalananmu."},
        {"type": "treasure",  "text": "Kamu menemukan peti tua terkubur."},
        {"type": "none",      "text": "Perjalanan berjalan lancar."},
    ]
    weights = [25, 15, 15, 10, 5, 30]
    return random.choices(events, weights=weights, k=1)[0]

def travel_time(city_a, city_b):
    """Travel time dalam in-game menit."""
    from cities import get_city
    a, b = get_city(city_a), get_city(city_b)
    if not a or not b:
        return 120
    # Estimasi sederhana dari danger
    base = 60 + (a.get("danger", 1) + b.get("danger", 1)) * 30
    if a["kingdom"] != b["kingdom"]:
        base += 180
    return base
