"""Bounty menu — accept, track, turn in."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from bounty import (
    load_bounties, get_bounty, available_bounties, active_bounties,
    accept_bounty, complete_bounty, threat_color,
)

def _lang():
    return settings.get("language", "id")

def bounty_menu(character_id):
    while True:
        clear()
        active = active_bounties(character_id)
        completed = db.get_bounties(character_id, status="completed")
        ready = db.get_bounties(character_id, status="ready_to_turn_in")
        lines = [
            f" Aktif       : {len(active)}",
            f" Siap klaim  : {len(ready)}",
            f" Selesai     : {len(completed)}",
            "",
            " 1. Active Bounties",
            " 2. Available Bounties",
            " 3. Klaim Bounty",
            " 0. Kembali",
        ]
        print(box("BOUNTY BOARD", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _active(character_id)
        elif ch == "2":
            _available(character_id)
        elif ch == "3":
            _claim(character_id)

def _available(character_id):
    while True:
        avail = available_bounties(character_id)
        clear()
        lines = []
        for i, b in enumerate(avail, 1):
            col = threat_color(b["threat"])
            lines.append(f" [{i:2d}] {color(b['name'], col)}")
            lines.append(f"      Tipe: {b['type']}  Level: {b['target_level']}  Threat: {b['threat']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("AVAILABLE BOUNTIES", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            b = avail[int(ch) - 1]
            _bounty_detail(character_id, b)
        except Exception:
            pass

def _bounty_detail(character_id, b):
    clear()
    col = threat_color(b["threat"])
    rw = b.get("reward", {})
    lines = [
        color(b["name"], col + C.BOLD),
        f" Tipe       : {b['type']}",
        f" Target     : {b['target_name']}",
        f" Level      : {b['target_level']}",
        f" Threat     : {color(b['threat'], col)}",
        f" Lokasi     : {b['location']}",
        f" Kondisi    : {b['condition']}",
        f" Guild      : {b.get('guild','?')}",
        "",
        color(b.get("desc", ""), C.GRAY),
        "",
        color("REWARD:", C.YELLOW),
    ]
    if rw.get("exp"): lines.append(f"  EXP    : {rw['exp']}")
    if rw.get("silver"): lines.append(f"  Silver : {rw['silver']}")
    if rw.get("gold"): lines.append(f"  Gold   : {rw['gold']}")
    lines.append("")
    lines.append(" 1. Accept Bounty")
    lines.append(" 0. Batal")
    print(box("BOUNTY", lines))
    if prompt("> ") == "1":
        if accept_bounty(character_id, b["id"]):
            print(color(f" ✓ Bounty '{b['name']}' diterima!", C.GREEN))
        else:
            print(color(" Sudah diterima.", C.YELLOW))
        pause()

def _active(character_id):
    while True:
        active = active_bounties(character_id)
        if not active:
            clear()
            print(box("ACTIVE BOUNTIES", [" Tidak ada bounty aktif."]))
            pause()
            return
        clear()
        lines = []
        for i, b in enumerate(active, 1):
            col = threat_color(b["threat"])
            lines.append(f" [{i}] {color(b['name'], col)}")
            lines.append(f"      Target: {b['target_name']} Lv{b['target_level']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("ACTIVE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            b = active[int(ch) - 1]
            _active_detail(character_id, b)
        except Exception:
            pass

def _active_detail(character_id, b):
    clear()
    col = threat_color(b["threat"])
    lines = [
        color(b["name"], col + C.BOLD),
        f" Target     : {b['target_name']}",
        f" Level      : {b['target_level']}",
        f" Lokasi     : {b['location']}",
        f" Kondisi    : {b['condition']}",
        "",
        color("Untuk menyelesaikan: kalahkan target di Hunt/Adventure.", C.YELLOW),
        "",
        " 0. Kembali",
    ]
    print(box("BOUNTY DETAIL", lines))
    prompt("> ")

def _claim(character_id):
    ready = db.get_bounties(character_id, status="ready_to_turn_in")
    if not ready:
        clear()
        print(box("CLAIM", [" Tidak ada bounty siap diklaim."]))
        pause()
        return
    clear()
    lines = []
    for i, r in enumerate(ready, 1):
        b = get_bounty(r["bounty_id"])
        if b:
            lines.append(f" [{i}] {b['name']}")
    lines.append("")
    lines.append(" 0. Kembali")
    print(box("CLAIM BOUNTY", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        b = get_bounty(ready[int(ch) - 1]["bounty_id"])
        _finish(character_id, b)
    except Exception:
        pass

def _finish(character_id, b):
    summary = complete_bounty(character_id, b)
    clear()
    lines = [
        color(f" {b['name']} SELESAI!", C.GREEN + C.BOLD),
        "",
    ]
    if summary["exp"]: lines.append(f" EXP    : +{summary['exp']}")
    if summary["silver"]: lines.append(f" Silver : +{summary['silver']}")
    if summary["gold"]: lines.append(f" Gold   : +{summary['gold']}")
    for fac, amt in summary["reputation"]:
        lines.append(f" Rep    : {fac} +{amt}")
    for lv in summary["level_ups"]:
        lines.append(color(f" ★ LEVEL UP! → Lv {lv}", C.MAGENTA + C.BOLD))
    print(box("BOUNTY COMPLETE", lines))
    try:
        from achievements import check_all
        check_all(character_id, silent=False)
    except Exception:
        pass
    pause()
