"""CIT MODE — secret endgame unlock."""
import json, os, time, random
from config import DATA_DIR
import database as db

_C = None


def load_cit():
    global _C
    if _C is not None:
        return _C
    path = os.path.join(DATA_DIR, "cit.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _C = json.load(f)
    except Exception:
        _C = {"config": {}, "keeper_dialog": []}
    return _C


def config():
    return load_cit().get("config", {})


def is_cit_unlocked(character_id):
    return db.get_world_state(character_id, "cit_mode_unlocked", "0") == "1"


def is_cit_active(character_id):
    char = db.get_character(character_id)
    return bool(char.get("cit_mode")) if char else False


def attempt_unlock(character_id):
    """Coba unlock CIT MODE dengan syarat tersembunyi."""
    from story import progress_percent
    char = db.get_character(character_id)

    # Syarat: level 100+, story 90%+, sudah pernah dapat 3 achievement
    achievements = len(db.get_achievements(character_id))
    story_pct = progress_percent(character_id)
    requirements = {
        "level": char["level"] >= 100,
        "story": story_pct >= 90,
        "achievements": achievements >= 3,
    }
    return all(requirements.values()), requirements


def show_keeper_dialog(character_id):
    """Tampilkan dialog The Keeper."""
    from ui import C, color, clear, box, prompt, pause
    from cutscene import _type
    import time as _t

    clear()
    print(box("???", [
        color(" Sebuah suara memanggilmu dari kegelapan...", C.MAGENTA),
    ]))
    pause()

    for line in load_cit().get("keeper_dialog", []):
        clear()
        print()
        print(color("  KEEPER OF CYCLES:", C.MAGENTA + C.BOLD))
        _type(f"  \"{line}\"")
        _t.sleep(0.3)
        pause()

    clear()
    print(box("CHOOSE", [
        " 1. Ya, aku siap.",
        " 0. Tidak, aku belum siap.",
    ]))
    from ui import prompt
    if prompt("> ") != "1":
        clear()
        print(box("CIT MODE", [" Kau mundur. The Keeper menghilang...", "",
                                color(" Mungkin lain kali.", C.GRAY)]))
        pause()
        return False

    # Unlock!
    _activate_cit(character_id)
    return True


def _activate_cit(character_id):
    from ui import C, color, clear, box, pause
    db.set_world_state(character_id, "cit_mode_unlocked", "1")
    db.set_world_state(character_id, "cit_unlocked_at", str(int(time.time())))
    db.update_character(character_id, cit_mode=1)
    db.inc_counter(character_id, "cit_unlocked", 1)

    clear()
    print(box("★ CIT MODE ACTIVATED ★", [
        color(" KAU TELAH MENEMBUS BATAS.", C.YELLOW + C.BOLD),
        "",
        " Level cap → 1111",
        " Beast & Demon race → TERSEDIA",
        " Semua role → BISA DIPELAJARI",
        " Teleport → GRATIS",
        " Reward → 2x",
        "",
        color(" Dunia baru terbuka di hadapanmu.", C.CYAN),
    ]))
    pause()


def try_secret_command(character_id, cmd):
    """Handle command rahasia. Return True kalau cmd valid."""
    cmd = cmd.strip().lower()
    if cmd == "/cit":
        unlocked = is_cit_unlocked(character_id)
        if unlocked:
            from ui import C, color, box, pause
            print(box("CIT MODE", [
                color(" ✓ CIT MODE sudah aktif.", C.GREEN),
            ]))
            pause()
            return True
        ok, reqs = attempt_unlock(character_id)
        from ui import C, color, box, pause
        if not ok:
            lines = [
                color(" ✗ The Keeper belum menjawab panggilanmu.", C.RED),
                "",
                " SYARAT:",
            ]
            for k, v in reqs.items():
                mark = "✓" if v else "✗"
                col = C.GREEN if v else C.RED
                lines.append(color(f"  {mark} {k}", col))
            print(box("CIT MODE", lines))
            pause()
            return True
        # Unlock dialog
        show_keeper_dialog(character_id)
        return True

    if cmd == "/thekeeper":
        if is_cit_unlocked(character_id):
            show_keeper_dialog(character_id)
        else:
            from ui import C, color, box, pause
            print(box("KEEPER", [
                color(" Tidak ada yang menjawab.", C.GRAY),
                "",
                " Suara-suara di kegelapan tetap diam...",
            ]))
            pause()
        return True

    if cmd == "/unlockall":
        if is_cit_active(character_id):
            from ui import C, color, box, pause
            # Unlock semua race
            db.inc_counter(character_id, "cit_races_unlocked", 30)
            print(box("DEBUG", [
                color(" ✓ Semua race terbuka.", C.GREEN),
            ]))
            pause()
        return True

    return False


def effective_max_level(character_id):
    from config import MAX_LEVEL_NORMAL, MAX_LEVEL_CIT
    if is_cit_active(character_id):
        return MAX_LEVEL_CIT
    return MAX_LEVEL_NORMAL


def effective_exp_mult(character_id):
    if is_cit_active(character_id):
        return config().get("exp_multiplier", 1.5)
    return 1.0


def effective_reward_mult(character_id):
    if is_cit_active(character_id):
        return config().get("rewards_multiplier", 2.0)
    return 1.0


def check_level_cap(character_id, new_level):
    max_lv = effective_max_level(character_id)
    return min(new_level, max_lv)
