"""Quest loader + objective checking + reward grant."""
import json, os, time
from config import DATA_DIR
import database as db

_Q = None

def load_quests():
    global _Q
    if _Q is not None:
        return _Q
    path = os.path.join(DATA_DIR, "quests.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _Q = json.load(f).get("quests", [])
    except Exception:
        _Q = []
    return _Q

def get_quest(qid):
    for q in load_quests():
        if q["id"] == qid:
            return q
    return None

def quests_by_difficulty(diff):
    return [q for q in load_quests() if q.get("difficulty") == diff]

def is_eligible(char, quest):
    """Check level & rank req."""
    from rank import get_rank
    if char["level"] < quest.get("level_req", 0):
        return False, f"Butuh Level {quest['level_req']}"
    cur_rank = get_rank(char["level"], bool(char.get("cit_mode")))["id"]
    if cur_rank < quest.get("rank_req", 1):
        return False, f"Butuh Rank {quest['rank_req']}"
    return True, None

def objective_progress(character_id, obj, char=None):
    """Return (current, target)."""
    t = obj.get("type")
    target = obj.get("amount", 1)
    if t == "kill":
        from database import conn
        c = conn()
        row = c.execute(
            "SELECT count FROM monster_kills WHERE character_id=? AND monster_id=?",
            (character_id, obj["monster"])
        ).fetchone()
        return (row["count"] if row else 0), target
    if t == "collect":
        return db.get_item_count(character_id, obj["item"]), target
    if t == "visit":
        visited = db.get_visited_cities(character_id)
        return (1 if obj["city"] in visited else 0), 1
    return 0, target

def objective_complete(character_id, obj):
    cur, tgt = objective_progress(character_id, obj)
    return cur >= tgt

def quest_objectives_complete(character_id, quest):
    for obj in quest.get("objectives", []):
        if not objective_complete(character_id, obj):
            return False
    return True

def objective_text(obj, character_id):
    cur, tgt = objective_progress(character_id, obj)
    desc = obj.get("desc", f"{obj.get('type','?')} {tgt}")
    mark = "✓" if cur >= tgt else "•"
    return f"{mark} {desc} [{cur}/{tgt}]"

def grant_rewards(character_id, quest):
    """Give EXP, silver, gold, items, reputation. Return summary dict."""
    from character import grant_exp
    rw = quest.get("rewards", {})
    summary = {"exp": 0, "silver": 0, "gold": 0, "items": [], "reputation": [], "level_ups": []}

    if rw.get("exp"):
        events = grant_exp(character_id, rw["exp"])
        summary["exp"] = rw["exp"]
        summary["level_ups"] = events

    char = db.get_character(character_id)
    silver = rw.get("silver", 0)
    gold = rw.get("gold", 0)
    if silver or gold:
        db.update_character(
            character_id,
            silver=char["silver"] + silver,
            gold=char["gold"] + gold
        )
        summary["silver"] = silver
        summary["gold"] = gold

    for item in rw.get("items", []):
        db.add_item(character_id, item["id"], item.get("amount", 1))
        summary["items"].append(item)

    for fac, amt in rw.get("reputation", {}).items():
        if ":" in fac:
            t, fid = fac.split(":", 1)
            db.add_reputation(character_id, t, fid, amt)
            summary["reputation"].append((fac, amt))

    # counters
    db.inc_counter(character_id, "quests_completed", 1)
    db.inc_counter(character_id, f"quests_completed_{quest.get('difficulty','?')}", 1)

    return summary

def complete_quest(character_id, quest):
    db.update_quest_status(character_id, quest["id"], "completed")
    return grant_rewards(character_id, quest)

def available_quests(character_id):
    """Quests not yet taken and eligible."""
    char = db.get_character(character_id)
    taken = {q["quest_id"] for q in db.get_quests(character_id)}
    out = []
    for q in load_quests():
        if q["id"] in taken and not q.get("repeatable"):
            continue
        eligible, _ = is_eligible(char, q)
        out.append((q, eligible))
    return out

def active_quests(character_id):
    ids = [q["quest_id"] for q in db.get_quests(character_id, status="active")]
    return [get_quest(i) for i in ids if get_quest(i)]
