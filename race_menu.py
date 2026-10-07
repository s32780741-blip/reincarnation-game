"""Race menu — view, switch (requires CIT for non-Human)."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from races import (
    load_races, get_race, race_name, race_color,
    available_races, bonus_for_race, passive_for_race, races_by_group,
)
from cit_mode import is_cit_unlocked, is_cit_active


def race_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        cit = is_cit_active(character_id)
        current = get_race(char["race"])

        clear()
        lines = [
            f" Race saat ini : {race_name(char['race'])}",
            f" Grup          : {current.get('group','?') if current else '?'}",
            f" CIT MODE      : {'✓ AKTIF' if cit else '✗ Tidak aktif'}",
            "",
            " 1. Lihat semua race",
            " 2. Ganti race" + ("" if cit else color("  (butuh CIT)", C.YELLOW)),
            " 3. Info race saat ini",
            " 0. Kembali",
        ]
        print(box("RACE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _list_all(character_id)
        elif ch == "2":
            if not cit:
                clear()
                print(box("RACE", [
                    color(" Ganti race butuh CIT MODE.", C.RED),
                    "",
                    " Hanya Human yang bisa dimainkan tanpa CIT.",
                ]))
                pause()
                continue
            _switch_race(character_id)
        elif ch == "3":
            _race_detail(char["race"], character_id)


def _list_all(character_id):
    while True:
        clear()
        lines = []
        listing = available_races(character_id)
        for i, (r, status) in enumerate(listing, 1):
            col = race_color(r["id"]) if status == "unlocked" else C.GRAY
            mark = color("✓", C.GREEN) if status == "unlocked" else color("🔒", C.YELLOW)
            lines.append(f" {mark} [{i:2d}] {color(r['name'], col):<20} [{r['group']}] T{r['tier']}")
        lines.append("")
        lines.append(color("✓ playable  🔒 terkunci", C.DIM))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("ALL RACES", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            r, status = listing[int(ch) - 1]
            _race_detail(r["id"], character_id)
        except Exception:
            pass


def _race_detail(race_id, character_id):
    r = get_race(race_id)
    if not r:
        return
    col = race_color(race_id)
    lines = [
        color(r["name"], col + C.BOLD),
        f" Group   : {r['group']}",
        f" Tier    : {r['tier']}",
        f" Unlock  : {r.get('unlock','starter')}",
        "",
        color(r["desc"], C.WHITE),
        "",
        color("BASE BONUS:", C.YELLOW),
    ]
    for k, v in r.get("base_bonus", {}).items():
        sign = "+" if v > 0 else ""
        lines.append(f"  {k.replace('_',' ').title():<15}: {sign}{v}")
    lines.append("")
    lines.append(color("PASSIVE:", C.YELLOW))
    lines.append(f"  {r.get('passive','-')}")

    # Ownership check
    char = db.get_character(character_id)
    if char and char["race"] == race_id:
        lines.append("")
        lines.append(color(" ✓ Race saat ini.", C.GREEN))

    lines.append("")
    lines.append(" 0. Kembali")
    print(box("RACE DETAIL", lines))
    prompt("> ")


def _switch_race(character_id):
    listing = available_races(character_id)
    unlocked = [(r, s) for r, s in listing if s == "unlocked"]
    if not unlocked:
        return
    clear()
    lines = []
    for i, (r, s) in enumerate(unlocked, 1):
        col = race_color(r["id"])
        lines.append(f" [{i:2d}] {color(r['name'], col)}")
    lines.append("")
    lines.append(" 0. Batal")
    print(box("SWITCH RACE", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        r = unlocked[int(ch) - 1][0]
    except Exception:
        return
    char = db.get_character(character_id)
    if char["race"] == r["id"]:
        print(color(" Sudah memakai race ini.", C.YELLOW))
        pause()
        return
    # Confirm
    clear()
    print(box("CONFIRM", [
        f" Ganti race ke {r['name']}?",
        "",
        color(" Base stat akan disesuaikan.", C.YELLOW),
        "",
        " 1. Ya",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return

    # Apply race
    old_race = get_race(char["race"])
    old_bonus = old_race.get("base_bonus", {}) if old_race else {}
    new_bonus = r.get("base_bonus", {})

    stats = db.get_stats(character_id)
    if stats:
        # Hapus bonus lama, tambah bonus baru
        updates = {}
        keys = set(list(old_bonus.keys()) + list(new_bonus.keys()))
        from config import STAT_KEYS
        for k in keys:
            if k not in STAT_KEYS:
                continue
            old_v = old_bonus.get(k, 0)
            new_v = new_bonus.get(k, 0)
            if k in stats:
                new_stat = max(1, stats[k] - old_v + new_v)
                updates[k] = new_stat
        if updates:
            db.update_stats(character_id, **updates)

    db.update_character(character_id, race=r["id"])
    db.inc_counter(character_id, "race_switches", 1)

    clear()
    print(box("RACE CHANGED", [
        color(f" ✓ Kau sekarang {r['name']}.", C.GREEN + C.BOLD),
        "",
        color(r.get("passive", ""), C.CYAN),
    ]))
    pause()


def handle_secret_command(character_id, cmd):
    """Wrapper untuk secret command dari main menu."""
    from cit_mode import try_secret_command
    return try_secret_command(character_id, cmd)
