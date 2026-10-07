"""Mentor system — find, talk, learn role."""
import json, os
from config import DATA_DIR

_MENTORS = None

def load_mentors():
    global _MENTORS
    if _MENTORS is not None:
        return _MENTORS
    path = os.path.join(DATA_DIR, "mentors.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _MENTORS = json.load(f).get("mentors", [])
    except Exception:
        _MENTORS = []
    return _MENTORS

def get_mentor(mentor_id):
    for m in load_mentors():
        if m["id"] == mentor_id:
            return m
    return None

def mentors_in_location(location):
    return [m for m in load_mentors() if m.get("location") == location]

def can_train(character_id, mentor, char_dict, stats=None):
    """Return (ok, reason)."""
    import database as db
    reasons = []
    if char_dict["level"] < mentor.get("req_level", 0):
        reasons.append(f"Butuh Level {mentor['req_level']}")
    req_mastery = mentor.get("req_mastery", {})
    for tree_id, lv in req_mastery.items():
        m = db.get_mastery(character_id, tree_id)
        if m["level"] < lv:
            from mastery import get_tree
            t = get_tree(tree_id)
            tname = t["name"] if t else tree_id
            reasons.append(f"Butuh {tname} level {lv}")
    if char_dict["gold"] < mentor.get("cost_gold", 0):
        reasons.append(f"Butuh {mentor['cost_gold']} Gold")
    gl = mentor.get("gender_lock")
    if gl and char_dict["gender"] != gl:
        reasons.append(f"Hanya untuk {gl.capitalize()}")
    if reasons:
        return False, reasons
    return True, []

def train(character_id, mentor_id):
    """Attempt to learn role from mentor. Returns (ok, msg)."""
    import database as db
    mentor = get_mentor(mentor_id)
    if not mentor:
        return False, "Mentor tidak ditemukan."
    char = db.get_character(character_id)
    ok, reasons = can_train(character_id, mentor, char)
    if not ok:
        return False, " | ".join(reasons)
    role_id = mentor["teaches"]
    if db.unlock_role(character_id, role_id):
        # Potong gold
        if mentor.get("cost_gold", 0) > 0:
            db.update_character(character_id, gold=char["gold"] - mentor["cost_gold"])
        db.mark_mentor_trained(character_id, mentor_id)
        from roles import get_role
        r = get_role(role_id)
        return True, f"Role '{r['name'] if r else role_id}' dipelajari!"
    return False, "Role sudah dimiliki."
