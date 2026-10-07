"""Crafting logic."""
import json, os, random
from config import DATA_DIR
import database as db
from items import get_item

_R = None


def load_recipes():
    global _R
    if _R is not None:
        return _R
    path = os.path.join(DATA_DIR, "recipes.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _R = json.load(f).get("recipes", [])
    except Exception:
        _R = []
    return _R


def get_recipe(rid):
    for r in load_recipes():
        if r["id"] == rid:
            return r
    return None


def recipes_by_category(cat):
    return [r for r in load_recipes() if r.get("category") == cat]


def get_crafting_skill(character_id):
    """Crafting mastery level dari mastery tree."""
    m = db.get_mastery(character_id, "blacksmithing")
    return m["level"]


def can_craft(character_id, recipe):
    """Return (ok, reasons)."""
    reasons = []
    req = recipe.get("crafting_req", 1)
    cur = get_crafting_skill(character_id)
    if cur < req:
        reasons.append(f"Butuh Crafting Lv{req} (kamu {cur})")
    for m in recipe.get("materials", []):
        if m["amount"] <= 0:
            continue
        have = db.get_item_count(character_id, m["id"])
        if have < m["amount"]:
            item = get_item(m["id"])
            reasons.append(f"Butuh {item['name'] if item else m['id']} x{m['amount']} (punya {have})")
    return (len(reasons) == 0), reasons


def craft(character_id, recipe):
    ok, reasons = can_craft(character_id, recipe)
    if not ok:
        return False, reasons

    # Consume materials
    for m in recipe.get("materials", []):
        if m["amount"] > 0:
            db.remove_item(character_id, m["id"], m["amount"])

    # Add output
    out = recipe["output"]
    db.add_item(character_id, out["id"], out["amount"])

    # Mastery EXP
    exp = recipe.get("exp", 10)
    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, "blacksmithing", exp)
    events = check_levelup(character_id, "blacksmithing", new_exp)

    db.inc_counter(character_id, "items_crafted", out["amount"])

    return True, {"output": out, "exp": exp, "level_ups": events}
