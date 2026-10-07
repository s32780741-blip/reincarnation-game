"""Role menu — view, switch, learn skills."""
from ui import C, color, clear, box, prompt, pause
from i18n import t
import database as db
import settings
from roles import load_roles, get_role, role_menu_list, mastery_tree, stat_bias, weapon_pref
from mastery import mastery_display, get_tree
from skills import skills_for_role, get_skill

def _lang():
    return settings.get("language", "id")

def role_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        clear()
        active_id = char["role"]
        active = get_role(active_id)
        owned = [r["role_id"] for r in db.get_roles(character_id)]

        lines = [
            f" Aktif   : {color(active['name'] if active else active_id, C.GREEN + C.BOLD)}",
            f" Dimiliki: {len(owned)} role",
            "",
            " 1. Lihat semua role",
            " 2. Ganti role aktif",
            " 3. Skill & Mastery",
            " 4. Cari Mentor",
            " 5. Latihan (Training)",
            " 0. Kembali",
        ]
        print(box("ROLE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _view_all(char)
        elif ch == "2":
            _switch_role(character_id)
        elif ch == "3":
            _skill_menu(character_id)
        elif ch == "4":
            from mentor import mentors_in_location, can_train, get_mentor, train
            loc = char["location"]
            ms = mentors_in_location(loc)
            if not ms:
                print(color(" Tidak ada mentor di kota ini.", C.YELLOW)); pause(); continue
            _mentor_menu(character_id, ms)
        elif ch == "5":
            from training import training_menu
            training_menu(character_id)
        else:
            print(color(" Input tidak valid.", C.RED)); pause()

def _view_all(char):
    clear()
    gender = char["gender"]
    owned = {r["role_id"] for r in db.get_roles(char["id"])}
    listing = role_menu_list(gender, owned)

    lines = []
    for i, (r, status) in enumerate(listing, 1):
        if status == "owned":
            mark = color("✓", C.GREEN)
            name = color(r["name"], C.GREEN)
        elif status == "mentor_locked":
            mark = color("🔒", C.YELLOW)
            name = color(r["name"], C.GRAY)
        else:
            mark = color("•", C.WHITE)
            name = r["name"]
        lines.append(f" {mark} [{i:2d}] {name}  T{r.get('tier','?')}")
    lines.append("")
    lines.append(color("✓ dimiliki  • bisa dipelajari  🔒 mentor", C.DIM))
    lines.append("")
    lines.append(" 1. Detail role  0. Kembali")
    print(box(f"ALL ROLES ({len(listing)})", lines))
    ch = prompt("> ")
    if ch == "1":
        n = prompt(" Nomor role: ")
        try:
            r, status = listing[int(n) - 1]
            _detail_role(r, status)
        except Exception:
            pass

def _detail_role(r, status):
    clear()
    lines = [
        f" Nama   : {color(r['name'], C.CYAN + C.BOLD)}",
        f" Tier   : {r.get('tier','?')}",
        f" Gender : {', '.join(r.get('gender', []))}",
        f" Weapon : {', '.join(weapon_pref(r['id']))}",
        f" Status : {status}",
        "",
        color(r.get('desc',''), C.GRAY),
        "",
        color("Bias stat:", C.YELLOW),
    ]
    for k, v in stat_bias(r["id"]).items():
        sign = "+" if v > 0 else ""
        lines.append(f"   {k}: {sign}{v}")
    print(box("ROLE DETAIL", lines))
    pause()

def _switch_role(character_id):
    char = db.get_character(character_id)
    owned = db.get_roles(character_id)
    if not owned:
        print(color(" Tidak punya role lain.", C.YELLOW)); pause(); return
    clear()
    lines = []
    for i, o in enumerate(owned, 1):
        r = get_role(o["role_id"])
        mark = color(" ●", C.GREEN) if o["is_active"] else "  "
        lines.append(f"{mark} [{i}] {r['name'] if r else o['role_id']}")
    lines.append("")
    lines.append(" 0. Batal")
    print(box("GANTI ROLE", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        idx = int(ch) - 1
        target = owned[idx]
        db.set_active_role(character_id, target["role_id"])
        print(color(f" Role aktif: {target['role_id']}", C.GREEN))
    except Exception:
        print(color(" Invalid.", C.RED))
    pause()

def _skill_menu(character_id):
    char = db.get_character(character_id)
    tree_id = mastery_tree(char["role"])
    while True:
        clear()
        print(box("SKILL & MASTERY", [
            f" Role    : {char['role']}",
            f" Mastery : {mastery_display(character_id, tree_id)}",
            "",
            " 1. Lihat skill role ini",
            " 2. Pelajari skill baru",
            " 3. Lihat semua mastery",
            " 0. Kembali",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _list_skills(character_id, char["role"])
        elif ch == "2":
            _learn_skill(character_id, char["role"], tree_id)
        elif ch == "3":
            _all_mastery(character_id)

def _list_skills(character_id, role_id):
    clear()
    learned = {s["skill_id"]: s for s in db.get_skills(character_id)}
    all_sk = skills_for_role(role_id)
    if not all_sk:
        print(color(" Tidak ada skill untuk role ini (belum diimplementasikan).", C.YELLOW))
        pause(); return
    lines = []
    for s in all_sk:
        mark = color("✓", C.GREEN) if s["id"] in learned else color("✗", C.RED)
        t = s.get("type", "active")
        lines.append(f" {mark} {s['name']} [{t}] req M{s.get('mastery_req',1)}")
        if s["id"] in learned:
            lines.append(color(f"     {s.get('desc','')}", C.GRAY))
    print(box(f"SKILLS — {role_id}", lines))
    pause()

def _learn_skill(character_id, role_id, tree_id):
    all_sk = skills_for_role(role_id)
    if not all_sk:
        return
    m = db.get_mastery(character_id, tree_id)
    learned = {s["skill_id"] for s in db.get_skills(character_id)}
    options = [s for s in all_sk if s["id"] not in learned]
    if not options:
        print(color(" Semua skill role ini sudah dipelajari.", C.GREEN)); pause(); return
    clear()
    lines = []
    for i, s in enumerate(options, 1):
        ok = m["level"] >= s.get("mastery_req", 1)
        mark = color("•", C.WHITE) if ok else color("🔒", C.YELLOW)
        lines.append(f" {mark} [{i}] {s['name']} (req M{s.get('mastery_req',1)}, kamu M{m['level']})")
    lines.append("")
    lines.append(" 0. Batal")
    print(box("PELAJARI SKILL", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        target = options[int(ch) - 1]
    except Exception:
        return
    if m["level"] < target.get("mastery_req", 1):
        print(color(f" Mastery belum cukup. Butuh M{target['mastery_req']}.", C.RED)); pause(); return
    if db.learn_skill(character_id, target["id"]):
        print(color(f" ✓ Skill '{target['name']}' dipelajari!", C.GREEN))
    else:
        print(color(" Sudah dipelajari.", C.YELLOW))
    pause()

def _all_mastery(character_id):
    clear()
    from mastery import load_trees
    trees = load_trees()
    lines = []
    for tid, t in trees.items():
        lines.append(f" {t['name']}: {mastery_display(character_id, tid)}")
    print(box("MASTERY TREE", lines))
    pause()

def _mentor_menu(character_id, mentors):
    while True:
        clear()
        char = db.get_character(character_id)
        lines = []
        for i, m in enumerate(mentors, 1):
            from mentor import can_train
            ok, reasons = can_train(character_id, m, char)
            mark = color("✓", C.GREEN) if ok else color("🔒", C.YELLOW)
            lines.append(f" {mark} [{i}] {m['name']} → {m['teaches']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("MENTOR", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            m = mentors[int(ch) - 1]
        except Exception:
            continue
        _talk_mentor(character_id, m)

def _talk_mentor(character_id, m):
    from mentor import can_train, train
    clear()
    char = db.get_character(character_id)
    ok, reasons = can_train(character_id, m, char)
    lines = [
        color(m["name"], C.CYAN + C.BOLD),
        "",
        color(f'"{m.get("dialog","")}"', C.GRAY),
        "",
        f"Mengajarkan: {m['teaches']}",
        f"Biaya: {m.get('cost_gold',0)} Gold",
    ]
    if not ok:
        lines.append("")
        lines.append(color("Syarat belum terpenuhi:", C.YELLOW))
        for r in reasons:
            lines.append(f"  • {r}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("MENTOR", lines))
        prompt("> ")
        return
    lines.append("")
    lines.append(" 1. Pelajari role ini")
    lines.append(" 0. Kembali")
    print(box("MENTOR", lines))
    if prompt("> ") == "1":
        success, msg = train(character_id, m["id"])
        if success:
            print(color(f" ✓ {msg}", C.GREEN))
        else:
            print(color(f" ✗ {msg}", C.RED))
        pause()
