"""SQLite database layer — FINAL Phase 1-12 lengkap.

Phase 1  : accounts, characters, stats, world_state
Phase 2  : roles, mastery, skills, mentors, skill_cooldowns
Phase 3  : world_unlocks, travel_log
Phase 4  : inventory, monster_kills, combat_log
Phase 5  : quests, bounties, achievements, reputation, counters, cities_visited
Phase 6  : guild, guild_members, guild_applications, guild_exam_attempts,
           npc_relationships, npc_memory, world_npc_state
Phase 7  : character_equipment
Phase 8  : farming_plots
Phase 9  : active_dungeon, world_events_log
Phase 10 : story_log
Phase 11 : race_history, cit_log
Phase 12 : ng_plus_log
"""
import sqlite3
import os
import hashlib
import secrets
import hmac
import time as _time
from config import DB_PATH

_conn = None


def conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA foreign_keys = ON")
    return _conn


SCHEMA = """
-- ============================================================
-- PHASE 1 — ACCOUNT, CHARACTER, STATS, WORLD STATE
-- ============================================================
CREATE TABLE IF NOT EXISTS accounts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    created_at    INTEGER NOT NULL,
    last_login    INTEGER
);

CREATE TABLE IF NOT EXISTS characters (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id     INTEGER NOT NULL,
    name           TEXT NOT NULL,
    gender         TEXT NOT NULL,
    race           TEXT NOT NULL DEFAULT 'Human',
    level          INTEGER NOT NULL DEFAULT 15,
    exp            INTEGER NOT NULL DEFAULT 0,
    rank_id        INTEGER NOT NULL DEFAULT 2,
    role           TEXT NOT NULL DEFAULT 'fighter',
    location       TEXT NOT NULL DEFAULT 'aurelia',
    silver         INTEGER NOT NULL DEFAULT 100,
    gold           INTEGER NOT NULL DEFAULT 0,
    zambrut        INTEGER NOT NULL DEFAULT 0,
    hp_current     INTEGER NOT NULL DEFAULT 100,
    mp_current     INTEGER NOT NULL DEFAULT 50,
    stamina_current INTEGER NOT NULL DEFAULT 80,
    attr_points    INTEGER NOT NULL DEFAULT 15,
    cit_mode       INTEGER NOT NULL DEFAULT 0,
    created_at     INTEGER NOT NULL,
    updated_at     INTEGER NOT NULL,
    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_stats (
    character_id INTEGER PRIMARY KEY,
    strength INTEGER DEFAULT 5,
    intelligence INTEGER DEFAULT 5,
    defense INTEGER DEFAULT 5,
    endurance INTEGER DEFAULT 5,
    dexterity INTEGER DEFAULT 5,
    agility INTEGER DEFAULT 5,
    speed INTEGER DEFAULT 5,
    jump INTEGER DEFAULT 3,
    mana INTEGER DEFAULT 5,
    hp INTEGER DEFAULT 10,
    stamina INTEGER DEFAULT 8,
    swimming INTEGER DEFAULT 3,
    perception INTEGER DEFAULT 5,
    stealth INTEGER DEFAULT 3,
    luck INTEGER DEFAULT 5,
    critical INTEGER DEFAULT 3,
    accuracy INTEGER DEFAULT 5,
    carry INTEGER DEFAULT 10,
    mining INTEGER DEFAULT 1,
    gathering INTEGER DEFAULT 1,
    crafting INTEGER DEFAULT 1,
    persuasion INTEGER DEFAULT 3,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_state (
    character_id INTEGER NOT NULL,
    key          TEXT NOT NULL,
    value        TEXT,
    PRIMARY KEY(character_id, key),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 2 — ROLES, MASTERY, SKILLS, MENTORS
-- ============================================================
CREATE TABLE IF NOT EXISTS character_roles (
    character_id INTEGER NOT NULL,
    role_id      TEXT NOT NULL,
    unlocked_at  INTEGER NOT NULL,
    is_active    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, role_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_mastery (
    character_id INTEGER NOT NULL,
    tree_id      TEXT NOT NULL,
    level        INTEGER NOT NULL DEFAULT 1,
    exp          INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, tree_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_skills (
    character_id INTEGER NOT NULL,
    skill_id     TEXT NOT NULL,
    learned_at   INTEGER NOT NULL,
    times_used   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, skill_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_mentors (
    character_id INTEGER NOT NULL,
    mentor_id    TEXT NOT NULL,
    met_at       INTEGER NOT NULL,
    trained      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, mentor_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS skill_cooldowns (
    character_id INTEGER NOT NULL,
    skill_id     TEXT NOT NULL,
    ready_at     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, skill_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 3 — WORLD UNLOCKS, TRAVEL LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS world_unlocks (
    character_id INTEGER NOT NULL,
    unlock_id    TEXT NOT NULL,
    unlocked_at  INTEGER NOT NULL,
    PRIMARY KEY(character_id, unlock_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS travel_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    from_city    TEXT,
    to_city      TEXT,
    method       TEXT,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 4 — INVENTORY, KILLS, COMBAT LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS character_inventory (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id   INTEGER NOT NULL,
    item_id        TEXT NOT NULL,
    quantity       INTEGER NOT NULL DEFAULT 1,
    quality        TEXT DEFAULT 'normal',
    durability     INTEGER DEFAULT 100,
    max_durability INTEGER DEFAULT 100,
    acquired_at    INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS monster_kills (
    character_id INTEGER NOT NULL,
    monster_id   TEXT NOT NULL,
    count        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, monster_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS combat_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    monster_id   TEXT NOT NULL,
    monster_lv   INTEGER,
    result       TEXT,
    turns        INTEGER,
    exp_gain     INTEGER,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 5 — QUEST, BOUNTY, ACHIEVEMENT, REPUTATION
-- ============================================================
CREATE TABLE IF NOT EXISTS character_quests (
    character_id INTEGER NOT NULL,
    quest_id     TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active',
    started_at   INTEGER NOT NULL,
    completed_at INTEGER,
    PRIMARY KEY(character_id, quest_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_bounties (
    character_id INTEGER NOT NULL,
    bounty_id    TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'accepted',
    accepted_at  INTEGER NOT NULL,
    completed_at INTEGER,
    PRIMARY KEY(character_id, bounty_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_achievements (
    character_id   INTEGER NOT NULL,
    achievement_id TEXT NOT NULL,
    unlocked_at    INTEGER NOT NULL,
    PRIMARY KEY(character_id, achievement_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_reputation (
    character_id INTEGER NOT NULL,
    faction_type TEXT NOT NULL,
    faction_id   TEXT NOT NULL,
    value        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, faction_type, faction_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_stats_counter (
    character_id INTEGER NOT NULL,
    key          TEXT NOT NULL,
    value        INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(character_id, key),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS character_cities_visited (
    character_id INTEGER NOT NULL,
    city_id      TEXT NOT NULL,
    first_visit  INTEGER NOT NULL,
    PRIMARY KEY(character_id, city_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 6 — GUILD & NPC
-- ============================================================
CREATE TABLE IF NOT EXISTS character_guild (
    character_id INTEGER PRIMARY KEY,
    guild_id     TEXT NOT NULL,
    rank         TEXT DEFAULT 'F',
    joined_at    INTEGER NOT NULL,
    contribution INTEGER DEFAULT 0,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guild_members (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id   TEXT NOT NULL,
    npc_id     TEXT NOT NULL,
    rank       TEXT DEFAULT 'E',
    joined_at  INTEGER NOT NULL,
    power      INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS guild_applications (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    npc_id       TEXT NOT NULL,
    status       TEXT DEFAULT 'pending',
    applied_at   INTEGER NOT NULL,
    reason       TEXT,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guild_exam_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    guild_id     TEXT NOT NULL,
    passed       INTEGER DEFAULT 0,
    score        INTEGER DEFAULT 0,
    attempted_at INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS npc_relationships (
    character_id     INTEGER NOT NULL,
    npc_id           TEXT NOT NULL,
    relationship     INTEGER DEFAULT 0,
    met_at           INTEGER NOT NULL,
    last_interaction INTEGER,
    PRIMARY KEY(character_id, npc_id),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS npc_memory (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    npc_id       TEXT NOT NULL,
    event        TEXT NOT NULL,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_npc_state (
    npc_id           TEXT PRIMARY KEY,
    location         TEXT,
    status           TEXT DEFAULT 'alive',
    current_activity TEXT,
    updated_at       INTEGER
);

-- ============================================================
-- PHASE 7 — EQUIPMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS character_equipment (
    character_id   INTEGER NOT NULL,
    slot           TEXT NOT NULL,
    item_id        TEXT NOT NULL,
    quality        TEXT DEFAULT 'normal',
    durability     INTEGER DEFAULT 100,
    max_durability INTEGER DEFAULT 100,
    upgrade_level  INTEGER DEFAULT 0,
    PRIMARY KEY(character_id, slot),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 8 — FARMING
-- ============================================================
CREATE TABLE IF NOT EXISTS farming_plots (
    character_id INTEGER NOT NULL,
    plot_index   INTEGER NOT NULL,
    state        TEXT NOT NULL DEFAULT 'empty',
    seed_id      TEXT,
    crop_id      TEXT,
    planted_at   INTEGER,
    water_count  INTEGER DEFAULT 0,
    PRIMARY KEY(character_id, plot_index),
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 9 — DUNGEON & WORLD EVENTS
-- ============================================================
CREATE TABLE IF NOT EXISTS active_dungeon (
    character_id INTEGER PRIMARY KEY,
    data         TEXT NOT NULL,
    started_at   INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS world_events_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    event_id     TEXT NOT NULL,
    region_id    TEXT,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 10 — STORY LOG
-- ============================================================
CREATE TABLE IF NOT EXISTS story_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    event_type   TEXT NOT NULL,
    event_id     TEXT NOT NULL,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 11 — RACE & CIT
-- ============================================================
CREATE TABLE IF NOT EXISTS race_history (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    race_id      TEXT NOT NULL,
    changed_at   INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    action       TEXT NOT NULL,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- PHASE 12 — NEW GAME+
-- ============================================================
CREATE TABLE IF NOT EXISTS ng_plus_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    ng_level     INTEGER NOT NULL,
    at_time      INTEGER NOT NULL,
    FOREIGN KEY(character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_char_account ON characters(account_id);
CREATE INDEX IF NOT EXISTS idx_inv_char ON character_inventory(character_id);
CREATE INDEX IF NOT EXISTS idx_quest_char ON character_quests(character_id);
CREATE INDEX IF NOT EXISTS idx_bounty_char ON character_bounties(character_id);
CREATE INDEX IF NOT EXISTS idx_apps_char ON guild_applications(character_id);
CREATE INDEX IF NOT EXISTS idx_eq_char ON character_equipment(character_id);
CREATE INDEX IF NOT EXISTS idx_farm_char ON farming_plots(character_id);
CREATE INDEX IF NOT EXISTS idx_kills_char ON monster_kills(character_id);
CREATE INDEX IF NOT EXISTS idx_rep_char ON character_reputation(character_id);
CREATE INDEX IF NOT EXISTS idx_npc_rel_char ON npc_relationships(character_id);
CREATE INDEX IF NOT EXISTS idx_events_char ON world_events_log(character_id);
CREATE INDEX IF NOT EXISTS idx_story_char ON story_log(character_id);
CREATE INDEX IF NOT EXISTS idx_race_char ON race_history(character_id);
CREATE INDEX IF NOT EXISTS idx_cit_char ON cit_log(character_id);
CREATE INDEX IF NOT EXISTS idx_ng_char ON ng_plus_log(character_id);
"""


