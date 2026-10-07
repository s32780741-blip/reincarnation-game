"""Monster loader + random spawn + mutation."""
import json, os, random
from config import DATA_DIR

_M = None

def load_monsters():
    global _M
    if _M is not None:
        return _M
    path = os.path.join(DATA_DIR, "monsters.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _M = json.load(f).get("monsters", [])
    except Exception:
        _M = []
    return _M

def get_monster(mid):
    for m in load_monsters():
        if m["id"] == mid:
            return m
    return None

RANK_WEIGHTS = {
    "common": 60, "uncommon": 25, "normal": 10, "rare": 4,
    "epic": 1.0, "mythic": 0.1, "beast": 3, "high_beast": 0.5,
    "king_beast": 0.05, "demon_beast": 0.005,
}

RANK_ORDER = ["common", "uncommon", "normal", "rare", "epic", "mythic",
              "beast", "high_beast", "king_beast", "demon_beast"]

def scale_monster(monster, level_offset=0, difficulty_mult=1.0):
    """Return a scaled copy for combat. Does not mutate source."""
    m = dict(monster)
    lv = max(1, m["level"] + level_offset)
    # scale stats roughly proportional
    base_lv = monster["level"]
    factor = 1 + (lv - base_lv) * 0.08
    if factor < 0.3: factor = 0.3
    m["level"] = lv
    m["hp"] = int(m["hp"] * factor * difficulty_mult)
    m["max_hp"] = m["hp"]
    m["mp"] = int(m["mp"] * factor)
    m["max_mp"] = m["mp"]
    m["attack"] = int(m["attack"] * factor * difficulty_mult)
    m["defense"] = int(m["defense"] * factor)
    m["speed"] = int(m["speed"] * (1 + (lv - base_lv) * 0.05))
    m["exp"] = int(m["exp"] * factor)
    return m

def maybe_mutate(monster):
    """Mutation: rare+ can mutate with small chance. Returns (monster, mutated_bool, mutation_label)."""
    if monster.get("rank") in ("common", "uncommon"):
        return monster, False, None
    chance = {"normal": 0.02, "rare": 0.06, "epic": 0.05, "mythic": 0.04,
              "beast": 0.03, "high_beast": 0.05, "king_beast": 0.05, "demon_beast": 0.03}.get(monster["rank"], 0.03)
    if random.random() > chance:
        return monster, False, None
    m = dict(monster)
    # Mutasi elemen atau stat
    mutations = [
        ("elemental", "Fire",  "fire"),
        ("elemental", "Frost", "ice"),
        ("elemental", "Storm", "lightning"),
        ("elemental", "Shadow","dark"),
        ("elemental", "Holy",  "light"),
        ("elemental", "Toxic", "poison"),
    ]
    kind, label, elem = random.choice(mutations)
    m["name"] = f"{label} Mutated {monster['name']}"
    m["element"] = elem
    m["hp"] = int(m["hp"] * 1.5)
    m["max_hp"] = m["hp"]
    m["attack"] = int(m["attack"] * 1.4)
    m["defense"] = int(m["defense"] * 1.2)
    m["exp"] = int(m["exp"] * 2.0)
    m["is_mutation"] = True
    # Boost drops x1.5
    new_drops = []
    for d in m.get("drops", []):
        nd = dict(d)
        nd["chance"] = min(1.0, d.get("chance", 0.5) * 1.5)
        new_drops.append(nd)
    m["drops"] = new_drops
    return m, True, label

def pick_random_monster(player_level, region_danger=1, rank_bias=None):
    """Pick a monster suitable for player level in a region."""
    monsters = load_monsters()
    if not monsters:
        return None
    # Filter by level range: player_level - 10 to player_level + 15 + danger
    lo = max(1, player_level - 12)
    hi = player_level + 10 + region_danger * 3
    pool = [m for m in monsters if lo <= m["level"] <= hi]
    if not pool:
        # fallback: nearest by level
        pool = sorted(monsters, key=lambda m: abs(m["level"] - player_level))[:10]

    # Weight by rank
    weighted = []
    for m in pool:
        w = RANK_WEIGHTS.get(m["rank"], 1)
        # Avoid too-strong monsters spawning often
        if m["level"] > player_level + 20:
            w *= 0.2
        weighted.append((m, w))
    if not weighted:
        return None
    total = sum(w for _, w in weighted)
    r = random.random() * total
    acc = 0
    for m, w in weighted:
        acc += w
        if r <= acc:
            return m
    return weighted[-1][0]

def rank_color(rank):
    from ui import C
    return {
        "common": C.GRAY, "uncommon": C.WHITE, "normal": C.GREEN,
        "rare": C.CYAN, "epic": C.MAGENTA, "mythic": C.YELLOW,
        "beast": C.GREEN, "high_beast": C.CYAN,
        "king_beast": C.MAGENTA, "demon_beast": C.RED,
    }.get(rank, C.WHITE)

def rank_label(rank):
    return rank.replace("_", " ").title()
