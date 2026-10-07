"""New Game+ — reset progress dengan bonus permanen."""
import database as db
import time


# Bonus yang dipertahankan saat NG+
KEEP = [
    "achievements",         # achievement tetap
    "story_progress",       # chapter tetap
    "lore_unlocked",        # lore tetap
    "cit_mode_unlocked",    # CIT tetap
    "ending_id",            # ending tetap
    "race_unlocked_count",  # jumlah race unlock
]

# Bonus NG+ per siklus
NG_PLUS_BONUS = {
    "exp_bonus_pct": 10,    # +10% EXP per NG+
    "gold_bonus_pct": 5,    # +5% gold reward
    "start_attr_points": 5, # +5 attr point di setiap NG+
    "start_silver": 500,    # +500 silver awal
    "start_gold": 5,        # +5 gold awal
}


def get_ng_plus_level(character_id):
    val = db.get_world_state(character_id, "ng_plus_level", "0")
    try:
        return int(val)
    except Exception:
        return 0


def can_start_ng_plus(character_id):
    """Syarat NG+: sudah selesai story atau punya ending."""
    ending = db.get_world_state(character_id, "ending_id")
    from story import progress_percent
    pct = progress_percent(character_id)
    if ending or pct >= 100:
        return True, None
    return False, "Selesaikan main story terlebih dahulu."


def apply_ng_plus(character_id):
    """Reset karakter tapi pertahankan achievement, story, dll."""
    ok, reason = can_start_ng_plus(character_id)
    if not ok:
        return False, reason

    char = db.get_character(character_id)
    if not char:
        return False, "Karakter tidak ditemukan."

    ng_level = get_ng_plus_level(character_id) + 1

    # Snapshot data yang dipertahankan
    stats = db.get_stats(character_id)

    # Reset progress — hapus data non-keep
    c = db.conn()
    tables_reset = [
        "character_roles",
        "character_mastery",
        "character_skills",
        "character_mentors",
        "character_equipment",
        "character_inventory",
        "character_quests",
        "character_bounties",
        "character_reputation",
        "monster_kills",
        "combat_log",
        "active_dungeon",
        "world_events_log",
        "travel_log",
        "farming_plots",
        "npc_relationships",
        "npc_memory",
        "race_history",
    ]
    for t in tables_reset:
        try:
            c.execute(f"DELETE FROM {t} WHERE character_id=?", (character_id,))
        except Exception:
            pass
    c.commit()

    # Reset counters (kecuali NG+ level)
    c.execute("DELETE FROM character_stats_counter WHERE character_id=?", (character_id,))
    c.commit()

    # Reset stats ke default + bonus NG+
    from config import DEFAULT_STATS
    base_stats = dict(DEFAULT_STATS)
    new_attr_points = 15 + ng_level * NG_PLUS_BONUS["start_attr_points"]
    db.update_stats(character_id, **base_stats)

    # Reset character
    db.update_character(
        character_id,
        level=15,
        exp=0,
        hp_current=100,
        mp_current=50,
        stamina_current=80,
        attr_points=new_attr_points,
        silver=100 + ng_level * NG_PLUS_BONUS["start_silver"],
        gold=ng_level * NG_PLUS_BONUS["start_gold"],
        location="aurelia",
        role="fighter",
    )

    # Simpan NG+ level
    db.set_world_state(character_id, "ng_plus_level", str(ng_level))
    db.set_world_state(character_id, "ng_plus_at", str(int(time.time())))

    # Re-grant starting role
    db.unlock_role(character_id, "fighter")
    db.set_active_role(character_id, "fighter")
    db.get_mastery(character_id, "combat_arts")

    # Re-init farming plots
    db.ensure_farming_plots(character_id, 6)

    return True, ng_level


def ng_bonus_mult(character_id):
    """Return multiplier dari NG+ untuk EXP & reward."""
    ng = get_ng_plus_level(character_id)
    exp_m = 1 + (ng * NG_PLUS_BONUS["exp_bonus_pct"] / 100.0)
    gold_m = 1 + (ng * NG_PLUS_BONUS["gold_bonus_pct"] / 100.0)
    return {"exp": exp_m, "gold": gold_m}


def ng_bonus_label(character_id):
    ng = get_ng_plus_level(character_id)
    if ng <= 0:
        return ""
    b = ng_bonus_mult(character_id)
    return f"NG+{ng}  (EXP +{int((b['exp']-1)*100)}%, Gold +{int((b['gold']-1)*100)}%)"
