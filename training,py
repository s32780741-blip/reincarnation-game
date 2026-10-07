"""Interactive training — grants mastery EXP, not free character EXP."""
import random, time
from ui import C, color, clear, box, prompt, pause, progress_bar
from i18n import t
import database as db
import settings

def _lang():
    return settings.get("language", "id")

DRILLS = {
    "combat_arts": [
        {"id": "strike",   "name": "Strike Practice",   "stat": "strength",  "base_exp": 12},
        {"id": "endure",   "name": "Endurance Drill",   "stat": "endurance", "base_exp": 10},
        {"id": "dodge",    "name": "Dodge Training",    "stat": "agility",   "base_exp": 11},
    ],
    "swordsmanship": [
        {"id": "sword_form",   "name": "Sword Form",    "stat": "dexterity", "base_exp": 14},
        {"id": "sword_power",  "name": "Power Slash",   "stat": "strength",  "base_exp": 15},
        {"id": "sword_speed",  "name": "Quick Draw",    "stat": "speed",     "base_exp": 13},
    ],
    "magic_knowledge": [
        {"id": "mana_flow",   "name": "Mana Flow",      "stat": "mana",        "base_exp": 14},
        {"id": "focus",       "name": "Focus Meditation","stat": "intelligence","base_exp": 15},
        {"id": "cast",        "name": "Cast Practice",  "stat": "dexterity",   "base_exp": 12},
    ],
    "archery": [
        {"id": "aim",      "name": "Aim Practice",   "stat": "accuracy",   "base_exp": 13},
        {"id": "draw",     "name": "Bow Draw",       "stat": "dexterity",  "base_exp": 12},
        {"id": "track",    "name": "Tracking Drill", "stat": "perception", "base_exp": 14},
    ],
    "assassination": [
        {"id": "sneak",    "name": "Stealth Drill",  "stat": "stealth",    "base_exp": 14},
        {"id": "vital",    "name": "Vital Strike",   "stat": "critical",   "base_exp": 15},
        {"id": "shadow",   "name": "Shadow Step",    "stat": "agility",    "base_exp": 13},
    ],
    "holy_arts": [
        {"id": "prayer",   "name": "Prayer",         "stat": "mana",       "base_exp": 12},
        {"id": "channel",  "name": "Channel Light",  "stat": "intelligence","base_exp": 14},
        {"id": "shield",   "name": "Holy Shield",    "stat": "defense",    "base_exp": 13},
    ],
    "necromancy": [
        {"id": "bone",     "name": "Bone Reading",   "stat": "perception", "base_exp": 13},
        {"id": "bind",     "name": "Soul Binding",   "stat": "intelligence","base_exp": 15},
        {"id": "dark",     "name": "Dark Channel",   "stat": "mana",       "base_exp": 14},
    ],
    "blacksmithing": [
        {"id": "hammer",   "name": "Hammer Drill",   "stat": "strength",   "base_exp": 13},
        {"id": "forge",    "name": "Forge Practice", "stat": "crafting",   "base_exp": 16},
        {"id": "temper",   "name": "Tempering",      "stat": "endurance",  "base_exp": 12},
    ],
}

def training_menu(character_id):
    lang = _lang()
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    if not char or not stats:
        return
    from roles import mastery_tree
    tree_id = mastery_tree(char["role"])

    while True:
        clear()
        from mastery import mastery_display, get_tree
        tree = get_tree(tree_id)
        tree_name = tree["name"] if tree else tree_id
        drills = DRILLS.get(tree_id, DRILLS["combat_arts"])

        lines = [color(f"Training Grounds — {tree_name}", C.BOLD + C.CYAN), ""]
        for i, d in enumerate(drills, 1):
            lines.append(f" {i}. {d['name']}  (pakai {d['stat']})")
        lines.append(" 4. Sparring (risiko tinggi, reward besar)")
        lines.append(" 0. Kembali")
        print(box("TRAINING", lines))
        ch = prompt("> ")

        if ch == "0":
            return
        if ch in ("1", "2", "3"):
            drill = drills[int(ch) - 1]
            _do_drill(character_id, tree_id, drill, stats)
        elif ch == "4":
            _do_sparring(character_id, tree_id, stats)
        else:
            print(color(" Input tidak valid.", C.RED)); pause()