def init():
    c = conn()
    c.executescript(SCHEMA)
    c.commit()


def close():
    global _conn
    if _conn:
        _conn.close()
        _conn = None


# ============================================================
# PHASE 1 — PASSWORD
# ============================================================
def _hash(password, salt):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000,
    ).hex()


def create_account(username, password):
    username = username.strip()
    if not username:
        return False, "empty_username"
    if len(username) < 3:
        return False, "short_username"
    if len(password) < 4:
        return False, "short_password"
    salt = secrets.token_hex(16)
    ph = _hash(password, salt)
    try:
        c = conn()
        c.execute(
            "INSERT INTO accounts(username, password_hash, salt, created_at) VALUES (?,?,?,?)",
            (username, ph, salt, int(_time.time())),
        )
        c.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "username_exists"
    except Exception as e:
        return False, f"db_error:{e}"


def verify_login(username, password):
    c = conn()
    row = c.execute(
        "SELECT * FROM accounts WHERE username=?", (username.strip(),)
    ).fetchone()
    if not row:
        _hash(password, "x" * 32)
        return None
    expected = row["password_hash"]
    actual = _hash(password, row["salt"])
    if hmac.compare_digest(expected, actual):
        c.execute(
            "UPDATE accounts SET last_login=? WHERE id=?",
            (int(_time.time()), row["id"]),
        )
        c.commit()
        return dict(row)
    return None


