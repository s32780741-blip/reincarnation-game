"""Cooking logic."""
import json, os
from config import DATA_DIR
import database as db
from items import get_item

_C = None


def load_recipes():
    global _C
    if _C is not None:
        return _C
    path = os.path.join(DATA_DIR, "cooking.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _C = json.load(f).get("recipes", [])
    except Exception:
        _C = []
    return _C


def get_recipe(rid):
    for r in load_recipes():
        if r["id"] == rid:
            return r
    return None


def can_cook(character_id, recipe):
    reasons = []
    req = recipe.get("cooking_req", 1)
    m = db.get_mastery(character_id, "cooking")
    cur = m["level"]
    if cur < req:
        reasons.append(f"Butuh Cooking Lv{req} (kamu {cur})")
    for mat in recipe.get("materials", []):
        if mat["amount"] <= 0:
            continue
        have = db.get_item_count(character_id, mat["id"])
        if have < mat["amount"]:
            item = get_item(mat["id"])
            reasons.append(f"Butuh {item['name'] if item else mat['id']} x{mat['amount']} (punya {have})")
    return (len(reasons) == 0), reasons


def cook(character_id, recipe):
    ok, reasons = can_cook(character_id, recipe)
    if not ok:
        return False, reasons
    for mat in recipe.get("materials", []):
        if mat["amount"] > 0:
            db.remove_item(character_id, mat["id"], mat["amount"])
    out = recipe["output"]
    db.add_item(character_id, out["id"], out["amount"])
    exp = recipe.get("exp", 15)
    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, "cooking", exp)
    events = check_levelup(character_id, "cooking", new_exp)
    db.inc_counter(character_id, "meals_cooked", out["amount"])
    return True, {"output": out, "exp": exp, "level_ups": events}
