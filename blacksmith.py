"""Blacksmith — repair, upgrade."""
import random
import database as db
from equipment import (
    get_equipped, SLOT_LABEL, QUALITY_ORDER, get_quality_mult
)
from items import get_item


def repair_cost(slot_row):
    """Biaya repair berdasarkan durability hilang."""
    lost = slot_row["max_durability"] - slot_row["durability"]
    if lost <= 0:
        return 0
    item = get_item(slot_row["item_id"])
    if not item:
        return 0
    base = item.get("price", 50) or 50
    return max(5, int(base * 0.15 * lost / max(1, slot_row["max_durability"])))


def repair_slot(character_id, slot):
    eq = get_equipped(character_id)
    row = eq.get(slot)
    if not row:
        return False, "Slot kosong."
    cost = repair_cost(row)
    if cost == 0:
        return False, "Durability penuh."
    char = db.get_character(character_id)
    if char["silver"] < cost:
        return False, f"Butuh {cost}s."
    db.update_character(character_id, silver=char["silver"] - cost)
    c = db.conn()
    c.execute(
        "UPDATE character_equipment SET durability=max_durability "
        "WHERE character_id=? AND slot=?",
        (character_id, slot)
    )
    c.commit()
    return True, cost


def upgrade_cost(slot_row):
    """Biaya upgrade: exponential per level."""
    lv = slot_row.get("upgrade_level", 0)
    item = get_item(slot_row["item_id"])
    if not item:
        return 0, {}
    base = item.get("price", 100) or 100
    silver_cost = int(base * 0.5 * (1.5 ** lv))
    # Material cost increases
    mat_id = _material_for(item)
    mat_qty = 1 + lv
    return silver_cost, {mat_id: mat_qty}


def _material_for(item):
    """Pilih material dasar berdasarkan tipe item."""
    t = item.get("type")
    if t in ("weapon", "shield"):
        return "iron_ore"
    if t in ("helmet", "chest", "gloves", "legs", "boots"):
        return "beast_hide"
    return "stone_shard"


def upgrade_chance(level):
    """Chance sukses turun per level."""
    return max(0.30, 0.95 - level * 0.08)


def upgrade_slot(character_id, slot):
    eq = get_equipped(character_id)
    row = eq.get(slot)
    if not row:
        return False, "Slot kosong."
    lv = row.get("upgrade_level", 0)
    if lv >= 10:
        return False, "Sudah level maksimum (+10)."
    char = db.get_character(character_id)
    silver_cost, mats = upgrade_cost(row)
    if char["silver"] < silver_cost:
        return False, f"Butuh {silver_cost}s."
    # Cek material
    for mat_id, qty in mats.items():
        if db.get_item_count(character_id, mat_id) < qty:
            item = get_item(mat_id)
            nm = item["name"] if item else mat_id
            return False, f"Butuh {nm} x{qty}."
    # Potong biaya
    db.update_character(character_id, silver=char["silver"] - silver_cost)
    for mat_id, qty in mats.items():
        db.remove_item(character_id, mat_id, qty)

    # Roll
    chance = upgrade_chance(lv)
    if random.random() < chance:
        c = db.conn()
        c.execute(
            "UPDATE character_equipment SET upgrade_level=upgrade_level+1 "
            "WHERE character_id=? AND slot=?",
            (character_id, slot)
        )
        c.commit()
        return True, "success"
    else:
        return True, "fail"


def max_durability_for(item):
    return item.get("durability", 100)
