"""Equipment system — slot management, quality, stat bonus."""
import database as db
from items import get_item

SLOTS = ["main_weapon", "off_hand", "helmet", "chest",
         "gloves", "legs", "boots", "ring1", "ring2", "necklace"]

SLOT_LABEL = {
    "main_weapon": "Main Weapon", "off_hand": "Off Hand",
    "helmet": "Helmet", "chest": "Chest", "gloves": "Gloves",
    "legs": "Legs", "boots": "Boots", "ring1": "Ring 1",
    "ring2": "Ring 2", "necklace": "Necklace",
}

SLOT_ACCEPTS = {
    "main_weapon": ["weapon"],
    "off_hand": ["shield", "weapon"],
    "helmet": ["helmet"], "chest": ["chest"],
    "gloves": ["gloves"], "legs": ["legs"], "boots": ["boots"],
    "ring1": ["ring"], "ring2": ["ring"], "necklace": ["necklace"],
}

QUALITY_MULT = {
    "broken": 0.3, "poor": 0.5, "low": 0.7, "average": 0.85,
    "normal": 1.0, "good": 1.15, "high": 1.3, "superior": 1.5,
    "excellent": 1.75, "masterwork": 2.0, "legendary": 3.0,
}

QUALITY_COLOR = {
    "broken": "red", "poor": "red", "low": "yellow", "average": "yellow",
    "normal": "white", "good": "green", "high": "green",
    "superior": "cyan", "excellent": "cyan", "masterwork": "magenta",
    "legendary": "yellow",
}

QUALITY_ORDER = ["broken", "poor", "low", "average", "normal",
                 "good", "high", "superior", "excellent", "masterwork", "legendary"]


def get_equipped(character_id):
    """Return dict slot -> row."""
    c = db.conn()
    rows = c.execute(
        "SELECT slot, item_id, quality, durability, max_durability, upgrade_level "
        "FROM character_equipment WHERE character_id=?",
        (character_id,)
    ).fetchall()
    out = {slot: None for slot in SLOTS}
    for r in rows:
        out[r["slot"]] = dict(r)
    return out


def get_quality_mult(quality):
    return QUALITY_MULT.get(quality, 1.0)


def item_effective_stat(item, key, quality="normal", upgrade_level=0):
    """Base stat × quality mult + upgrade bonus."""
    base = item.get(key, 0)
    if not isinstance(base, (int, float)):
        return 0
    mult = get_quality_mult(quality)
    up = 1 + upgrade_level * 0.1  # +10% per upgrade
    return int(base * mult * up)


def can_equip(item, slot):
    """Cek apakah item cocok untuk slot."""
    if not item:
        return False
    return item.get("type") in SLOT_ACCEPTS.get(slot, [])


def equip_item(character_id, inv_item_id, slot):
    """Pindahkan item dari inventory ke equipment slot."""
    inv = db.get_inventory(character_id)
    target = None
    for it in inv:
        if it["id"] == inv_item_id:
            target = it
            break
    if not target:
        return False, "Item tidak ditemukan di inventory."
    item = get_item(target["item_id"])
    if not item:
        return False, "Item tidak valid."
    if not can_equip(item, slot):
        return False, f"Item tidak cocok untuk slot {SLOT_LABEL[slot]}."

    # Unequip existing
    _unequip_slot_internal(character_id, slot)

    # Move: delete 1 qty from inventory (equipment non-stackable → qty=1)
    db.remove_item(character_id, target["item_id"], 1)

    # Insert into equipment
    c = db.conn()
    c.execute(
        "INSERT INTO character_equipment"
        "(character_id, slot, item_id, quality, durability, max_durability, upgrade_level) "
        "VALUES (?,?,?,?,?,?,0)",
        (character_id, slot, target["item_id"],
         target.get("quality", "normal"),
         target.get("durability", 100),
         target.get("max_durability", 100))
    )
    c.commit()
    return True, f"Equipped {item['name']} pada {SLOT_LABEL[slot]}."


def _unequip_slot_internal(character_id, slot):
    """Internal — pindahkan item dari equipment ke inventory."""
    eq = get_equipped(character_id)
    current = eq.get(slot)
    if not current:
        return False
    db.add_item(character_id, current["item_id"], 1)
    c = db.conn()
    c.execute("DELETE FROM character_equipment WHERE character_id=? AND slot=?",
              (character_id, slot))
    c.commit()
    return True


def unequip_slot(character_id, slot):
    ok = _unequip_slot_internal(character_id, slot)
    if ok:
        return True, "Unequipped."
    return False, "Slot kosong."


def get_total_equipment_bonus(character_id):
    """Sum semua stat dari equipment (attack, defense, magic_attack, dll)."""
    eq = get_equipped(character_id)
    bonus = {}
    for slot, row in eq.items():
        if not row:
            continue
        item = get_item(row["item_id"])
        if not item:
            continue
        q = row.get("quality", "normal")
        up = row.get("upgrade_level", 0)
        for key in ("attack", "magic_attack", "defense", "magic_defense",
                    "speed", "crit", "accuracy", "hp", "mana", "stamina",
                    "luck", "critical", "intelligence", "strength", "endurance",
                    "agility", "persuasion", "block"):
            if key in item:
                bonus[key] = bonus.get(key, 0) + item_effective_stat(item, key, q, up)
    return bonus


def durability_check(item_id, durability, max_durability):
    """Return (multiplier, label)."""
    if max_durability <= 0:
        return 1.0, "OK"
    pct = durability / max_durability
    if durability <= 0:
        return 0.3, "BROKEN"
    if pct < 0.2:
        return 0.7, "Poor"
    if pct < 0.5:
        return 0.9, "Worn"
    return 1.0, "OK"


def reduce_durability(character_id, slot, amount=1):
    """Kurangi durability equipment slot."""
    c = db.conn()
    row = c.execute(
        "SELECT durability FROM character_equipment WHERE character_id=? AND slot=?",
        (character_id, slot)
    ).fetchone()
    if not row:
        return
    new_dur = max(0, row["durability"] - amount)
    c.execute(
        "UPDATE character_equipment SET durability=? WHERE character_id=? AND slot=?",
        (new_dur, character_id, slot)
    )
    c.commit()
