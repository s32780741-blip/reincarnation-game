"""Mastery tree logic — level up, bonus calculation."""
import json, os
from config import DATA_DIR

_TREES = None

def load_trees():
    global _TREES
    if _TREES is not None:
        return _TREES
    path = os.path.join(DATA_DIR, "masteries.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _TREES = json.load(f).get("trees", {})
    except Exception:
        _TREES = {}
    return _TREES

def get_tree(tree_id):
    return load_trees().get(tree_id)

def get_level_info(tree_id, level):
    t = get_tree(tree_id)
    if not t:
        return None
    for lv in t["levels"]:
        if lv["id"] == level:
            return lv
    return None

def check_levelup(character_id, tree_id, current_exp):
    """Return (new_level, levelup_events) or (current_level, [])."""
    import database as db
    t = get_tree(tree_id)
    if not t:
        return 1, []
    m = db.get_mastery(character_id, tree_id)
    cur_lv = m["level"]
    events = []
    while cur_lv < 6:
        next_lv = get_level_info(tree_id, cur_lv + 1)
        if not next_lv:
            break
        if current_exp >= next_lv["exp_req"]:
            cur_lv += 1
            events.append(cur_lv)
        else:
            break
    if cur_lv != m["level"]:
        db.update_mastery_level(character_id, tree_id, cur_lv)
    return cur_lv, events

def total_bonus(character_id):
    """Aggregate all passive mastery bonuses for a character."""
    import database as db
    trees = load_trees()
    bonuses = {}
    for m in db.get_all_mastery(character_id):
        t = trees.get(m["tree_id"])
        if not t:
            continue
        info = get_level_info(m["tree_id"], m["level"])
        if not info:
            continue
        for k, v in info.get("bonus", {}).items():
            if isinstance(v, (int, float)):
                bonuses[k] = bonuses.get(k, 0) + v
    return bonuses

def mastery_display(character_id, tree_id):
    """Return pretty string for UI."""
    import database as db
    t = get_tree(tree_id)
    if not t:
        return f"[{tree_id}] (unknown)"
    m = db.get_mastery(character_id, tree_id)
    info = get_level_info(tree_id, m["level"])
    name = info["name"] if info else "?"
    roman = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}.get(m["level"], "?")
    return f"{t['name']} {roman} — {name}"
