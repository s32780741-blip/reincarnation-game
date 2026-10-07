"""Guild system core: join, exam, rank up, recruitment."""
import random, time
import database as db
from ui import C, color
from guilds import get_guild, load_guilds
from exams import pick_random_set, run_exam
from npc import get_npc, recruitable_npcs

# ---------- player guild membership ----------
def get_player_guild(character_id):
    """Return (guild_id, rank) or (None, None)."""
    c = db.conn()
    row = c.execute(
        "SELECT guild_id, rank, contribution FROM character_guild WHERE character_id=?",
        (character_id,)
    ).fetchone()
    if row:
        return dict(row)
    return None

def set_player_guild(character_id, guild_id, rank="F"):
    c = db.conn()
    c.execute(
        "INSERT INTO character_guild(character_id, guild_id, rank, joined_at, contribution) "
        "VALUES (?,?,?,?,0) "
        "ON CONFLICT(character_id) DO UPDATE SET guild_id=excluded.guild_id, rank=excluded.rank, joined_at=excluded.joined_at",
        (character_id, guild_id, rank, int(time.time()))
    )
    c.commit()

def leave_guild(character_id):
    c = db.conn()
    c.execute("DELETE FROM character_guild WHERE character_id=?", (character_id,))
    c.commit()

def add_contribution(character_id, amount):
    c = db.conn()
    c.execute(
        "UPDATE character_guild SET contribution=contribution+? WHERE character_id=?",
        (amount, character_id)
    )
    c.commit()

RANK_ORDER = ["F", "E", "D", "C", "B", "A", "S"]
RANK_NAMES = {"F": "Recruit", "E": "Member", "D": "Veteran", "C": "Elite",
              "B": "Officer", "A": "Vice Captain", "S": "Guild Master"}
RANK_CONTRIBUTION = {"F": 0, "E": 100, "D": 500, "C": 1500, "B": 4000, "A": 10000, "S": 30000}

def can_rank_up(character_id):
    pg = get_player_guild(character_id)
    if not pg:
        return False, None, None
    cur = pg["rank"]
    idx = RANK_ORDER.index(cur)
    if idx >= len(RANK_ORDER) - 1:
        return False, cur, None
    next_rank = RANK_ORDER[idx + 1]
    needed = RANK_CONTRIBUTION[next_rank]
    return pg["contribution"] >= needed, cur, next_rank

def rank_up(character_id):
    ok, cur, nxt = can_rank_up(character_id)
    if not ok or not nxt:
        return False, None
    c = db.conn()
    c.execute("UPDATE character_guild SET rank=? WHERE character_id=?", (nxt, character_id))
    c.commit()
    return True, nxt

# ---------- guild examination ----------
def run_guild_exam(character_id, guild_id):
    """Return dict summary."""
    g = get_guild(guild_id)
    if not g:
        return {"ok": False, "reason": "Guild tidak ditemukan."}
    char = db.get_character(character_id)
    req = g.get("join_req", {})
    if char["level"] < req.get("level", 0):
        return {"ok": False, "reason": f"Butuh Level {req['level']}"}
    from rank import get_rank
    cur_rank = get_rank(char["level"], bool(char.get("cit_mode")))["id"]
    if cur_rank < req.get("rank_req", 1):
        return {"ok": False, "reason": f"Butuh Rank {req['rank_req']}"}

    # Run 3 exams
    exams = pick_random_set(3)
    results = []
    passed_count = 0
    for ex in exams:
        ok, roll, thresh, stat_val = run_exam(character_id, ex)
        results.append({
            "exam": ex, "ok": ok, "roll": roll, "threshold": thresh, "stat": stat_val
        })
        if ok:
            passed_count += 1

    overall = passed_count >= 2
    c = db.conn()
    c.execute(
        "INSERT INTO guild_exam_attempts(character_id, guild_id, passed, score, attempted_at) "
        "VALUES (?,?,?,?,?)",
        (character_id, guild_id, 1 if overall else 0, passed_count, int(time.time()))
    )
    c.commit()

    return {"ok": overall, "passed_count": passed_count, "total": 3, "results": results, "guild": g}

