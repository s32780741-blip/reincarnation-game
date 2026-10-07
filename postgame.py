"""Post-game content."""
import json, os, random, time
from config import DATA_DIR
import database as db

_P = None


def load_postgame():
    global _P
    if _P is not None:
        return _P
    path = os.path.join(DATA_DIR, "postgame.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _P = json.load(f)
    except Exception:
        _P = {}
    return _P


# ============================================================
# ENDLESS DUNGEON
# ============================================================
def endless_start_floor(character_id):
    val = db.get_world_state(character_id, "endless_current_floor", "0")
    try:
        return int(val)
    except Exception:
        return 0


def endless_best_floor(character_id):
    val = db.get_world_state(character_id, "endless_best_floor", "0")
    try:
        return int(val)
    except Exception:
        return 0


def endless_next_floor(character_id, current_floor):
    """Pick monster & level untuk floor berikutnya."""
    cfg = load_postgame().get("endless_dungeon", {})
    base = cfg.get("base_level", 100)
    per_floor = cfg.get("level_per_floor", 5)
    pool = cfg.get("enemy_pool", [])
    if not pool:
        return None
    from monsters import get_monster, scale_monster
    mid = random.choice(pool)
    base_m = get_monster(mid)
    if not base_m:
        return None
    target_level = base + (current_floor + 1) * per_floor
    offset = max(0, target_level - base_m["level"])
    scaled = scale_monster(base_m, level_offset=offset)
    scaled["level"] = target_level
    return scaled


def endless_reward(character_id, floor):
    cfg = load_postgame().get("endless_dungeon", {})
    rw = cfg.get("reward_per_floor", {})
    mult = 1 + floor * 0.1
    char = db.get_character(character_id)
    silver = int(rw.get("silver", 500) * mult)
    gold = int(rw.get("gold", 5) * mult)
    exp = int(rw.get("exp", 2000) * mult)
    db.update_character(character_id, silver=char["silver"] + silver,
                        gold=char["gold"] + gold)
    from character import grant_exp
    grant_exp(character_id, exp)
    return {"silver": silver, "gold": gold, "exp": exp}


def endless_update_floor(character_id, new_floor):
    db.set_world_state(character_id, "endless_current_floor", str(new_floor))
    if new_floor > endless_best_floor(character_id):
        db.set_world_state(character_id, "endless_best_floor", str(new_floor))
        db.inc_counter(character_id, "endless_best_floor", new_floor -
                       db.get_counter(character_id, "endless_best_floor"))
    # Milestone achievements
    cfg = load_postgame().get("endless_dungeon", {}).get("milestones", {})
    ms = cfg.get(str(new_floor))
    if ms and ms.get("reward") == "achievement":
        try:
            from achievements import unlock
            unlock(character_id, ms["id"], silent=False)
        except Exception:
            pass


def endless_reset(character_id):
    db.set_world_state(character_id, "endless_current_floor", "0")


# ============================================================
# ARENA
# ============================================================
def arena_get_wave(character_id):
    val = db.get_world_state(character_id, "arena_wave", "0")
    try:
        return int(val)
    except Exception:
        return 0


def arena_set_wave(character_id, wave):
    db.set_world_state(character_id, "arena_wave", str(wave))


def arena_reset(character_id):
    db.set_world_state(character_id, "arena_wave", "0")


def arena_next_wave(character_id):
    cfg = load_postgame().get("arena", {})
    waves = cfg.get("waves", [])
    wave_idx = arena_get_wave(character_id)
    if wave_idx >= len(waves):
        return None
    w = waves[wave_idx]
    return w


def arena_clear_wave(character_id):
    arena_set_wave(character_id, arena_get_wave(character_id) + 1)


def arena_complete_reward(character_id):
    cfg = load_postgame().get("arena", {})
    rw = cfg.get("rewards", {})
    char = db.get_character(character_id)
    db.update_character(character_id,
                        silver=char["silver"] + rw.get("silver", 5000),
                        gold=char["gold"] + rw.get("gold", 100))
    from character import grant_exp
    grant_exp(character_id, rw.get("exp", 15000))
    if rw.get("achievement"):
        try:
            from achievements import unlock
            unlock(character_id, rw["achievement"], silent=False)
        except Exception:
            pass
    arena_reset(character_id)
    db.inc_counter(character_id, "arena_completions", 1)


# ============================================================
# BOSS RUSH
# ============================================================
def boss_rush_index(character_id):
    val = db.get_world_state(character_id, "boss_rush_idx", "0")
    try:
        return int(val)
    except Exception:
        return 0


def boss_rush_next(character_id):
    cfg = load_postgame().get("boss_rush", {})
    seq = cfg.get("sequence", [])
    idx = boss_rush_index(character_id)
    if idx >= len(seq):
        return None
    from world_boss import get_boss
    return get_boss(seq[idx])


def boss_rush_advance(character_id):
    new_idx = boss_rush_index(character_id) + 1
    db.set_world_state(character_id, "boss_rush_idx", str(new_idx))
    return new_idx


def boss_rush_reset(character_id):
    db.set_world_state(character_id, "boss_rush_idx", "0")


def boss_rush_complete_reward(character_id):
    cfg = load_postgame().get("boss_rush", {})
    rw = cfg.get("rewards", {})
    char = db.get_character(character_id)
    db.update_character(character_id,
                        silver=char["silver"] + rw.get("silver", 20000),
                        gold=char["gold"] + rw.get("gold", 300))
    from character import grant_exp
    grant_exp(character_id, rw.get("exp", 50000))
    if rw.get("achievement"):
        try:
            from achievements import unlock
            unlock(character_id, rw["achievement"], silent=False)
        except Exception:
            pass
    boss_rush_reset(character_id)
    db.inc_counter(character_id, "boss_rush_completions", 1)


def boss_rush_total():
    cfg = load_postgame().get("boss_rush", {})
    return len(cfg.get("sequence", []))


# ============================================================
# UNLOCK CHECK
# ============================================================
def is_postgame_unlocked(character_id):
    """Post-game terbuka setelah main story selesai."""
    from story import progress_percent
    ending = db.get_world_state(character_id, "ending_id")
    return bool(ending) or progress_percent(character_id) >= 100
