"""Race system — playable races."""
import json, os
from config import DATA_DIR

_R = None


def load_races():
    global _R
    if _R is not None:
        return _R
    path = os.path.join(DATA_DIR, "races.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _R = json.load(f).get("races", [])
    except Exception:
        _R = []
    return _R


def reload():
    global _R
    _R = None
    return load_races()


def get_race(race_id):
    for r in load_races():
        if r["id"] == race_id:
            return r
    return None


def race_name(race_id):
    r = get_race(race_id)
    return r["name"] if r else race_id


def race_color(race_id):
    from ui import C
    r = get_race(race_id)
    if not r:
        return C.WHITE
    return getattr(C, r.get("color", "white").upper(), C.WHITE)


def races_by_group():
    out = {}
    for r in load_races():
        g = r.get("group", "Other")
        out.setdefault(g, []).append(r)
    return out


def available_races(character_id):
    """Return list races yang bisa dipakai (unlocked)."""
    import database as db
    cit = db.get_character(character_id)
    cit_unlocked = db.get_world_state(character_id, "cit_mode_unlocked", "0") == "1"
    is_cit = bool(cit.get("cit_mode")) if cit else False

    out = []
    for r in load_races():
        unlock = r.get("unlock", "starter")
        if unlock == "starter":
            out.append((r, "unlocked"))
        elif unlock == "cit":
            if cit_unlocked:
                out.append((r, "unlocked"))
            else:
                out.append((r, "locked"))
        elif unlock == "cit_hard":
            if is_cit and db.get_counter(character_id, "cit_races_unlocked") >= 5:
                out.append((r, "unlocked"))
            else:
                out.append((r, "locked"))
        elif unlock == "cit_endgame":
            if is_cit and db.get_counter(character_id, "cit_races_unlocked") >= 15:
                out.append((r, "unlocked"))
            else:
                out.append((r, "locked"))
        else:
            out.append((r, "locked"))
    return out


def bonus_for_race(race_id):
    r = get_race(race_id)
    if not r:
        return {}
    return r.get("base_bonus", {})


def passive_for_race(race_id):
    r = get_race(race_id)
    if not r:
        return ""
    return r.get("passive", "")