# ---------- recruitment (incoming applications) ----------
def maybe_spawn_application(character_id):
    """Kalau player di guild dengan rank cukup, NPC mungkin kirim aplikasi."""
    pg = get_player_guild(character_id)
    if not pg:
        return None
    # Rank player global
    char = db.get_character(character_id)
    from rank import get_rank
    player_rank = get_rank(char["level"], bool(char.get("cit_mode")))["id"]

    # Cek sudah punya pending?
    c = db.conn()
    pending = c.execute(
        "SELECT COUNT(*) AS n FROM guild_applications WHERE character_id=? AND status='pending'",
        (character_id,)
    ).fetchone()["n"]
    if pending >= 3:
        return None

    # 15% chance
    if random.random() > 0.15:
        return None

    # Pool recruitable sesuai rank
    pool = [n for n in recruitable_npcs() if n.get("recruit_req", {}).get("player_rank", 99) <= player_rank]
    if not pool:
        return None
    # Filter yang sudah di-apply
    existing = c.execute(
        "SELECT npc_id FROM guild_applications WHERE character_id=?",
        (character_id,)
    ).fetchall()
    taken = {r["npc_id"] for r in existing}
    pool = [n for n in pool if n["id"] not in taken]
    if not pool:
        return None

    npc = random.choice(pool)
    reason = npc.get("application_reason", "...")
    c.execute(
        "INSERT INTO guild_applications(character_id, npc_id, status, applied_at, reason) "
        "VALUES (?,?,?,?,?)",
        (character_id, npc["id"], "pending", int(time.time()), reason)
    )
    c.commit()
    return npc

def get_applications(character_id, status="pending"):
    c = db.conn()
    rows = c.execute(
        "SELECT id, npc_id, status, applied_at, reason FROM guild_applications "
        "WHERE character_id=? AND status=? ORDER BY applied_at DESC",
        (character_id, status)
    ).fetchall()
    return [dict(r) for r in rows]

def resolve_application(character_id, app_id, accept=True):
    c = db.conn()
    row = c.execute(
        "SELECT npc_id FROM guild_applications WHERE id=? AND character_id=?",
        (app_id, character_id)
    ).fetchone()
    if not row:
        return False, "Application tidak ditemukan"
    npc_id = row["npc_id"]
    new_status = "accepted" if accept else "rejected"
    c.execute(
        "UPDATE guild_applications SET status=? WHERE id=?",
        (new_status, app_id)
    )
    if accept:
        pg = get_player_guild(character_id)
        guild_id = pg["guild_id"] if pg else "player_guild"
        c.execute(
            "INSERT INTO guild_members(guild_id, npc_id, rank, joined_at, power) "
            "VALUES (?,?,?,?,?)",
            (guild_id, npc_id, "E", int(time.time()), get_npc(npc_id).get("level", 10) * 10)
        )
    c.commit()
    return True, new_status

def get_guild_members(character_id):
    """Member guild tempat player bergabung."""
    pg = get_player_guild(character_id)
    if not pg:
        return []
    c = db.conn()
    rows = c.execute(
        "SELECT npc_id, rank, joined_at, power FROM guild_members WHERE guild_id=? ORDER BY joined_at DESC",
        (pg["guild_id"],)
    ).fetchall()
    return [dict(r) for r in rows]

# ---------- relationship ----------
def get_relationship(character_id, npc_id):
    c = db.conn()
    row = c.execute(
        "SELECT relationship, met_at, last_interaction FROM npc_relationships "
        "WHERE character_id=? AND npc_id=?",
        (character_id, npc_id)
    ).fetchone()
    if not row:
        c.execute(
            "INSERT INTO npc_relationships(character_id, npc_id, relationship, met_at) "
            "VALUES (?,?,0,?)",
            (character_id, npc_id, int(time.time()))
        )
        c.commit()
        return {"relationship": 0, "met_at": int(time.time()), "last_interaction": None}
    return dict(row)

def change_relationship(character_id, npc_id, amount):
    get_relationship(character_id, npc_id)
    c = db.conn()
    c.execute(
        "UPDATE npc_relationships SET relationship=relationship+?, last_interaction=? "
        "WHERE character_id=? AND npc_id=?",
        (amount, int(time.time()), character_id, npc_id)
    )
    c.commit()

def remember(character_id, npc_id, event):
    c = db.conn()
    c.execute(
        "INSERT INTO npc_memory(character_id, npc_id, event, at_time) VALUES (?,?,?,?)",
        (character_id, npc_id, event, int(time.time()))
    )
    c.commit()

def get_memory(character_id, npc_id, limit=5):
    c = db.conn()
    rows = c.execute(
        "SELECT event, at_time FROM npc_memory WHERE character_id=? AND npc_id=? "
        "ORDER BY id DESC LIMIT ?",
        (character_id, npc_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]
