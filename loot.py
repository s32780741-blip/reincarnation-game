"""Loot roll + add to inventory."""
import random
import database as db
from monsters import scale_monster

def roll_loot(monster, luck_bonus=0):
    """Return list of {id, amount}."""
    drops = []
    luck_mult = 1 + luck_bonus / 100.0
    for d in monster.get("drops", []):
        chance = min(0.99, d.get("chance", 0.5) * luck_mult)
        if random.random() <= chance:
            amt = d.get("amount")
            if isinstance(amt, list):
                n = random.randint(amt[0], amt[1])
            else:
                n = 1
            drops.append({"id": d["id"], "amount": n})
    return drops

def apply_loot_to_char(character_id, drops):
    """Add drops to inventory or currency."""
    from items import get_item
    silver_gain = 0
    gold_gain = 0
    zambrut_gain = 0
    items_gained = []
    for d in drops:
        item = get_item(d["id"])
        if not item:
            # unknown → treat as material default
            db.add_item(character_id, d["id"], d["amount"])
            items_gained.append((d["id"], d["amount"]))
            continue
        if item["type"] == "currency":
            if d["id"] == "silver":
                silver_gain += d["amount"]
            elif d["id"] == "gold":
                gold_gain += d["amount"]
            elif d["id"] == "zambrut":
                zambrut_gain += d["amount"]
        else:
            db.add_item(character_id, d["id"], d["amount"])
            items_gained.append((d["id"], d["amount"]))
    if silver_gain or gold_gain or zambrut_gain:
        char = db.get_character(character_id)
        db.update_character(
            character_id,
            silver=char["silver"] + silver_gain,
            gold=char["gold"] + gold_gain,
            zambrut=char["zambrut"] + zambrut_gain,
        )
    return {
        "silver": silver_gain,
        "gold": gold_gain,
        "zambrut": zambrut_gain,
        "items": items_gained,
    }
