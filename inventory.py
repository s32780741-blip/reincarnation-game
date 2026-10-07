"""Inventory helpers."""
import database as db
from items import get_item, is_stackable, item_name

def total_weight(character_id):
    inv = db.get_inventory(character_id)
    w = 0.0
    for it in inv:
        item = get_item(it["item_id"])
        if not item: continue
        w += item.get("weight", 0.1) * it["quantity"]
    return round(w, 1)

def carry_capacity(character_id):
    stats = db.get_stats(character_id)
    return stats.get("carry", 10) * 5  # 1 carry = 5kg

def is_overweight(character_id):
    return total_weight(character_id) > carry_capacity(character_id)

def group_by_type(character_id):
    inv = db.get_inventory(character_id)
    groups = {}
    for it in inv:
        item = get_item(it["item_id"])
        t = item.get("type", "misc") if item else "misc"
        groups.setdefault(t, []).append(it)
    return groups
