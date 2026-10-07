"""Treasure & hidden locations."""
import json, os, random
from config import DATA_DIR
import database as db

_T = None


def load_treasures():
    global _T
    if _T is not None:
        return _T
    path = os.path.join(DATA_DIR, "treasures.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _T = json.load(f)
    except Exception:
        _T = {"hidden_locations": []}
    return _T


def get_hidden_location(hid):
    for h in load_treasures().get("hidden_locations", []):
        if h["id"] == hid:
            return h
    return None


def roll_hidden_location(biome, perception):
    """Cari hidden location yang memenuhi perception."""
    pool = [h for h in load_treasures().get("hidden_locations", [])
            if h.get("biome") == biome and perception >= h.get("req_perception", 5)]
    if not pool:
        return None
    return random.choice(pool)


def claim_treasure(character_id, loot):
    """Beri loot ke karakter."""
    from character import grant_exp
    char = db.get_character(character_id)
    silver = loot.get("silver", 0)
    gold = loot.get("gold", 0)
    if silver or gold:
        db.update_character(character_id,
                            silver=char["silver"] + silver,
                            gold=char["gold"] + gold)
    for item in loot.get("items", []):
        db.add_item(character_id, item["id"], item.get("amount", 1))
    return True
