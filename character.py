"""Character creation + status display."""
from ui import C, color, clear, box, prompt, pause, progress_bar
from i18n import t
import database as db
import settings
from config import (
    STARTING_LEVEL, STARTING_ATTRIBUTE_POINTS, ATTRIBUTE_POINTS_PER_LEVEL,
    DEFAULT_STATS, STAT_KEYS, MAX_LEVEL_NORMAL, MAX_LEVEL_CIT,
)
from rank import rank_text, get_rank, exp_to_next
from roles import available_for_gender, get_role, mastery_tree

def _lang():
    return settings.get("language", "id")

# ---------- character creation ----------
def create_character_flow(account_id):
    lang = _lang()
    clear()
    print(box(t("menu.create_character", lang), [
        "Dunia baru menantimu...",
        "",
        "Pilih identitas untuk kehidupan kedua.",
    ]))

    # Nama
    while True:
        name = prompt(" Nama: ")
        if 2 <= len(name) <= 20:
            break
        print(color(" Nama harus 2-20 karakter.", C.RED))

    # Gender
    while True:
        clear()
        print(box("GENDER", [
            " 1. Male",
            " 2. Female",
        ]))
        g = prompt("> ")
        if g == "1":
            gender = "male"
            break
        elif g == "2":
            gender = "female"
            break
        print(color(" Pilih 1 atau 2.", C.RED))

    # Starting role
    role = _pick_starting_role(gender)

    # Stat alokasi
    stats = dict(DEFAULT_STATS)
    points = STARTING_ATTRIBUTE_POINTS

    clear()
    print(box("STAT DISTRIBUTION", [
        f"Kamu punya {points} poin untuk dibagikan.",
        "Ketik nama stat & jumlah (contoh: strength 3)",
        "Ketik 'done' jika selesai.",
        "",
        "Stats tersedia:",
        ", ".join(STAT_KEYS),
    ]))
    while points > 0:
        print()
        print(color(f" Poin tersisa: {points}", C.YELLOW + C.BOLD))
        line = prompt(" invest> ")
        if line.lower() in ("done", "selesai", ""):
            if points > 0:
                print(color(" Masih ada poin tersisa. Yakin selesai? (y/n)", C.YELLOW))
                if prompt("> ").lower() == "y":
                    break
                continue
            break
        parts = line.split()
        if len(parts) != 2:
            print(color(" Format: <stat> <jumlah>", C.RED)); continue
        k, v = parts[0].lower(), parts[1]
        try:
            v = int(v)
        except ValueError:
            print(color(" Jumlah harus angka.", C.RED)); continue
        if k not in STAT_KEYS:
            print(color(f" Stat '{k}' tidak dikenal.", C.RED)); continue
        if v < 1 or v > points:
            print(color(f" Jumlah harus 1-{points}.", C.RED)); continue
        stats[k] += v
        points -= v

    # Simpan ke DB
    cid = db.create_character(account_id, name, gender, role=role)
    db.update_stats(cid, **stats)
    _grant_starting_role(cid, role)

    # Currency awal
    db.update_character(cid, silver=100, gold=1, zambrut=0)

    clear()
    print(box("CHARACTER CREATED", [
        f" Nama   : {name}",
        f" Gender : {gender.capitalize()}",
        f" Role   : {get_role(role)['name'] if get_role(role) else role}",
        f" Level  : {STARTING_LEVEL}",
        "",
        color("Kehidupan kedua dimulai...", C.CYAN),
    ]))
    pause()
    return cid

def _pick_starting_role(gender):
    roles = available_for_gender(gender)
    clear()
    lines = ["Pilih role awal:"]
    for i, r in enumerate(roles, 1):
        lines.append(f" {i}. {r['name']}")
    print(box("STARTING ROLE", lines))
    while True:
        c = prompt("> ")
        try:
            idx = int(c) - 1
            if 0 <= idx < len(roles):
                return roles[idx]["id"]
        except ValueError:
            pass
        print(color(" Pilih nomor yang valid.", C.RED))

def _grant_starting_role(character_id, role_id):
    db.unlock_role(character_id, role_id)
    db.set_active_role(character_id, role_id)
    tree = mastery_tree(role_id)
    db.get_mastery(character_id, tree)

