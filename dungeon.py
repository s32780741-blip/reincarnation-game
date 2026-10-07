"""Procedural dungeon generator."""
import json, os, random, time
from config import DATA_DIR
import database as db

_D = None


def load_dungeons():
    global _D
    if _D is not None:
        return _D
    path = os.path.join(DATA_DIR, "dungeons.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _D = json.load(f)
    except Exception:
        _D = {"dungeon_themes": [], "floor_types": []}
    return _D


def get_theme(tid):
    for t in load_dungeons().get("dungeon_themes", []):
        if t["id"] == tid:
            return t
    return None


def pick_theme(biome, player_level):
    """Pick dungeon theme sesuai biome + level."""
    themes = load_dungeons().get("dungeon_themes", [])
    candidates = [t for t in themes if biome in t.get("biomes", [])]
    if not candidates:
        candidates = themes
    if not candidates:
        return None
    # Filter by level range
    pool = [t for t in candidates if abs(t.get("level_base", 20) - player_level) <= 40]
    if not pool:
        pool = sorted(candidates, key=lambda t: abs(t.get("level_base", 20) - player_level))[:3]
    return random.choice(pool)


def generate_dungeon(biome, player_level, seed=None):
    """Buat dungeon instance. Return dict."""
    if seed is not None:
        random.seed(seed)
    theme = pick_theme(biome, player_level)
    if not theme:
        return None
    floors = random.randint(theme.get("min_floor", 3), theme.get("max_floor", 6))

    floor_types = load_dungeons().get("floor_types", [])
    types_pool = []
    for ft in floor_types:
        types_pool.extend([ft["id"]] * ft.get("weight", 10))

    floor_list = []
    for i in range(1, floors + 1):
        if i == floors:
            ftype = "boss"
        elif i == 1:
            ftype = "combat"
        else:
            ftype = random.choice(types_pool)
        floor_list.append({
            "floor": i,
            "type": ftype,
            "cleared": False,
        })

    dungeon = {
        "theme": theme,
        "theme_id": theme["id"],
        "name": theme["name"],
        "floors": floor_list,
        "total_floors": floors,
        "current_floor": 1,
        "generated_at": int(time.time()),
        "player_level": player_level,
    }
    random.seed()
    return dungeon


def pick_monster_for_floor(dungeon, floor_num):
    theme = dungeon["theme"]
    pool = theme.get("monster_pool", [])
    if not pool:
        return None
    from monsters import get_monster
    mid = random.choice(pool)
    return get_monster(mid)


def pick_boss_for_dungeon(dungeon):
    theme = dungeon["theme"]
    pool = theme.get("boss_pool", [])
    if not pool:
        return None
    from monsters import get_monster
    bid = random.choice(pool)
    return get_monster(bid)


def floor_type_label(ftype):
    return {
        "combat": "Combat Chamber",
        "treasure": "Treasure Room",
        "trap": "Trap Room",
        "puzzle": "Puzzle Room",
        "rest": "Rest Chamber",
        "boss": "Boss Chamber",
    }.get(ftype, ftype.title())


def save_dungeon_progress(character_id, dungeon):
    """Simpan dungeon aktif ke DB."""
    c = db.conn()
    import json as _json
    c.execute(
        "INSERT OR REPLACE INTO active_dungeon(character_id, data, started_at) VALUES (?,?,?)",
        (character_id, _json.dumps(dungeon), int(time.time()))
    )
    c.commit()


def load_dungeon_progress(character_id):
    c = db.conn()
    row = c.execute(
        "SELECT data, started_at FROM active_dungeon WHERE character_id=?",
        (character_id,)
    ).fetchone()
    if not row:
        return None
    import json as _json
    try:
        return _json.loads(row["data"])
    except Exception:
        return None


def clear_dungeon_progress(character_id):
    c = db.conn()
    c.execute("DELETE FROM active_dungeon WHERE character_id=?", (character_id,))
    c.commit()