def _do_drill(character_id, tree_id, drill, stats):
    lang = _lang()
    clear()
    print(box("TRAINING", [
        f"Kamu berlatih: {drill['name']}",
        f"Stat terkait: {drill['stat']}",
        "",
        "Berapa lama? (1-5 sesi)",
    ]))
    r = prompt("Sesi (default 1): ")
    try:
        sesi = max(1, min(5, int(r)))
    except Exception:
        sesi = 1

    total_exp = 0
    total_stat_used = 0
    for i in range(sesi):
        stat_val = stats.get(drill["stat"], 5)
        roll = random.randint(1, 20) + stat_val
        if roll >= 25:
            gain = drill["base_exp"] * 2
            grade = "EXCELLENT"
            col = C.GREEN
        elif roll >= 18:
            gain = int(drill["base_exp"] * 1.4)
            grade = "GOOD"
            col = C.CYAN
        elif roll >= 12:
            gain = drill["base_exp"]
            grade = "OK"
            col = C.YELLOW
        else:
            gain = max(1, drill["base_exp"] // 2)
            grade = "POOR"
            col = C.RED
        total_exp += gain
        total_stat_used += stat_val
        print(f"  Sesi {i+1}: roll {roll} → {color(grade, col)} (+{gain} mastery EXP)")

    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, tree_id, total_exp)
    new_lv, events = check_levelup(character_id, tree_id, new_exp)

    print()
    print(color(f" +{total_exp} mastery EXP untuk {tree_id}", C.GREEN))
    if events:
        for lv in events:
            from mastery import get_level_info
            info = get_level_info(tree_id, lv)
            nm = info["name"] if info else "?"
            print(color(f" ★ MASTERY UP! Level {lv} — {nm}", C.MAGENTA + C.BOLD))
    pause()

def _do_sparring(character_id, tree_id, stats):
    lang = _lang()
    clear()
    char = db.get_character(character_id)
    print(box("SPARRING", [
        "Kamu menghadapi partner sparring.",
        "Risiko: HP bisa turun.",
        "Reward: mastery EXP besar.",
        "",
        "1. Mulai",
        "2. Batal",
    ]))
    if prompt("> ") != "1":
        return

    # Simulasi sparring: 3 ronde
    my_hp = char["hp_current"]
    partner_hp = 100 + char["level"] * 5
    total_exp = 0
    round_no = 0
    while my_hp > 0 and partner_hp > 0 and round_no < 20:
        round_no += 1
        # Player attack
        patk = stats.get("strength", 5) + random.randint(1, 10)
        partner_def = 5 + char["level"] // 2
        dmg = max(1, patk - partner_def // 2)
        partner_hp -= dmg
        # Partner attack
        en_atk = 8 + char["level"] + random.randint(1, 8)
        my_def = stats.get("defense", 5) // 2
        edmg = max(1, en_atk - my_def)
        my_hp -= edmg
        total_exp += 8
        print(f" Round {round_no}: Kamu -{dmg} HP musuh | Musuh -{edmg} HP kamu")
        time.sleep(0.15)

    # Apply HP loss
    my_hp = max(1, my_hp)  # jangan mati di sparring
    db.update_character(character_id, hp_current=my_hp)

    won = partner_hp <= 0
    bonus = 40 if won else 15
    total_exp += bonus

    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, tree_id, total_exp)
    new_lv, events = check_levelup(character_id, tree_id, new_exp)

    print()
    if won:
        print(color(f" 🏆 KAMU MENANG! +{total_exp} mastery EXP", C.GREEN + C.BOLD))
    else:
        print(color(f" 💢 Kamu kalah. +{total_exp} mastery EXP", C.YELLOW))
    for lv in events:
        from mastery import get_level_info
        info = get_level_info(tree_id, lv)
        print(color(f" ★ MASTERY UP! Lv {lv} — {info['name'] if info else '?'}", C.MAGENTA + C.BOLD))
    pause()
