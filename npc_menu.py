"""NPC menu — lihat NPC, bicara, belajar dari mentor, relationship."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from npc import (
    npcs_at, get_npc, relationship_label, time_label, time_of_day,
    get_dialog, mentors_at,
)
from guild_system import get_relationship, change_relationship, remember, get_memory
from cities import city_name


def npc_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        loc = char["location"]
        npcs = npcs_at(character_id, loc)
        clear()
        lines = [
            f" Lokasi : {city_name(loc)}",
            f" Waktu  : {time_label()}",
            "",
        ]
        if not npcs:
            lines.append(" Tidak ada NPC di sini saat ini.")
        else:
            for i, n in enumerate(npcs, 1):
                tags = []
                if n.get("recruitable"):
                    tags.append("⭐")
                if n.get("teaches"):
                    tags.append("🎓")  # mentor
                tag_str = (" " + " ".join(tags)) if tags else ""
                lines.append(
                    f" [{i}] {n['name']} ({n['role']} Lv{n['level']}){tag_str}"
                )
            lines.append("")
            lines.append(color(" ⭐ recruitable  🎓 mentor", C.DIM))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("PEOPLE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            n = npcs[int(ch) - 1]
            _npc_interact(character_id, n)
        except Exception:
            pass


def _npc_interact(character_id, npc):
    while True:
        rel = get_relationship(character_id, npc["id"])
        label, col_name = relationship_label(rel["relationship"])
        col = getattr(C, col_name.upper(), C.WHITE)

        lines = [
            color(npc["name"], C.CYAN + C.BOLD),
            f" Race       : {npc['race']}",
            f" Role       : {npc['role']}",
            f" Level      : {npc['level']}",
            f" Personality: {npc.get('personality','?')}",
        ]
        if npc.get("teaches"):
            lines.append(f" Mengajar   : {npc['teaches']}  🎓")
        lines.append("")
        lines.append(f" Relationship: {color(str(rel['relationship']), col)} ({label})")
        lines.append("")

        # Menu dinamis
        options = []
        options.append(("1", "Bicara", _talk))
        options.append(("2", "Lihat memori", _memory))
        options.append(("3", "Beri hadiah (+relationship)", _gift))
        if npc.get("teaches"):
            options.append(("4", f"Belajar role: {npc['teaches']}  🎓", _learn_from_mentor))
        options.append(("0", "Kembali", None))

        for key, txt, _ in options:
            lines.append(f" {key}. {txt}")

        print(box("NPC", lines))
        ch = prompt("> ")

        # Cari aksi
        action = None
        for key, _, fn in options:
            if ch == key:
                action = fn
                break
        if action is None:
            return
        else:
            action(character_id, npc)


def _talk(character_id, npc):
    text = get_dialog(npc)
    clear()
    lines = [
        f" {color(npc['name'], C.CYAN + C.BOLD)} berkata:",
        "",
        f" {text}",
    ]
    # Topik tambahan random
    topics = [
        "Cuaca akhir-akhir ini tidak menentu.",
        "Kudengar ada monster baru muncul di wilayah utara.",
        "Guild-guild sedang sibuk belakangan ini.",
        "Harga potion naik lagi. Menyebalkan.",
        "Kalau kau butuh pekerjaan, cek papan bounty.",
        "Aku pernah melihat reruntuhan aneh di timur.",
        "Malam ini bintang-bintang terlihat terang.",
    ]
    import random
    extra = random.choice(topics)
    lines.append("")
    lines.append(color(f" \"{extra}\"", C.GRAY))

    print(box("DIALOG", lines))
    change_relationship(character_id, npc["id"], 1)
    pause()


def _memory(character_id, npc):
    mems = get_memory(character_id, npc["id"])
    clear()
    if not mems:
        print(box("MEMORY", [f" {npc['name']} belum mengenalmu baik."]))
        pause()
        return
    lines = []
    for m in mems:
        lines.append(f" • {m['event']}")
    print(box(f"MEMORY — {npc['name']}", lines))
    pause()


def _gift(character_id, npc):
    char = db.get_character(character_id)
    clear()
    print(box("BERI HADIAH", [
        f" Beri {npc['name']} 50 Silver?",
        "",
        " 1. Ya (+3 relationship)",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    if char["silver"] < 50:
        print(color(" Silver tidak cukup.", C.RED))
        pause()
        return
    db.update_character(character_id, silver=char["silver"] - 50)
    change_relationship(character_id, npc["id"], 3)
    remember(character_id, npc["id"], "Diberi hadiah 50 Silver")
    print(color(f" ✓ {npc['name']} tersenyum. (+3 relationship)", C.GREEN))
    pause()


# ---------- MENTOR ----------
def _learn_from_mentor(character_id, npc):
    """Belajar role dari NPC mentor (yang punya field 'teaches')."""
    from roles import get_role
    from mastery import get_tree

    role_id = npc["teaches"]
    role = get_role(role_id)

    # Cek apakah sudah punya role ini
    owned = {r["role_id"] for r in db.get_roles(character_id)}
    char = db.get_character(character_id)

    clear()
    lines = [
        color(f"Belajar dari {npc['name']}", C.CYAN + C.BOLD),
        "",
        f" Role    : {role['name'] if role else role_id}",
        f" Mastery : {role.get('mastery','?') if role else '?'}",
        f" Weapon  : {', '.join(role.get('weapon', [])) if role else '-'}",
        "",
    ]

    if role_id in owned:
        lines.append(color(" ✓ Kau sudah mempelajari role ini.", C.GREEN))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("MENTOR", lines))
        prompt("> ")
        return

    # Syarat tambahan (dari role.json)
    from rank import get_rank
    cur_rank = get_rank(char["level"], bool(char.get("cit_mode")))["id"]
    min_level = 20
    min_rank = 2
    if role:
        tier = role.get("tier", 1)
        min_level = 15 + (tier - 1) * 10
        min_rank = min(6, max(1, tier))

    # Tampilkan syarat
    lines.append(color("SYARAT:", C.YELLOW))
    lv_ok = char["level"] >= min_level
    rk_ok = cur_rank >= min_rank
    lines.append(f"  Level {min_level}+    {'✓' if lv_ok else '✗'} (kamu {char['level']})")
    lines.append(f"  Rank {min_rank}+     {'✓' if rk_ok else '✗'} (kamu {cur_rank})")
    lines.append("")

    if not (lv_ok and rk_ok):
        lines.append(color(" Syarat belum terpenuhi.", C.RED))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("MENTOR", lines))
        pause()
        return

    lines.append(" 1. Minta diajari")
    lines.append(" 0. Batal")
    print(box("MENTOR", lines))

    if prompt("> ") != "1":
        return

    # Unlock role
    db.unlock_role(character_id, role_id)
    # Inisialisasi mastery tree
    tree = role.get("mastery", "combat_arts") if role else "combat_arts"
    db.get_mastery(character_id, tree)
    remember(character_id, npc["id"], f"Belajar role {role_id}")

    clear()
    print(box("🎓 ROLE DIPELAJARI", [
        color(f" {role['name'] if role else role_id} berhasil dipelajari!", C.GREEN + C.BOLD),
        "",
        " Role baru tersedia di menu 'Role & Skill'.",
        " Ganti role aktif melalui menu tersebut.",
    ]))
    pause()
