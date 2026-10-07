"""Achievement menu."""
from ui import C, color, clear, box, prompt, pause
import database as db
from achievements import load_achievements
from reputation import rep_line, rep_label

def achievement_menu(character_id):
    while True:
        clear()
        unlocked = {a["achievement_id"] for a in db.get_achievements(character_id)}
        all_ach = load_achievements()
        lines = [
            f" Total: {len(all_ach)}",
            f" Unlocked: {len(unlocked)}",
            f" Progress: {int(len(unlocked) / max(1, len(all_ach)) * 100)}%",
            "",
            " 1. Lihat achievement",
            " 2. Lihat reputation",
            " 0. Kembali",
        ]
        print(box("ACHIEVEMENTS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _list(character_id, unlocked, all_ach)
        elif ch == "2":
            _reputation(character_id)

def _list(character_id, unlocked, all_ach):
    clear()
    lines = []
    for a in all_ach:
        mark = color("✓", C.GREEN) if a["id"] in unlocked else color("✗", C.GRAY)
        name = color(a["name"], C.YELLOW if a["id"] in unlocked else C.WHITE)
        lines.append(f" {mark} {name}")
        lines.append(color(f"     {a['desc']}", C.GRAY))
    print(box("ALL ACHIEVEMENTS", lines))
    pause()

def _reputation(character_id):
    clear()
    rows = db.get_all_reputation(character_id)
    if not rows:
        print(box("REPUTATION", [" Belum ada reputation."]))
        pause()
        return
    lines = []
    for r in rows:
        label, col = rep_label(r["value"])
        lines.append(f" {r['faction_type']}:{r['faction_id']}  =  {color(str(r['value']), col)} ({label})")
    print(box("REPUTATION", lines))
    pause()
