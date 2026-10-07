"""Guild examination system."""
import json, os, random
from config import DATA_DIR

_E = None

def load_exams():
    global _E
    if _E is not None:
        return _E
    path = os.path.join(DATA_DIR, "exams.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _E = json.load(f).get("categories", {})
    except Exception:
        _E = {}
    return _E

def all_exams():
    out = []
    for cat_id, cat in load_exams().items():
        for e in cat.get("exams", []):
            ex = dict(e)
            ex["category"] = cat_id
            ex["category_name"] = cat["name"]
            out.append(ex)
    return out

def get_exam(eid):
    for e in all_exams():
        if e["id"] == eid:
            return e
    return None

def pick_random_set(count=3):
    """Pick `count` exams from different categories."""
    cats = list(load_exams().keys())
    random.shuffle(cats)
    picked = []
    for cat in cats[:count]:
        exams = load_exams()[cat].get("exams", [])
        if exams:
            picked.append(random.choice(exams) | {"category": cat, "category_name": load_exams()[cat]["name"]})
    return picked

def run_exam(character_id, exam):
    """Return (passed: bool, roll: int, threshold: int, stat_val: int)."""
    import database as db
    stats = db.get_stats(character_id)
    stat_val = stats.get(exam["stat"], 5)
    roll = random.randint(1, 20) + stat_val
    threshold = exam["difficulty"] * 3 + 5
    return roll >= threshold, roll, threshold, stat_val
