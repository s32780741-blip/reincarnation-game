"""World boss system."""
import json, os, time, random
from config import DATA_DIR
import database as db

_B = None


def load_bosses():
    global _B
    if _B is not None:
        return _B
    path = os.path.join(DATA_DIR, "world_bosses.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _B = json.load(f).get("world_bosses", [])
    except Exception:
        _B = []
    return _B


def get_boss(bid):
    for b in load_bosses():
        if b["id"] == bid:
            return b
    return None


def is_boss_active(character_id, boss):
    """Cek apakah world boss siap di-spawn (tidak dalam cooldown)."""
    last = db.get_world_state(character_id, f"wb_last_{boss['id']}", "0")
    try:
        last_t = int(last)
    except Exception:
        last_t = 0
    respawn_sec = boss.get("respawn_hours", 24) * 3600
    return (time.time() - last_t) >= respawn_sec


def mark_boss_defeated(character_id, boss):
    db.set_world_state(character_id, f"wb_last_{boss['id']}", str(int(time.time())))
    db.inc_counter(character_id, "world_bosses_defeated", 1)


def bosses_in_region(region_id):
    return [b for b in load_bosses() if b.get("region") == region_id]


def roll_boss_encounter(character_id, region_id):
    """Roll untuk encounter world boss di region. Chance kecil."""
    pool = [b for b in bosses_in_region(region_id) if is_boss_active(character_id, b)]
    if not pool:
        return None
    # Base 3% chance
    if random.random() > 0.03:
        return None
    return random.choice(pool)


def grant_boss_reward(character_id, boss):
    from character import grant_exp
    rw = boss.get("reward", {})
    silver = rw.get("silver", 0)
    gold = rw.get("gold", 0)
    exp = rw.get("exp", 0)
    char = db.get_character(character_id)
    if silver or gold:
        db.update_character(character_id,
                            silver=char["silver"] + silver,
                            gold=char["gold"] + gold)
    if exp:
        grant_exp(character_id, exp)
    mark_boss_defeated(character_id, boss)
    return rw
