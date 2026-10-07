"""Story engine — progression, cutscene, endings."""
import json, os, time
from config import DATA_DIR
import database as db

_M = None
_L = None
_C = None
_G = None
_K = None
_E = None


def _load(filename):
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def main_chapters():
    global _M
    if _M is None:
        _M = _load("story_main.json").get("chapters", [])
    return _M


def all_lore():
    global _L
    if _L is None:
        _L = _load("story_lore.json").get("lore", [])
    return _L


def character_stories():
    global _C
    if _C is None:
        _C = _load("story_character.json")
    return _C


def guild_stories():
    global _G
    if _G is None:
        _G = _load("story_guild.json").get("guild_stories", {})
    return _G


def kingdom_stories():
    global _K
    if _K is None:
        _K = _load("story_kingdom.json").get("kingdom_stories", {})
    return _K


def all_endings():
    global _E
    if _E is None:
        _E = _load("story_endings.json").get("endings", [])
    return _E


# ============================================================
# PROGRESS
# ============================================================
def get_chapter(chid):
    for c in main_chapters():
        if c["id"] == chid:
            return c
    return None


def current_chapter_id(character_id):
    """Chapter yang sedang aktif (prereq terpenuhi, belum selesai)."""
    completed = db.get_world_state(character_id, "chapters_completed", "") or ""
    completed_set = set(x for x in completed.split(",") if x)

    # Cari chapter yang prereq-nya selesai tapi belum selesai
    for c in main_chapters():
        if c["id"] in completed_set:
            continue
        prereq = c.get("prereq")
        if prereq is None or prereq in completed_set:
            return c["id"]
    return None


def mark_chapter_complete(character_id, chid):
    current = db.get_world_state(character_id, "chapters_completed", "") or ""
    ids = set(x for x in current.split(",") if x)
    ids.add(chid)
    db.set_world_state(character_id, "chapters_completed", ",".join(sorted(ids)))
    db.inc_counter(character_id, "chapters_completed", 1)


def is_chapter_complete(character_id, chid):
    current = db.get_world_state(character_id, "chapters_completed", "") or ""
    return chid in current.split(",")


def total_chapters():
    return len(main_chapters())


def progress_percent(character_id):
    current = db.get_world_state(character_id, "chapters_completed", "") or ""
    done = len([x for x in current.split(",") if x])
    return int(done / max(1, total_chapters()) * 100)


# ============================================================
# LORE
# ============================================================
def unlock_lore(character_id, lore_id):
    current = db.get_world_state(character_id, "lore_unlocked", "") or ""
    ids = set(x for x in current.split(",") if x)
    if lore_id in ids:
        return False
    ids.add(lore_id)
    db.set_world_state(character_id, "lore_unlocked", ",".join(sorted(ids)))
    db.inc_counter(character_id, "lore_collected", 1)
    return True


def has_lore(character_id, lore_id):
    current = db.get_world_state(character_id, "lore_unlocked", "") or ""
    return lore_id in current.split(",")


def get_lore(lore_id):
    for l in all_lore():
        if l["id"] == lore_id:
            return l
    return None


def unlocked_lore(character_id):
    current = db.get_world_state(character_id, "lore_unlocked", "") or ""
    ids = [x for x in current.split(",") if x]
    return [get_lore(i) for i in ids if get_lore(i)]


# ============================================================
# CHARACTER / GUILD / KINGDOM STORIES
# ============================================================
def get_gender_story(gender):
    return character_stories().get("gender_paths", {}).get(gender)


def get_role_story(role_id):
    return character_stories().get("role_stories", {}).get(role_id)


def get_guild_story(guild_id):
    return guild_stories().get(guild_id)


def get_kingdom_story(kingdom_id):
    return kingdom_stories().get(kingdom_id)


# ============================================================
# ENDINGS
# ============================================================
def check_ending_available(character_id):
    """Return list ending yang bisa diambil sekarang."""
    from guild_system import get_player_guild
    char = db.get_character(character_id)
    pg = get_player_guild(character_id)

    all_done = is_chapter_complete(character_id, "ch12") or (
        progress_percent(character_id) >= 100
    )
    if not all_done:
        return []

    endings = []
    has_elara = db.get_relationship(character_id, "elara").get("relationship", 0) >= 30 \
        if db.get_world_state(character_id, "met_elara", "0") == "1" else False

    for e in all_endings():
        eid = e["id"]
        if eid == "end_cycle_broken":
            if has_elara:
                endings.append(e)
        elif eid == "end_eternal_guardian":
            endings.append(e)
        elif eid == "end_return_home":
            if has_elara:
                endings.append(e)
        elif eid == "end_sacrifice":
            if not has_elara:
                endings.append(e)
        elif eid == "end_void_consumed":
            endings.append(e)
        elif eid == "end_dragon_ascension":
            if char.get("role") == "dragon_knight" and has_elara:
                endings.append(e)
    return endings


def apply_ending(character_id, ending_id):
    """Apply ending reward."""
    for e in all_endings():
        if e["id"] == ending_id:
            rw = e.get("reward", {})
            from character import grant_exp
            if rw.get("exp"):
                grant_exp(character_id, rw["exp"])
            char = db.get_character(character_id)
            if rw.get("gold"):
                db.update_character(character_id, gold=char["gold"] + rw["gold"])
            if rw.get("achievement"):
                try:
                    from achievements import unlock
                    unlock(character_id, rw["achievement"], silent=False)
                except Exception:
                    pass
            db.set_world_state(character_id, "ending_id", ending_id)
            db.set_world_state(character_id, "ending_at", str(int(time.time())))
            return e
    return None
