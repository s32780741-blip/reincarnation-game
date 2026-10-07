"""Lore menu."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from story import all_lore, unlocked_lore, get_lore, has_lore


def lore_menu(character_id):
    while True:
        unlocked = unlocked_lore(character_id)
        total = len(all_lore())
        clear()
        lines = [
            f" Total Lore   : {total}",
            f" Unlocked     : {len(unlocked)}",
            f" Progress     : {int(len(unlocked)/max(1,total)*100)}%",
            "",
            " 1. Lihat lore terkumpul",
            " 2. Lihat semua lore (dengan hint)",
            " 0. Kembali",
        ]
        print(box("LORE ARCHIVE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _list_unlocked(character_id)
        elif ch == "2":
            _list_all(character_id)


def _list_unlocked(character_id):
    unlocked = unlocked_lore(character_id)
    if not unlocked:
        clear()
        print(box("LORE", [" Belum ada lore terkumpul.", "", " Jelajahi dunia untuk menemukan lore."]))
        pause()
        return
    while True:
        clear()
        lines = []
        for i, l in enumerate(unlocked, 1):
            lines.append(f" [{i:2d}] [{l['category']:<10}] {l['title']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"LORE ({len(unlocked)})", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            l = unlocked[int(ch) - 1]
            clear()
            print(box(l["title"], [
                f" Kategori: {l['category']}",
                "",
                color(l["desc"], C.WHITE),
            ]))
            pause()
        except Exception:
            pass


def _list_all(character_id):
    while True:
        clear()
        lines = []
        for i, l in enumerate(all_lore(), 1):
            have = has_lore(character_id, l["id"])
            mark = color("✓", C.GREEN) if have else color("?", C.GRAY)
            title = l["title"] if have else "???"
            lines.append(f" {mark} [{i:2d}] {title}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"ALL LORE ({len(all_lore())})", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            l = all_lore()[int(ch) - 1]
            if has_lore(character_id, l["id"]):
                clear()
                print(box(l["title"], [
                    f" Kategori: {l['category']}",
                    "",
                    color(l["desc"], C.WHITE),
                ]))
            else:
                clear()
                print(box("???", [
                    " Kau belum menemukan lore ini.",
                    "",
                    color(" Jelajahi dunia, selesaikan quest, atau bicara dengan NPC.", C.GRAY),
                ]))
            pause()
        except Exception:
            pass
