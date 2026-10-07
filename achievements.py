"""Achievement system + auto-check."""
import json, os
from config import DATA_DIR
import database as db

_A = None

def load_achievements():
    global _A
    if _A is not None:
        return _A
    path = os.path.join(DATA_DIR, "achievements.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _A = json.load(f).get("achievements", [])
    except Exception:
        _A = []
    return _A

def get_achievement(aid):
    for a in load_achievements():
        if a["id"] == aid:
            return a
    return None

def unlock(character_id, aid, silent=False):
    a = get_achievement(aid)
    if not a:
        return False
    if db.has_achievement(character_id, aid):
        return False
    if db.unlock_achievement(character_id, aid):
        rw = a.get("reward", {})
        from character import grant_exp
        if rw.get("exp"):
            grant_exp(character_id, rw["exp"])
        char = db.get_character(character_id)
        silver = rw.get("silver", 0)
        gold = rw.get("gold", 0)
        if silver or gold:
            db.update_character(character_id,
                                silver=char["silver"] + silver,
                                gold=char["gold"] + gold)
        if not silent:
            _show_unlock(a)
        return True
    return False

def _show_unlock(a):
    from ui import C, color, box, pause
    print()
    print(box("🏆 ACHIEVEMENT UNLOCKED", [
        color(f" {a['name']}", C.YELLOW + C.BOLD),
        f" {a['desc']}",
    ]))
    pause()

def check_all(character_id, silent=False):
    """Auto-check semua achievement. Dipanggil setelah event penting."""
    unlocked = []

    # Combat
    kills = sum(k["count"] for k in db.get_kills(character_id))
    if kills >= 1:
        if unlock(character_id, "a_first_blood", silent): unlocked.append("First Blood")
    if kills >= 10:
        if unlock(character_id, "a_monster_hunter_10", silent): unlocked.append("Monster Hunter")
    if kills >= 100:
        if unlock(character_id, "a_monster_hunter_100", silent): unlocked.append("Ace Hunter")

    # Quests
    qc = db.get_counter(character_id, "quests_completed")
    if qc >= 1:
        if unlock(character_id, "a_first_quest", silent): unlocked.append("First Quest")
    if qc >= 10:
        if unlock(character_id, "a_quest_10", silent): unlocked.append("Adventurer")
    if qc >= 50:
        if unlock(character_id, "a_quest_50", silent): unlocked.append("Quest Master")

    # Bounty
    bc = db.get_counter(character_id, "bounties_completed")
    if bc >= 1:
        if unlock(character_id, "a_first_bounty", silent): unlocked.append("Bounty Hunter")
    if bc >= 10:
        if unlock(character_id, "a_bounty_10", silent): unlocked.append("Hunter Elite")

    # Level
    char = db.get_character(character_id)
    if char["level"] >= 20:
        if unlock(character_id, "a_level_20", silent): unlocked.append("Growing Strong")
    if char["level"] >= 50:
        if unlock(character_id, "a_level_50", silent): unlocked.append("Veteran Adventurer")
    if char["level"] >= 100:
        if unlock(character_id, "a_level_100", silent): unlocked.append("Master of the Realm")

    # Role
    roles = db.get_roles(character_id)
    if len(roles) >= 2:
        if unlock(character_id, "a_first_role_change", silent): unlocked.append("Versatile")

    from mastery import get_all_mastery
    ms = [m for m in db.get_all_mastery(character_id) if m["level"] >= 3]
    if len(ms) >= 3:
        if unlock(character_id, "a_all_masteries", silent): unlocked.append("Jack of All Trades")

    # Explore
    visited = db.get_visited_cities(character_id)
    if len(visited) >= 5:
        if unlock(character_id, "a_traveler", silent): unlocked.append("Traveler")
    if len(visited) >= 15:
        if unlock(character_id, "a_world_explorer", silent): unlocked.append("World Explorer")

    # Element cores
    from items import get_item
    inv = db.get_inventory(character_id)
    core_types = set()
    for it in inv:
        item = get_item(it["item_id"]) or {}
        if item.get("type") == "element_core":
            core_types.add(it["item_id"])
    if len(core_types) >= 5:
        if unlock(character_id, "a_element_collector", silent): unlocked.append("Element Collector")

    # Wealth
    if char["gold"] >= 10:
        if unlock(character_id, "a_rich", silent): unlocked.append("Wealthy")
    if char["gold"] >= 100:
        if unlock(character_id, "a_very_rich", silent): unlocked.append("Tycoon")

    # Rank
    from rank import get_rank
    r = get_rank(char["level"], bool(char.get("cit_mode")))
    if r["id"] >= 5:
        if unlock(character_id, "a_rank_5", silent): unlocked.append("Rank V")

    return unlocked
