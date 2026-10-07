"""Story menu — main story, character, guild, kingdom, endings."""
from ui import C, color, clear, box, prompt, pause, progress_bar
import database as db
import settings
from story import (
    main_chapters, get_chapter, current_chapter_id, is_chapter_complete,
    mark_chapter_complete, progress_percent, total_chapters,
    get_gender_story, get_role_story, get_guild_story, get_kingdom_story,
    check_ending_available, apply_ending, unlocked_lore, unlock_lore, get_lore,
)
from cutscene import play_chapter
from npc import get_npc


def _lang():
    return settings.get("language", "id")


def story_menu(character_id):
    while True:
        clear()
        pct = progress_percent(character_id)
        cur = current_chapter_id(character_id)
        lines = [
            f" Progress: {progress_bar(pct, 16)}",
            f" Chapter : {cur or 'Selesai'}",
            "",
            " 1. Lanjutkan cerita",
            " 2. Lihat semua chapter",
            " 3. Character Story",
            " 4. Guild Story",
            " 5. Kingdom Story",
            " 6. Endings",
            " 0. Kembali",
        ]
        print(box("STORY", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _continue_story(character_id)
        elif ch == "2":
            _list_chapters(character_id)
        elif ch == "3":
            _character_story(character_id)
        elif ch == "4":
            _guild_story(character_id)
        elif ch == "5":
            _kingdom_story(character_id)
        elif ch == "6":
            _endings_menu(character_id)


def _continue_story(character_id):
    cid = current_chapter_id(character_id)
    if not cid:
        clear()
        print(box("STORY", [
            color(" ✓ Semua chapter utama selesai!", C.GREEN + C.BOLD),
            "",
            " Pilih ending di menu Endings.",
        ]))
        pause()
        return
    ch = get_chapter(cid)
    if not ch:
        return
    char = db.get_character(character_id)
    if char["level"] < ch.get("level_req", 0):
        clear()
        print(box("STORY", [
            f" Chapter: {ch['title']}",
            "",
            color(f" ✗ Butuh Level {ch['level_req']}", C.RED),
            f" Level kamu: {char['level']}",
        ]))
        pause()
        return
    # Play
    play_chapter(ch)
    mark_chapter_complete(character_id, ch["id"])

    # Special: chapter tertentu unlock lore
    unlocks = {
        "ch1": "lore_01",
        "ch3": "lore_04",
        "ch5": "lore_07",
        "ch6": "lore_17",
        "ch7": "lore_08",
        "ch8": "lore_10",
        "ch10": "lore_03",
        "ch12": "lore_40",
    }
    if ch["id"] in unlocks:
        lid = unlocks[ch["id"]]
        if unlock_lore(character_id, lid):
            l = get_lore(lid)
            if l:
                clear()
                print(box("📖 LORE UNLOCKED", [
                    color(f" {l['title']}", C.YELLOW + C.BOLD),
                    "",
                    color(l["desc"], C.WHITE),
                ]))
                pause()

    # Special: chapter 7 unlock Elara
    if ch["id"] == "ch7":
        db.set_world_state(character_id, "met_elara", "1")
        db.set_world_state(character_id, "elara_intro_done", "1")
        # Elara relationship
        db.get_relationship(character_id, "elara")
        db.change_relationship(character_id, "elara", 30)

    # Achievement
    try:
        from achievements import check_all
        check_all(character_id, silent=True)
    except Exception:
        pass


def _list_chapters(character_id):
    while True:
        clear()
        lines = []
        for i, c in enumerate(main_chapters(), 1):
            done = is_chapter_complete(character_id, c["id"])
            mark = color("✓", C.GREEN) if done else color("•", C.YELLOW)
            lines.append(
                f" {mark} [{i:2d}] {c['title']:<28} (Lv {c['level_req']})"
            )
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"CHAPTERS ({total_chapters()})", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            c = main_chapters()[int(ch) - 1]
            clear()
            done = is_chapter_complete(character_id, c["id"])
            lines = [
                color(c["title"], C.YELLOW + C.BOLD),
                f" Status : {'SELESAI' if done else 'BELUM'}",
                f" Lokasi : {c.get('location', '?')}",
                f" Lv Req : {c.get('level_req', 0)}",
                "",
                color(c.get("desc", ""), C.GRAY),
            ]
            print(box("CHAPTER", lines))
            pause()
        except Exception:
            pass


def _character_story(character_id):
    char = db.get_character(character_id)
    gender = char["gender"]
    role = char["role"]
    clear()
    lines = [color("CHARACTER STORY", C.MAGENTA + C.BOLD), ""]

    gs = get_gender_story(gender)
    if gs:
        lines.append(color(f"PATH — {gender.capitalize()}", C.CYAN + C.BOLD))
        lines.append(color(f" {gs['intro']}", C.WHITE))
        for line in gs.get("unique_lines", []):
            lines.append(color(f" \"{line}\"", C.GRAY))
        lines.append("")

    rs = get_role_story(role)
    if rs:
        lines.append(color(f"ROLE — {rs['title']}", C.CYAN + C.BOLD))
        lines.append(color(f" {rs['text']}", C.WHITE))
        if rs.get("unlock_lore"):
            if unlock_lore(character_id, rs["unlock_lore"]):
                l = get_lore(rs["unlock_lore"])
                if l:
                    lines.append("")
                    lines.append(color(f" 📖 Lore unlocked: {l['title']}", C.YELLOW))
    else:
        lines.append(color(f"Role '{role}' belum memiliki story khusus.", C.GRAY))
    print(box("CHARACTER STORY", lines))
    pause()


def _guild_story(character_id):
    from guild_system import get_player_guild
    pg = get_player_guild(character_id)
    if not pg:
        clear()
        print(box("GUILD STORY", [" Kau belum bergabung dengan guild.", "", " Bergabunglah untuk unlock story."]))
        pause()
        return
    gs = get_guild_story(pg["guild_id"])
    clear()
    if not gs:
        print(box("GUILD STORY", [f" Guild '{pg['guild_id']}' belum memiliki story."]))
        pause()
        return
    lines = [
        color(gs["title"], C.YELLOW + C.BOLD),
        "",
        color(gs["text"], C.WHITE),
        "",
        color(f" Bonus: {gs.get('bonus', '-')}", C.GREEN),
    ]
    if gs.get("unlock_lore"):
        if unlock_lore(character_id, gs["unlock_lore"]):
            l = get_lore(gs["unlock_lore"])
            if l:
                lines.append("")
                lines.append(color(f" 📖 Lore unlocked: {l['title']}", C.YELLOW))
    print(box("GUILD STORY", lines))
    pause()


def _kingdom_story(character_id):
    from cities import get_city
    char = db.get_character(character_id)
    city = get_city(char["location"])
    if not city:
        return
    kid = city["kingdom"]
    ks = get_kingdom_story(kid)
    clear()
    if not ks:
        print(box("KINGDOM STORY", [f" Kingdom '{kid}' belum memiliki story."]))
        pause()
        return
    lines = [
        color(ks["title"], C.YELLOW + C.BOLD),
        "",
        color(ks["text"], C.WHITE),
    ]
    if ks.get("unlock_lore"):
        if unlock_lore(character_id, ks["unlock_lore"]):
            l = get_lore(ks["unlock_lore"])
            if l:
                lines.append("")
                lines.append(color(f" 📖 Lore unlocked: {l['title']}", C.YELLOW))
    print(box("KINGDOM STORY", lines))
    pause()


def _endings_menu(character_id):
    avail = check_ending_available(character_id)
    if not avail:
        clear()
        print(box("ENDINGS", [
            " Kau belum mencapai akhir cerita.",
            "",
            " Selesaikan 12 chapter utama untuk membuka ending.",
        ]))
        pause()
        return

    while True:
        clear()
        lines = []
        for i, e in enumerate(avail, 1):
            col = getattr(C, e.get("color", "white").upper(), C.WHITE)
            lines.append(f" [{i}] {color(e['title'], col)}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("CHOOSE YOUR ENDING", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            e = avail[int(ch) - 1]
            clear()
            lines = [
                color(e["title"], getattr(C, e.get("color", "white").upper(), C.WHITE) + C.BOLD),
                "",
                f" Kondisi: {e.get('condition','')}",
                "",
                color(e["text"], C.WHITE),
                "",
                " 1. Pilih ending ini",
                " 0. Batal",
            ]
            print(box("ENDING", lines))
            if prompt("> ") == "1":
                apply_ending(character_id, e["id"])
                clear()
                print(box("ENDING APPLIED", [
                    color(f" {e['title']}", C.YELLOW + C.BOLD),
                    "",
                    " Perjalananmu berakhir di sini.",
                    "",
                    " Terima kasih sudah bermain.",
                ]))
                pause()
                return
        except Exception:
            pass
