"""Skill loading & usage."""
import json, os
from config import DATA_DIR

_SKILLS = None

def load_skills():
    global _SKILLS
    if _SKILLS is not None:
        return _SKILLS
    path = os.path.join(DATA_DIR, "skills.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _SKILLS = json.load(f).get("skills", [])
    except Exception:
        _SKILLS = []
    return _SKILLS

def get_skill(skill_id):
    for s in load_skills():
        if s["id"] == skill_id:
            return s
    return None

def skills_for_role(role_id):
    return [s for s in load_skills() if s.get("role") == role_id]

def available_skills(character_id, role_id):
    """Skills the character can learn given current mastery."""
    import database as db
    from mastery import get_tree
    tree_id = None
    for s in skills_for_role(role_id):
        if tree_id is None:
            break
    # Ambil tree dari role
    from roles import mastery_tree
    tree_id = mastery_tree(role_id)
    m = db.get_mastery(character_id, tree_id)
    cur_lv = m["level"]
    learned = {s["skill_id"] for s in db.get_skills(character_id)}
    out = []
    for s in skills_for_role(role_id):
        out.append({
            "skill": s,
            "learned": s["id"] in learned,
            "unlockable": cur_lv >= s.get("mastery_req", 1),
        })
    return out

def classify(skill):
    return skill.get("type", "active")
