"""Item loader — Phase 4 + Phase 8.

Phase 4: items.json      (monster loot, potion, element core, weapon dasar)
Phase 8: items_p8.json   (tools, seeds, crops, refined materials, cooked food)

Semua data item digabung dan di-load sekali (lazy load + cache).
Gunakan reload() untuk memaksa load ulang setelah edit JSON.
"""
import json
import os
from config import DATA_DIR

_I = None


# ============================================================
# INTERNAL LOADER
# ============================================================
def _load_file(filename):
    """Load file JSON item. Return list item atau [] kalau gagal."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("items", [])
    except Exception:
        return []


def load_items():
    """Load semua item dari semua file JSON (dengan cache)."""
    global _I
    if _I is not None:
        return _I

    items = []
    # Phase 4
    items.extend(_load_file("items.json"))
    # Phase 8
    items.extend(_load_file("items_p8.json"))

    # Deteksi ID duplikat — file terakhir menang (Phase 8 override Phase 4)
    seen = {}
    ordered = []
    for it in items:
        if "id" not in it:
            continue
        if it["id"] in seen:
            # Replace yang sudah ada
            idx = seen[it["id"]]
            ordered[idx] = it
        else:
            seen[it["id"]] = len(ordered)
            ordered.append(it)

    _I = ordered
    return _I


def reload():
    """Force reload dari JSON (berguna saat edit data tanpa restart)."""
    global _I
    _I = None
    return load_items()


# ============================================================
# QUERY
# ============================================================
def get_item(iid):
    for it in load_items():
        if it["id"] == iid:
            return it
    return None


def item_name(iid):
    it = get_item(iid)
    return it["name"] if it else iid


def is_stackable(iid):
    """Cek apakah item bisa ditumpuk di inventory."""
    it = get_item(iid)
    return bool(it.get("stackable", False)) if it else True


def items_by_type(type_name):
    """Ambil semua item dengan tipe tertentu."""
    return [it for it in load_items() if it.get("type") == type_name]


def items_by_category(category):
    """Ambil semua item dengan kategori tertentu (untuk crafting filter)."""
    return [it for it in load_items() if it.get("category") == category]


def get_items_where(predicate):
    """Generic filter helper."""
    return [it for it in load_items() if predicate(it)]


# ============================================================
# HELPERS UNTUK UI / CRAFTING / EQUIPMENT
# ============================================================
def is_equipment(iid):
    """Cek apakah item bisa di-equip."""
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") in (
        "weapon", "shield", "helmet", "chest",
        "gloves", "legs", "boots", "ring", "necklace"
    )


def is_consumable(iid):
    """Cek apakah item bisa dikonsumsi (potion/food)."""
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") in ("potion", "food")


def is_material(iid):
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") == "material"


def is_tool(iid):
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") == "tool"


def is_seed(iid):
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") == "seed"


def is_currency(iid):
    it = get_item(iid)
    if not it:
        return False
    return it.get("type") == "currency"


def get_element_core_element(iid):
    """Kalau item = element_core, return elemennya. Else None."""
    it = get_item(iid)
    if not it or it.get("type") != "element_core":
        return None
    return it.get("element")


def get_effect(iid):
    """Return effect dict kalau ada (potion/food)."""
    it = get_item(iid)
    if not it:
        return None
    return it.get("effect")


def get_weapon_damage(iid):
    """Attack value senjata."""
    it = get_item(iid)
    if not it:
        return 0
    return it.get("attack", 0)


def get_armor_defense(iid):
    """Defense value armor."""
    it = get_item(iid)
    if not it:
        return 0
    return it.get("defense", 0)
