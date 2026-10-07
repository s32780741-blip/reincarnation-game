"""Random events engine."""
import json, os, random, time
from config import DATA_DIR

_E = None


def load_events():
    global _E
    if _E is not None:
        return _E
    path = os.path.join(DATA_DIR, "events.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _E = json.load(f)
    except Exception:
        _E = {"events": [], "treasure_tables": {}}
    return _E


def get_event(eid):
    for e in load_events().get("events", []):
        if e["id"] == eid:
            return e
    return None


def roll_event(biome, exclude_types=None):
    """Pick random event yang cocok untuk biome."""
    pool = []
    for e in load_events().get("events", []):
        if biome and biome not in e.get("biomes", []):
            continue
        if exclude_types and e.get("type") in exclude_types:
            continue
        pool.append(e)
    if not pool:
        return None
    # Weighted choice
    total = sum(e.get("weight", 1) for e in pool)
    r = random.random() * total
    acc = 0
    for e in pool:
        acc += e.get("weight", 1)
        if r <= acc:
            return e
    return pool[-1]


def roll_treasure(table_name):
    """Roll treasure dari tabel."""
    tables = load_events().get("treasure_tables", {})
    table = tables.get(table_name, [])
    if not table:
        return {}
    result = {"silver": 0, "gold": 0, "items": []}
    for entry in table:
        if random.random() > entry.get("chance", 1.0):
            continue
        if "silver" in entry:
            lo, hi = entry["silver"]
            result["silver"] += random.randint(lo, hi)
        if "gold" in entry:
            lo, hi = entry["gold"]
            result["gold"] += random.randint(lo, hi)
        if "item" in entry:
            amt = entry.get("amount", 1)
            if isinstance(amt, list) and amt and isinstance(amt[0], int):
                n = random.randint(amt[0], amt[1]) if len(amt) > 1 else amt[0]
            else:
                n = 1
            result["items"].append({"id": entry["item"], "amount": n})
    return result
