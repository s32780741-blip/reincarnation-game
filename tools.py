"""Tool helper."""
import database as db
from items import get_item


def has_tool(character_id, tool_id):
    return db.get_item_count(character_id, tool_id) > 0


def find_pickaxe(character_id):
    """Cari pickaxe terbaik di inventory."""
    for tid in ("steel_pickaxe", "iron_pickaxe"):
        if has_tool(character_id, tid):
            return tid
    return None


def find_axe(character_id):
    if has_tool(character_id, "iron_axe"):
        return "iron_axe"
    return None


def find_sickle(character_id):
    if has_tool(character_id, "sickle"):
        return "sickle"
    return None


def find_hoe(character_id):
    if has_tool(character_id, "hoe"):
        return "hoe"
    return None


def tool_tier_bonus(tool_id):
    return {"iron_pickaxe": 0, "steel_pickaxe": 1,
            "iron_axe": 0, "sickle": 0, "hoe": 0}.get(tool_id, 0)
