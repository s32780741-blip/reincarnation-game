"""Bounty system."""
import json, os
from config import DATA_DIR
import database as db

_B = None

def load_bounties():
    global _B
    if _B is not None:
        return _B
    path = os.path.join(DATA_DIR, "bounties.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _B = json.load(f).get("bounties", [])
    except Exception:
        _B = []
    return _B

def get_bounty(bid):
    for b in load_bounties():
        if b["id"] == bid:
            return b
    return None

def threat_color(threat):
    from ui import C
    return {
        "low": C.GREEN, "medium": C.YELLOW, "high": C.RED,
        "very_high": C.MAGENTA, "extreme": C.RED, "catastrophic": C.RED,
    }.get(threat, C.WHITE)

def accept_bounty(character_id, bounty_id):
    ok = db.add_bounty(character_id, bounty_id)
    if ok:
        db.inc_counter(character_id, "bounties_accepted", 1)
    return ok

def grant_bounty_reward(character_id, bounty):
    from character import grant_exp
    rw = bounty.get("reward", {})
    summary = {"exp": 0, "silver": 0, "gold": 0, "reputation": [], "level_ups": []}

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

    for fac, amt in rw.get("reputation", {}).items():
        if ":" in fac:
            t, fid = fac.split(":", 1)
            db.add_reputation(character_id, t, fid, amt)
            summary["reputation"].append((fac, amt))

    db.inc_counter(character_id, "bounties_completed", 1)
    return summary

def complete_bounty(character_id, bounty):
    db.update_bounty_status(character_id, bounty["id"], "completed")
    return grant_bounty_reward(character_id, bounty)

def check_bounty_kill(character_id, monster_id):
    """Kalau monster yang dibunuh cocok dengan bounty aktif, tandai."""
    active = db.get_bounties(character_id, status="accepted")
    matched = []
    for b in active:
        data = get_bounty(b["bounty_id"])
        if not data: continue
        if data.get("target_monster") == monster_id and data.get("condition") == "defeat":
            db.update_bounty_status(character_id, b["bounty_id"], "ready_to_turn_in")
            matched.append(data)
    return matched

def active_bounties(character_id):
    ids = [b["bounty_id"] for b in db.get_bounties(character_id, status="accepted")]
    return [get_bounty(i) for i in ids if get_bounty(i)]

def available_bounties(character_id):
    taken = {b["bounty_id"] for b in db.get_bounties(character_id)}
    out = []
    for b in load_bounties():
        if b["id"] in taken and not b.get("repeatable"):
            continue
        out.append(b)
    return out