def get_account(username):
    c = conn()
    row = c.execute(
        "SELECT * FROM accounts WHERE username=?", (username,)
    ).fetchone()
    return dict(row) if row else None


# ============================================================
# PHASE 1 — CHARACTER
# ============================================================
def create_character(account_id, name, gender, role="fighter", race="Human"):
    c = conn()
    now = int(_time.time())
    cur = c.execute(
        """INSERT INTO characters(account_id, name, gender, race, role, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?)""",
        (account_id, name, gender, race, role, now, now),
    )
    cid = cur.lastrowid
    c.execute("INSERT INTO character_stats(character_id) VALUES (?)", (cid,))
    c.commit()
    return cid


def get_characters(account_id):
    c = conn()
    rows = c.execute(
        "SELECT id, name, gender, race, level, rank_id, role "
        "FROM characters WHERE account_id=? ORDER BY id",
        (account_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_character(character_id):
    c = conn()
    row = c.execute(
        "SELECT * FROM characters WHERE id=?", (character_id,)
    ).fetchone()
    return dict(row) if row else None


def get_stats(character_id):
    c = conn()
    row = c.execute(
        "SELECT * FROM character_stats WHERE character_id=?", (character_id,)
    ).fetchone()
    return dict(row) if row else None


def update_character(character_id, **fields):
    if not fields:
        return
    fields["updated_at"] = int(_time.time())
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [character_id]
    c = conn()
    c.execute(f"UPDATE characters SET {cols} WHERE id=?", vals)
    c.commit()


def update_stats(character_id, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [character_id]
    c = conn()
    c.execute(f"UPDATE character_stats SET {cols} WHERE character_id=?", vals)
    c.commit()


def delete_character(character_id):
    c = conn()
    c.execute("DELETE FROM characters WHERE id=?", (character_id,))
    c.commit()


# ============================================================
# PHASE 1 — WORLD STATE
# ============================================================
def set_world_state(character_id, key, value):
    c = conn()
    c.execute(
        "INSERT INTO world_state(character_id, key, value) VALUES (?,?,?) "
        "ON CONFLICT(character_id, key) DO UPDATE SET value=excluded.value",
        (character_id, key, str(value)),
    )
    c.commit()


def get_world_state(character_id, key, default=None):
    c = conn()
    row = c.execute(
        "SELECT value FROM world_state WHERE character_id=? AND key=?",
        (character_id, key),
    ).fetchone()
    return row["value"] if row else default


# ============================================================
# PHASE 2 — ROLES
# ============================================================
def unlock_role(character_id, role_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_roles(character_id, role_id, unlocked_at, is_active) "
            "VALUES (?,?,?,0)",
            (character_id, role_id, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_roles(character_id):
    c = conn()
    rows = c.execute(
        "SELECT role_id, is_active FROM character_roles "
        "WHERE character_id=? ORDER BY unlocked_at",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_active_role(character_id, role_id):
    c = conn()
    c.execute(
        "UPDATE character_roles SET is_active=0 WHERE character_id=?",
        (character_id,),
    )
    c.execute(
        "UPDATE character_roles SET is_active=1 WHERE character_id=? AND role_id=?",
        (character_id, role_id),
    )
    c.execute(
        "UPDATE characters SET role=? WHERE id=?", (role_id, character_id)
    )
    c.commit()


# ============================================================
# PHASE 2 — MASTERY
# ============================================================
def get_mastery(character_id, tree_id):
    c = conn()
    row = c.execute(
        "SELECT level, exp FROM character_mastery WHERE character_id=? AND tree_id=?",
        (character_id, tree_id),
    ).fetchone()
    if not row:
        c.execute(
            "INSERT INTO character_mastery(character_id, tree_id, level, exp) "
            "VALUES (?,?,1,0)",
            (character_id, tree_id),
        )
        c.commit()
        return {"level": 1, "exp": 0}
    return dict(row)


def get_all_mastery(character_id):
    c = conn()
    rows = c.execute(
        "SELECT tree_id, level, exp FROM character_mastery WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_mastery_exp(character_id, tree_id, amount):
    m = get_mastery(character_id, tree_id)
    new_exp = m["exp"] + amount
    c = conn()
    c.execute(
        "UPDATE character_mastery SET exp=? WHERE character_id=? AND tree_id=?",
        (new_exp, character_id, tree_id),
    )
    c.commit()
    return new_exp


def update_mastery_level(character_id, tree_id, level):
    c = conn()
    c.execute(
        "UPDATE character_mastery SET level=? WHERE character_id=? AND tree_id=?",
        (level, character_id, tree_id),
    )
    c.commit()


# ============================================================
# PHASE 2 — SKILLS
# ============================================================
def learn_skill(character_id, skill_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_skills(character_id, skill_id, learned_at) "
            "VALUES (?,?,?)",
            (character_id, skill_id, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_skills(character_id):
    c = conn()
    rows = c.execute(
        "SELECT skill_id, times_used FROM character_skills WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def use_skill(character_id, skill_id):
    c = conn()
    c.execute(
        "UPDATE character_skills SET times_used=times_used+1 "
        "WHERE character_id=? AND skill_id=?",
        (character_id, skill_id),
    )
    c.commit()


# ============================================================
# PHASE 2 — MENTORS
# ============================================================
def meet_mentor(character_id, mentor_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_mentors(character_id, mentor_id, met_at) "
            "VALUES (?,?,?)",
            (character_id, mentor_id, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_mentors(character_id):
    c = conn()
    rows = c.execute(
        "SELECT mentor_id, trained FROM character_mentors WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def mark_mentor_trained(character_id, mentor_id):
    c = conn()
    c.execute(
        "UPDATE character_mentors SET trained=1 WHERE character_id=? AND mentor_id=?",
        (character_id, mentor_id),
    )
    c.commit()


# ============================================================
# PHASE 3 — WORLD UNLOCKS & TRAVEL
# ============================================================
def add_world_unlock(character_id, unlock_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO world_unlocks(character_id, unlock_id, unlocked_at) "
            "VALUES (?,?,?)",
            (character_id, unlock_id, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def has_world_unlock(character_id, unlock_id):
    c = conn()
    row = c.execute(
        "SELECT 1 FROM world_unlocks WHERE character_id=? AND unlock_id=?",
        (character_id, unlock_id),
    ).fetchone()
    return bool(row)


def log_travel(character_id, from_city, to_city, method):
    c = conn()
    c.execute(
        "INSERT INTO travel_log(character_id, from_city, to_city, method, at_time) "
        "VALUES (?,?,?,?,?)",
        (character_id, from_city, to_city, method, int(_time.time())),
    )
    c.commit()


def get_travel_log(character_id, limit=10):
    c = conn()
    rows = c.execute(
        "SELECT from_city, to_city, method, at_time FROM travel_log "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 4 — INVENTORY
# ============================================================
def add_item(character_id, item_id, amount=1):
    from items import is_stackable

    c = conn()
    if is_stackable(item_id):
        row = c.execute(
            "SELECT id, quantity FROM character_inventory "
            "WHERE character_id=? AND item_id=? LIMIT 1",
            (character_id, item_id),
        ).fetchone()
        if row:
            c.execute(
                "UPDATE character_inventory SET quantity=quantity+? WHERE id=?",
                (amount, row["id"]),
            )
        else:
            c.execute(
                "INSERT INTO character_inventory"
                "(character_id, item_id, quantity, acquired_at) VALUES (?,?,?,?)",
                (character_id, item_id, amount, int(_time.time())),
            )
    else:
        for _ in range(amount):
            c.execute(
                "INSERT INTO character_inventory"
                "(character_id, item_id, quantity, acquired_at) VALUES (?,?,1,?)",
                (character_id, item_id, int(_time.time())),
            )
    c.commit()


def remove_item(character_id, item_id, amount=1):
    c = conn()
    row = c.execute(
        "SELECT id, quantity FROM character_inventory "
        "WHERE character_id=? AND item_id=? LIMIT 1",
        (character_id, item_id),
    ).fetchone()
    if not row or row["quantity"] < amount:
        return False
    if row["quantity"] == amount:
        c.execute("DELETE FROM character_inventory WHERE id=?", (row["id"],))
    else:
        c.execute(
            "UPDATE character_inventory SET quantity=quantity-? WHERE id=?",
            (amount, row["id"]),
        )
    c.commit()
    return True


def get_inventory(character_id):
    c = conn()
    rows = c.execute(
        "SELECT id, item_id, quantity, quality, durability, max_durability "
        "FROM character_inventory WHERE character_id=? ORDER BY item_id",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_item_count(character_id, item_id):
    c = conn()
    row = c.execute(
        "SELECT SUM(quantity) AS total FROM character_inventory "
        "WHERE character_id=? AND item_id=?",
        (character_id, item_id),
    ).fetchone()
    return row["total"] or 0


# ============================================================
# PHASE 4 — KILLS & COMBAT LOG
# ============================================================
def record_kill(character_id, monster_id):
    c = conn()
    c.execute(
        "INSERT INTO monster_kills(character_id, monster_id, count) VALUES (?,?,1) "
        "ON CONFLICT(character_id, monster_id) DO UPDATE SET count=count+1",
        (character_id, monster_id),
    )
    c.commit()


def get_kills(character_id):
    c = conn()
    rows = c.execute(
        "SELECT monster_id, count FROM monster_kills "
        "WHERE character_id=? ORDER BY count DESC",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def log_combat(character_id, monster_id, monster_lv, result, turns, exp_gain):
    c = conn()
    c.execute(
        "INSERT INTO combat_log"
        "(character_id, monster_id, monster_lv, result, turns, exp_gain, at_time) "
        "VALUES (?,?,?,?,?,?,?)",
        (character_id, monster_id, monster_lv, result, turns,
         exp_gain, int(_time.time())),
    )
    c.commit()


# ============================================================
# PHASE 5 — QUESTS
# ============================================================
def add_quest(character_id, quest_id, status="active"):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_quests"
            "(character_id, quest_id, status, started_at) VALUES (?,?,?,?)",
            (character_id, quest_id, status, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_quests(character_id, status=None):
    c = conn()
    if status:
        rows = c.execute(
            "SELECT quest_id, status, started_at, completed_at "
            "FROM character_quests WHERE character_id=? AND status=? "
            "ORDER BY started_at",
            (character_id, status),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT quest_id, status, started_at, completed_at "
            "FROM character_quests WHERE character_id=? ORDER BY started_at",
            (character_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_quest_status(character_id, quest_id):
    c = conn()
    row = c.execute(
        "SELECT status FROM character_quests WHERE character_id=? AND quest_id=?",
        (character_id, quest_id),
    ).fetchone()
    return row["status"] if row else None


def update_quest_status(character_id, quest_id, status):
    c = conn()
    completed = int(_time.time()) if status == "completed" else None
    c.execute(
        "UPDATE character_quests SET status=?, completed_at=? "
        "WHERE character_id=? AND quest_id=?",
        (status, completed, character_id, quest_id),
    )
    c.commit()


# ============================================================
# PHASE 5 — BOUNTIES
# ============================================================
def add_bounty(character_id, bounty_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_bounties"
            "(character_id, bounty_id, status, accepted_at) VALUES (?,?,?,?)",
            (character_id, bounty_id, "accepted", int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_bounties(character_id, status=None):
    c = conn()
    if status:
        rows = c.execute(
            "SELECT bounty_id, status, accepted_at, completed_at "
            "FROM character_bounties WHERE character_id=? AND status=? "
            "ORDER BY accepted_at",
            (character_id, status),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT bounty_id, status, accepted_at, completed_at "
            "FROM character_bounties WHERE character_id=? ORDER BY accepted_at",
            (character_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_bounty_status(character_id, bounty_id):
    c = conn()
    row = c.execute(
        "SELECT status FROM character_bounties WHERE character_id=? AND bounty_id=?",
        (character_id, bounty_id),
    ).fetchone()
    return row["status"] if row else None


def update_bounty_status(character_id, bounty_id, status):
    c = conn()
    completed = int(_time.time()) if status in ("completed", "failed") else None
    c.execute(
        "UPDATE character_bounties SET status=?, completed_at=? "
        "WHERE character_id=? AND bounty_id=?",
        (status, completed, character_id, bounty_id),
    )
    c.commit()


# ============================================================
# PHASE 5 — ACHIEVEMENTS
# ============================================================
def unlock_achievement(character_id, ach_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_achievements"
            "(character_id, achievement_id, unlocked_at) VALUES (?,?,?)",
            (character_id, ach_id, int(_time.time())),
        )
        c.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_achievements(character_id):
    c = conn()
    rows = c.execute(
        "SELECT achievement_id, unlocked_at FROM character_achievements "
        "WHERE character_id=? ORDER BY unlocked_at",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def has_achievement(character_id, ach_id):
    c = conn()
    row = c.execute(
        "SELECT 1 FROM character_achievements "
        "WHERE character_id=? AND achievement_id=?",
        (character_id, ach_id),
    ).fetchone()
    return bool(row)


# ============================================================
# PHASE 5 — REPUTATION
# ============================================================
def get_reputation(character_id, faction_type, faction_id):
    c = conn()
    row = c.execute(
        "SELECT value FROM character_reputation "
        "WHERE character_id=? AND faction_type=? AND faction_id=?",
        (character_id, faction_type, faction_id),
    ).fetchone()
    return row["value"] if row else 0


def add_reputation(character_id, faction_type, faction_id, amount):
    c = conn()
    current = get_reputation(character_id, faction_type, faction_id)
    new = current + amount
    c.execute(
        "INSERT INTO character_reputation"
        "(character_id, faction_type, faction_id, value) VALUES (?,?,?,?) "
        "ON CONFLICT(character_id, faction_type, faction_id) "
        "DO UPDATE SET value=excluded.value",
        (character_id, faction_type, faction_id, new),
    )
    c.commit()
    return new


def get_all_reputation(character_id):
    c = conn()
    rows = c.execute(
        "SELECT faction_type, faction_id, value FROM character_reputation "
        "WHERE character_id=? ORDER BY value DESC",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 5 — COUNTERS
# ============================================================
def inc_counter(character_id, key, amount=1):
    c = conn()
    c.execute(
        "INSERT INTO character_stats_counter(character_id, key, value) "
        "VALUES (?,?,?) "
        "ON CONFLICT(character_id, key) DO UPDATE SET value=value+excluded.value",
        (character_id, key, amount),
    )
    c.commit()


def get_counter(character_id, key):
    c = conn()
    row = c.execute(
        "SELECT value FROM character_stats_counter "
        "WHERE character_id=? AND key=?",
        (character_id, key),
    ).fetchone()
    return row["value"] if row else 0


def get_all_counters(character_id):
    c = conn()
    rows = c.execute(
        "SELECT key, value FROM character_stats_counter WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return {r["key"]: r["value"] for r in rows}


# ============================================================
# PHASE 5 — CITIES VISITED
# ============================================================
def mark_city_visited(character_id, city_id):
    c = conn()
    try:
        c.execute(
            "INSERT INTO character_cities_visited"
            "(character_id, city_id, first_visit) VALUES (?,?,?)",
            (character_id, city_id, int(_time.time())),
        )
        c.commit()
    except sqlite3.IntegrityError:
        pass


def get_visited_cities(character_id):
    c = conn()
    rows = c.execute(
        "SELECT city_id FROM character_cities_visited WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return [r["city_id"] for r in rows]


# ============================================================
# PHASE 6 — GUILD
# ============================================================
def get_player_guild_row(character_id):
    c = conn()
    row = c.execute(
        "SELECT guild_id, rank, joined_at, contribution "
        "FROM character_guild WHERE character_id=?",
        (character_id,),
    ).fetchone()
    return dict(row) if row else None


def set_player_guild(character_id, guild_id, rank="F"):
    c = conn()
    c.execute(
        "INSERT INTO character_guild"
        "(character_id, guild_id, rank, joined_at, contribution) "
        "VALUES (?,?,?,?,0) "
        "ON CONFLICT(character_id) DO UPDATE SET "
        "guild_id=excluded.guild_id, rank=excluded.rank, "
        "joined_at=excluded.joined_at",
        (character_id, guild_id, rank, int(_time.time())),
    )
    c.commit()


def leave_guild(character_id):
    c = conn()
    c.execute("DELETE FROM character_guild WHERE character_id=?", (character_id,))
    c.commit()


def add_contribution(character_id, amount):
    c = conn()
    c.execute(
        "UPDATE character_guild SET contribution=contribution+? "
        "WHERE character_id=?",
        (amount, character_id),
    )
    c.commit()


def update_guild_rank(character_id, rank):
    c = conn()
    c.execute(
        "UPDATE character_guild SET rank=? WHERE character_id=?",
        (rank, character_id),
    )
    c.commit()


def get_guild_members(guild_id):
    c = conn()
    rows = c.execute(
        "SELECT id, npc_id, rank, joined_at, power FROM guild_members "
        "WHERE guild_id=? ORDER BY joined_at DESC",
        (guild_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def add_guild_member(guild_id, npc_id, rank="E", power=0):
    c = conn()
    c.execute(
        "INSERT INTO guild_members(guild_id, npc_id, rank, joined_at, power) "
        "VALUES (?,?,?,?,?)",
        (guild_id, npc_id, rank, int(_time.time()), power),
    )
    c.commit()


def get_applications(character_id, status="pending"):
    c = conn()
    rows = c.execute(
        "SELECT id, npc_id, status, applied_at, reason FROM guild_applications "
        "WHERE character_id=? AND status=? ORDER BY applied_at DESC",
        (character_id, status),
    ).fetchall()
    return [dict(r) for r in rows]


def add_application(character_id, npc_id, reason):
    c = conn()
    c.execute(
        "INSERT INTO guild_applications"
        "(character_id, npc_id, status, applied_at, reason) VALUES (?,?,?,?,?)",
        (character_id, npc_id, "pending", int(_time.time()), reason),
    )
    c.commit()


def resolve_application(app_id, status):
    c = conn()
    c.execute(
        "UPDATE guild_applications SET status=? WHERE id=?",
        (status, app_id),
    )
    c.commit()


def count_applications(character_id, status="pending"):
    c = conn()
    row = c.execute(
        "SELECT COUNT(*) AS n FROM guild_applications "
        "WHERE character_id=? AND status=?",
        (character_id, status),
    ).fetchone()
    return row["n"] if row else 0


def log_guild_exam(character_id, guild_id, passed, score):
    c = conn()
    c.execute(
        "INSERT INTO guild_exam_attempts"
        "(character_id, guild_id, passed, score, attempted_at) VALUES (?,?,?,?,?)",
        (character_id, guild_id, 1 if passed else 0, score, int(_time.time())),
    )
    c.commit()


# ============================================================
# PHASE 6 — NPC RELATIONSHIP & MEMORY
# ============================================================
def get_relationship(character_id, npc_id):
    c = conn()
    row = c.execute(
        "SELECT relationship, met_at, last_interaction FROM npc_relationships "
        "WHERE character_id=? AND npc_id=?",
        (character_id, npc_id),
    ).fetchone()
    if not row:
        now = int(_time.time())
        c.execute(
            "INSERT INTO npc_relationships"
            "(character_id, npc_id, relationship, met_at) VALUES (?,?,0,?)",
            (character_id, npc_id, now),
        )
        c.commit()
        return {"relationship": 0, "met_at": now, "last_interaction": None}
    return dict(row)


def change_relationship(character_id, npc_id, amount):
    get_relationship(character_id, npc_id)
    c = conn()
    c.execute(
        "UPDATE npc_relationships "
        "SET relationship=relationship+?, last_interaction=? "
        "WHERE character_id=? AND npc_id=?",
        (amount, int(_time.time()), character_id, npc_id),
    )
    c.commit()


def remember(character_id, npc_id, event):
    c = conn()
    c.execute(
        "INSERT INTO npc_memory(character_id, npc_id, event, at_time) "
        "VALUES (?,?,?,?)",
        (character_id, npc_id, event, int(_time.time())),
    )
    c.commit()


def get_memory(character_id, npc_id, limit=5):
    c = conn()
    rows = c.execute(
        "SELECT event, at_time FROM npc_memory "
        "WHERE character_id=? AND npc_id=? ORDER BY id DESC LIMIT ?",
        (character_id, npc_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 7 — EQUIPMENT
# ============================================================
def equip_get(character_id, slot):
    c = conn()
    row = c.execute(
        "SELECT slot, item_id, quality, durability, max_durability, upgrade_level "
        "FROM character_equipment WHERE character_id=? AND slot=?",
        (character_id, slot),
    ).fetchone()
    return dict(row) if row else None


def equip_set(character_id, slot, item_id, quality="normal",
              durability=100, max_durability=100, upgrade_level=0):
    c = conn()
    c.execute(
        "INSERT INTO character_equipment"
        "(character_id, slot, item_id, quality, durability, max_durability, upgrade_level) "
        "VALUES (?,?,?,?,?,?,?) "
        "ON CONFLICT(character_id, slot) DO UPDATE SET "
        "item_id=excluded.item_id, quality=excluded.quality, "
        "durability=excluded.durability, max_durability=excluded.max_durability, "
        "upgrade_level=excluded.upgrade_level",
        (character_id, slot, item_id, quality, durability,
         max_durability, upgrade_level),
    )
    c.commit()


def equip_clear(character_id, slot):
    c = conn()
    c.execute(
        "DELETE FROM character_equipment WHERE character_id=? AND slot=?",
        (character_id, slot),
    )
    c.commit()


def equip_all(character_id):
    c = conn()
    rows = c.execute(
        "SELECT slot, item_id, quality, durability, max_durability, upgrade_level "
        "FROM character_equipment WHERE character_id=?",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def equip_update_durability(character_id, slot, durability):
    c = conn()
    c.execute(
        "UPDATE character_equipment SET durability=? "
        "WHERE character_id=? AND slot=?",
        (durability, character_id, slot),
    )
    c.commit()


def equip_update_upgrade(character_id, slot, upgrade_level):
    c = conn()
    c.execute(
        "UPDATE character_equipment SET upgrade_level=? "
        "WHERE character_id=? AND slot=?",
        (upgrade_level, character_id, slot),
    )
    c.commit()


# ============================================================
# PHASE 8 — FARMING
# ============================================================
def ensure_farming_plots(character_id, count=6):
    c = conn()
    for i in range(count):
        c.execute(
            "INSERT OR IGNORE INTO farming_plots"
            "(character_id, plot_index, state) VALUES (?,?, 'empty')",
            (character_id, i),
        )
    c.commit()


def get_farming_plots(character_id):
    c = conn()
    rows = c.execute(
        "SELECT plot_index, state, seed_id, crop_id, planted_at, water_count "
        "FROM farming_plots WHERE character_id=? ORDER BY plot_index",
        (character_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def set_farming_plot(character_id, plot_index, **fields):
    if not fields:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [character_id, plot_index]
    c = conn()
    c.execute(
        f"UPDATE farming_plots SET {cols} WHERE character_id=? AND plot_index=?",
        vals,
    )
    c.commit()


def reset_farming_plot(character_id, plot_index):
    c = conn()
    c.execute(
        "UPDATE farming_plots SET state='empty', seed_id=NULL, crop_id=NULL, "
        "planted_at=NULL, water_count=0 "
        "WHERE character_id=? AND plot_index=?",
        (character_id, plot_index),
    )
    c.commit()


# ============================================================
# PHASE 9 — DUNGEON & EVENTS
# ============================================================
def log_event(character_id, event_id, region_id=None):
    c = conn()
    c.execute(
        "INSERT INTO world_events_log(character_id, event_id, region_id, at_time) "
        "VALUES (?,?,?,?)",
        (character_id, event_id, region_id, int(_time.time())),
    )
    c.commit()


def get_event_log(character_id, limit=20):
    c = conn()
    rows = c.execute(
        "SELECT event_id, region_id, at_time FROM world_events_log "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 10 — STORY LOG
# ============================================================
def log_story(character_id, event_type, event_id):
    c = conn()
    c.execute(
        "INSERT INTO story_log(character_id, event_type, event_id, at_time) "
        "VALUES (?,?,?,?)",
        (character_id, event_type, event_id, int(_time.time())),
    )
    c.commit()


def get_story_log(character_id, limit=20):
    c = conn()
    rows = c.execute(
        "SELECT event_type, event_id, at_time FROM story_log "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 11 — RACE & CIT
# ============================================================
def log_race_change(character_id, race_id):
    c = conn()
    c.execute(
        "INSERT INTO race_history(character_id, race_id, changed_at) "
        "VALUES (?,?,?)",
        (character_id, race_id, int(_time.time())),
    )
    c.commit()


def get_race_history(character_id, limit=10):
    c = conn()
    rows = c.execute(
        "SELECT race_id, changed_at FROM race_history "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def log_cit(character_id, action):
    c = conn()
    c.execute(
        "INSERT INTO cit_log(character_id, action, at_time) VALUES (?,?,?)",
        (character_id, action, int(_time.time())),
    )
    c.commit()


def get_cit_log(character_id, limit=10):
    c = conn()
    rows = c.execute(
        "SELECT action, at_time FROM cit_log "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# PHASE 12 — NEW GAME+
# ============================================================
def log_ng_plus(character_id, ng_level):
    c = conn()
    c.execute(
        "INSERT INTO ng_plus_log(character_id, ng_level, at_time) VALUES (?,?,?)",
        (character_id, ng_level, int(_time.time())),
    )
    c.commit()


def get_ng_plus_log(character_id, limit=5):
    c = conn()
    rows = c.execute(
        "SELECT ng_level, at_time FROM ng_plus_log "
        "WHERE character_id=? ORDER BY id DESC LIMIT ?",
        (character_id, limit),
    ).fetchall()
    return [dict(r) for r in rows]
