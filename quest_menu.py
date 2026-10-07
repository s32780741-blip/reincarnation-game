"""Quest menu — journal, available, active."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from quests import (
    load_quests, get_quest, available_quests, active_quests,
    is_eligible, objective_text, quest_objectives_complete,
    complete_quest,
)

def _lang():
    return settings.get("language", "id")

def quest_menu(character_id):
    while True:
        clear()
        active = active_quests(character_id)
        completed = db.get_quests(character_id, status="completed")
        lines = [
            f" Active    : {len(active)}",
            f" Completed : {len(completed)}",
            "",
            " 1. Active Quests",
            " 2. Available Quests",
            " 3. Quest Log (semua)",
            " 0. Kembali",
        ]
        print(box("QUEST JOURNAL", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _active_menu(character_id)
        elif ch == "2":
            _available_menu(character_id)
        elif ch == "3":
            _full_log(character_id)

def _active_menu(character_id):
    while True:
        active = active_quests(character_id)
        if not active:
            clear()
            print(box("ACTIVE QUESTS", [" Tidak ada quest aktif."]))
            pause()
            return
        clear()
        lines = []
        for i, q in enumerate(active, 1):
            lines.append(f" [{i}] {q['title']} [{q['difficulty']}]")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("ACTIVE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            q = active[int(ch) - 1]
            _quest_detail(character_id, q)
        except Exception:
            pass

def _available_menu(character_id):
    while True:
        avail = available_quests(character_id)
        clear()
        lines = []
        for i, (q, ok) in enumerate(avail, 1):
            mark = color("•", C.WHITE) if ok else color("🔒", C.YELLOW)
            lines.append(f" {mark} [{i:2d}] {q['title']:<32} [{q['difficulty']}] Lv{q['level_req']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("AVAILABLE QUESTS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            q, ok = avail[int(ch) - 1]
            if not ok:
                print(color(" Quest belum memenuhi syarat.", C.YELLOW))
                pause()
                continue
            _quest_offer(character_id, q)
        except Exception:
            pass

def _quest_offer(character_id, q):
    clear()
    lines = [
        color(q["title"], C.CYAN + C.BOLD),
        f" Difficulty : {q['difficulty'].upper()}",
        f" Category   : {q.get('category','?')}",
        f" Giver      : {q.get('giver','?')}",
        f" Lokasi     : {q.get('location','?')}",
        "",
        color(q.get("desc", ""), C.GRAY),
        "",
        color("OBJECTIVES:", C.YELLOW),
    ]
    for obj in q.get("objectives", []):
        lines.append(f"  • {obj.get('desc', obj['type'])}")
    rw = q.get("rewards", {})
    lines.append("")
    lines.append(color("REWARDS:", C.YELLOW))
    if rw.get("exp"): lines.append(f"  EXP    : {rw['exp']}")
    if rw.get("silver"): lines.append(f"  Silver : {rw['silver']}")
    if rw.get("gold"): lines.append(f"  Gold   : {rw['gold']}")
    for item in rw.get("items", []):
        lines.append(f"  Item   : {item['id']} x{item.get('amount',1)}")
    lines.append("")
    lines.append(" 1. Accept Quest")
    lines.append(" 0. Batal")
    print(box("QUEST", lines))
    if prompt("> ") == "1":
        db.add_quest(character_id, q["id"])
        db.inc_counter(character_id, "quests_started", 1)
        print(color(f" ✓ Quest '{q['title']}' diterima!", C.GREEN))
        pause()

def _quest_detail(character_id, q):
    clear()
    lines = [
        color(q["title"], C.CYAN + C.BOLD),
        f" Difficulty : {q['difficulty'].upper()}",
        f" Category   : {q.get('category','?')}",
        "",
        color("OBJECTIVES:", C.YELLOW),
    ]
    all_done = True
    for obj in q.get("objectives", []):
        txt = objective_text(obj, character_id)
        if "✓" not in txt:
            all_done = False
        lines.append(f"  {txt}")
    lines.append("")
    if all_done:
        lines.append(color(" ✓ Semua objective selesai!", C.GREEN))
        lines.append("")
        lines.append(" 1. Turn In Quest")
        lines.append(" 0. Kembali")
    else:
        lines.append(color(" Selesaikan semua objective dahulu.", C.YELLOW))
        lines.append("")
        lines.append(" 0. Kembali")
    print(box("QUEST DETAIL", lines))
    if prompt("> ") == "1" and all_done:
        _complete(character_id, q)

def _complete(character_id, q):
    summary = complete_quest(character_id, q)
    clear()
    lines = [
        color(f" {q['title']} SELESAI!", C.GREEN + C.BOLD),
        "",
    ]
    if summary["exp"]: lines.append(f" EXP    : +{summary['exp']}")
    if summary["silver"]: lines.append(f" Silver : +{summary['silver']}")
    if summary["gold"]: lines.append(f" Gold   : +{summary['gold']}")
    for item in summary["items"]:
        lines.append(f" Item   : {item['id']} x{item.get('amount',1)}")
    for fac, amt in summary["reputation"]:
        lines.append(f" Rep    : {fac} +{amt}")
    for lv in summary["level_ups"]:
        lines.append(color(f" ★ LEVEL UP! → Lv {lv}", C.MAGENTA + C.BOLD))
    print(box("QUEST COMPLETE", lines))
    # achievement auto-check
    try:
        from achievements import check_all
        check_all(character_id, silent=False)
    except Exception:
        pass
    pause()

def _full_log(character_id):
    clear()
    rows = db.get_quests(character_id)
    lines = []
    for r in rows:
        q = get_quest(r["quest_id"])
        title = q["title"] if q else r["quest_id"]
        lines.append(f" [{r['status']:<10}] {title}")
    if not lines:
        lines = [" Belum ada quest."]
    print(box("QUEST LOG", lines))
    pause()