# ---------- status display ----------
def show_status(character_id):
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    if not char or not stats:
        return
    clear()

    from mastery import mastery_display, total_bonus
    from roles import get_role
    active = get_role(char["role"])

    max_hp = 100 + stats["hp"] * 10 + char["level"] * 5
    max_mp = 50 + stats["mana"] * 8 + char["level"] * 2
    max_st = 80 + stats["stamina"] * 6 + char["level"] * 2

    hp_pct = int(char["hp_current"] / max_hp * 100) if max_hp else 0
    mp_pct = int(char["mp_current"] / max_mp * 100) if max_mp else 0
    st_pct = int(char["stamina_current"] / max_st * 100) if max_st else 0

    bonus = total_bonus(character_id)

    tree = mastery_tree(char["role"])
    m_line = mastery_display(character_id, tree)

    lines = [
        f" Nama   : {color(char['name'], C.CYAN + C.BOLD)}",
        f" Gender : {char['gender'].capitalize()}",
        f" Race   : {char['race']}",
        f" Level  : {char['level']}",
        f" Rank   : {rank_text(char['level'], bool(char.get('cit_mode')))}",
        f" Role   : {active['name'] if active else char['role']}",
        f" Mastery: {m_line}",
        f" Lokasi : {char['location']}",
        "",
        f" HP   {progress_bar(hp_pct, 18)} {char['hp_current']}/{max_hp}",
        f" MP   {progress_bar(mp_pct, 18)} {char['mp_current']}/{max_mp}",
        f" ST   {progress_bar(st_pct, 18)} {char['stamina_current']}/{max_st}",
        "",
        color("ATTRIBUTES", C.YELLOW),
    ]
    # Susun 2 kolom
    keys = STAT_KEYS
    half = (len(keys) + 1) // 2
    for i in range(half):
        k1 = keys[i]
        left = f"  {k1:<13}: {stats[k1]:>3}"
        if i + half < len(keys):
            k2 = keys[i + half]
            right = f"   {k2:<13}: {stats[k2]:>3}"
        else:
            right = ""
        lines.append(left + right)

    lines.append("")
    lines.append(f" Currency: {char['silver']}s  {char['gold']}g  {char['zambrut']}z")
    lines.append(f" Attr Pts: {char['attr_points']}")
    if bonus:
        lines.append("")
        lines.append(color("Mastery Bonuses:", C.MAGENTA))
        for k, v in bonus.items():
            if isinstance(v, (int, float)):
                lines.append(f"   {k}: +{v}")

    print(box("CHARACTER STATUS", lines))
    pause()

def max_hp(stats, level):
    return 100 + stats["hp"] * 10 + level * 5

def max_mp(stats, level):
    return 50 + stats["mana"] * 8 + level * 2

def max_stamina(stats, level):
    return 80 + stats["stamina"] * 6 + level * 2

# ---------- level up ----------
def grant_exp(character_id, amount):
    """Tambah EXP, cek level up, kembalikan list level up events."""
    char = db.get_character(character_id)
    if not char:
        return []
    max_lv = MAX_LEVEL_CIT if char.get("cit_mode") else MAX_LEVEL_NORMAL
    events = []
    new_exp = char["exp"] + amount
    level = char["level"]

    while level < max_lv:
        need = exp_to_next(level)
        if new_exp >= need:
            new_exp -= need
            level += 1
            events.append(level)
        else:
            break

    if events:
        points = char["attr_points"] + ATTRIBUTE_POINTS_PER_LEVEL * len(events)
        db.update_character(character_id, exp=new_exp, level=level, attr_points=points)
    else:
        db.update_character(character_id, exp=new_exp)

    return events

def spend_attr_points(character_id):
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    if not char or not stats:
        return
    while char["attr_points"] > 0:
        clear()
        print(box("ALOKASI ATTRIBUTE POINT", [
            f" Poin tersisa: {char['attr_points']}",
            "",
            " Ketik: <stat> <jumlah>  (contoh: strength 2)",
            " Ketik 'done' untuk selesai.",
            "",
            ", ".join(STAT_KEYS),
        ]))
        line = prompt(" invest> ")
        if line.lower() in ("done", "selesai", ""):
            return
        parts = line.split()
        if len(parts) != 2:
            print(color(" Format salah.", C.RED)); pause(); continue
        k, v = parts[0].lower(), parts[1]
        try:
            v = int(v)
        except ValueError:
            print(color(" Jumlah harus angka.", C.RED)); pause(); continue
        if k not in STAT_KEYS:
            print(color(" Stat tidak dikenal.", C.RED)); pause(); continue
        if v < 1 or v > char["attr_points"]:
            print(color(f" Jumlah harus 1-{char['attr_points']}.", C.RED)); pause(); continue
        db.update_stats(character_id, **{k: stats[k] + v})
        db.update_character(character_id, attr_points=char["attr_points"] - v)
        char = db.get_character(character_id)
        stats = db.get_stats(character_id)

