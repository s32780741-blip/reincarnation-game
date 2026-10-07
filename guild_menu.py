"""Guild menu — join, exam, member, recruitment."""
from ui import C, color, clear, box, prompt, pause, progress_bar
import database as db
import settings
from guilds import load_guilds, get_guild, guild_name, by_rank, guild_color
from guild_system import (
    get_player_guild, set_player_guild, leave_guild, run_guild_exam,
    get_applications, resolve_application, get_guild_members,
    can_rank_up, rank_up, RANK_NAMES, add_contribution,
)
from npc import get_npc


def guild_menu(character_id):
    while True:
        pg = get_player_guild(character_id)
        clear()
        if pg:
            g = get_guild(pg["guild_id"])
            lines = [
                f" Guild : {color(g['name'] if g else pg['guild_id'], guild_color(pg['guild_id']) + C.BOLD)}",
                f" Rank  : {pg['rank']} — {RANK_NAMES.get(pg['rank'], '?')}",
                f" Contribution: {pg['contribution']}",
                "",
                " 1. Guild Hub",
                " 2. Member List",
                " 3. Recruitment",
                " 4. Guild Ranking",
                " 5. Leave Guild",
                " 0. Kembali",
            ]
        else:
            lines = [
                " Kamu bukan anggota guild.",
                "",
                " 1. Lihat semua guild",
                " 2. Guild Ranking",
                " 0. Kembali",
            ]
        print(box("GUILD", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            if pg:
                _guild_hub(character_id)
            else:
                _list_guilds(character_id)
        elif ch == "2":
            if pg:
                _member_list(character_id)
            else:
                _ranking()
        elif ch == "3":
            if pg:
                _recruitment(character_id)
        elif ch == "4":
            if pg:
                _ranking()
        elif ch == "5":
            if pg:
                if _confirm("Keluar dari guild ini?"):
                    leave_guild(character_id)
                    print(color(" Kamu keluar dari guild.", C.YELLOW))
                    pause()
        else:
            print(color(" Invalid.", C.RED)); pause()


def _list_guilds(character_id):
    while True:
        guilds = by_rank()
        clear()
        lines = []
        for i, g in enumerate(guilds, 1):
            col = guild_color(g["id"])
            lines.append(f" [{i:2d}] {color(g['name'], col)}  #{g['rank_global']}")
            lines.append(f"      Power {g['power']:,}  Members {g['members']}  Rep {g['reputation']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("ALL GUILDS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            g = guilds[int(ch) - 1]
            _guild_detail(character_id, g)
        except Exception:
            pass


def _guild_detail(character_id, g):
    clear()
    col = guild_color(g["id"])
    req = g.get("join_req", {})
    lines = [
        color(g["name"], col + C.BOLD) + f"   #{g['rank_global']}",
        f" Leader      : {g['leader']}",
        f" Members     : {g['members']}",
        f" Power       : {g['power']:,}",
        f" Reputation  : {g['reputation']}",
        f" Total Bounty: {g['total_bounty']:,}",
        f" Total Kills : {g['total_kill']:,}",
        f" Wealth      : {g['wealth']:,}",
        f" Territory   : {g['territory']}",
        f" Specialty   : {g['specialization']}",
        f" Alignment   : {g['alignment']}",
        f" HQ          : {guild_name(g['headquarters']) if g.get('headquarters') else '?'}",
        "",
        color(g["desc"], C.GRAY),
        "",
        color("JOIN REQUIREMENT:", C.YELLOW),
        f"  Level : {req.get('level', 0)}+",
        f"  Rank  : {req.get('rank_req', 1)}+",
        "",
        " 1. Ambil Ujian Masuk",
        " 0. Kembali",
    ]
    print(box("GUILD DETAIL", lines))
    if prompt("> ") == "1":
        _run_exam(character_id, g)


def _run_exam(character_id, g):
    result = run_guild_exam(character_id, g["id"])
    if not result.get("ok") and "reason" in result:
        clear()
        print(box("GUILD EXAM", [
            color(" ✗ Tidak memenuhi syarat.", C.RED),
            f" {result['reason']}",
        ]))
        pause()
        return
    # Show each exam result
    clear()
    print(box(f"GUILD EXAM — {g['name']}", [
        " Ujian masuk guild akan dimulai.",
        " 3 ujian dari kategori berbeda.",
        "",
        " Tekan Enter untuk mulai...",
    ]))
    prompt("")

    for i, r in enumerate(result["results"], 1):
        ex = r["exam"]
        clear()
        col = C.GREEN if r["ok"] else C.RED
        mark = "✓ LULUS" if r["ok"] else "✗ GAGAL"
        lines = [
            f" [{i}/3] {ex['category_name']} — {ex['name']}",
            "",
            f" {ex['desc']}",
            "",
            f" Stat uji : {ex['stat']} ({r['stat']})",
            f" Roll     : {r['roll']} vs {r['threshold']}",
            "",
            color(f" {mark}", col + C.BOLD),
        ]
        print(box("EXAM", lines))
        pause()

    # Summary
    clear()
    if result["ok"]:
        set_player_guild(character_id, g["id"], "F")
        lines = [
            color(" ★ LULUS!", C.GREEN + C.BOLD),
            f" Kamu resmi masuk guild {g['name']}.",
            "",
            " Rank: F — Recruit",
            " Selesaikan quest guild untuk naik rank.",
        ]
        print(box("GUILD EXAM", lines))
        try:
            from achievements import check_all
            check_all(character_id, silent=False)
        except Exception:
            pass
    else:
        lines = [
            color(" ✗ GAGAL", C.RED + C.BOLD),
            f" Skor: {result['passed_count']}/{result['total']}",
            "",
            " Minimal 2/3 lulus untuk masuk.",
            " Coba lagi setelah menaikkan stat.",
        ]
        print(box("GUILD EXAM", lines))
    pause()


def _guild_hub(character_id):
    while True:
        pg = get_player_guild(character_id)
        if not pg:
            return
        g = get_guild(pg["guild_id"])
        # Rank up check
        can_up, cur, nxt = can_rank_up(character_id)
        cont = pg["contribution"]
        lines = [
            f" Guild  : {g['name'] if g else pg['guild_id']}",
            f" Rank   : {pg['rank']} — {RANK_NAMES.get(pg['rank'], '?')}",
            f" Contr. : {cont}",
        ]
        if nxt:
            need = 0
            from guild_system import RANK_CONTRIBUTION
            need = RANK_CONTRIBUTION[nxt]
            pct = min(100, int(cont / max(1, need) * 100))
            lines.append(f" Next   : {nxt} ({need}) {progress_bar(pct, 14)}")
        lines.append("")
        lines.append(" 1. Rank Up" if can_up else " 1. Rank Up (belum bisa)")
        lines.append(" 2. Guild Quest (dapat contribution)")
        lines.append(" 3. Member List")
        lines.append(" 4. Recruitment")
        lines.append(" 0. Kembali")
        print(box("GUILD HUB", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            if can_up:
                ok, new_rank = rank_up(character_id)
                if ok:
                    print(color(f" ★ Rank naik ke {new_rank} — {RANK_NAMES.get(new_rank,'?')}", C.GREEN + C.BOLD))
                pause()
            else:
                print(color(" Belum cukup contribution.", C.YELLOW)); pause()
        elif ch == "2":
            _guild_quest(character_id)
        elif ch == "3":
            _member_list(character_id)
        elif ch == "4":
            _recruitment(character_id)


def _guild_quest(character_id):
    """Simple guild quest: pilih kategori, dapat contribution + exp."""
    clear()
    lines = [
        " Pilih kontribusi untuk guild:",
        "",
        " 1. Berburu monster untuk guild (500 exp + 30 contribution)",
        " 2. Menyelesaikan quest guild (200 exp + 50 contribution)",
        " 3. Mengumpulkan material (300 exp + 40 contribution)",
        " 0. Batal",
    ]
    print(box("GUILD QUEST", lines))
    ch = prompt("> ")
    from character import grant_exp
    if ch == "1":
        grant_exp(character_id, 500)
        add_contribution(character_id, 30)
        db.inc_counter(character_id, "guild_contributions", 30)
        print(color(" +500 EXP  +30 Contribution", C.GREEN))
    elif ch == "2":
        grant_exp(character_id, 200)
        add_contribution(character_id, 50)
        db.inc_counter(character_id, "guild_contributions", 50)
        print(color(" +200 EXP  +50 Contribution", C.GREEN))
    elif ch == "3":
        grant_exp(character_id, 300)
        add_contribution(character_id, 40)
        db.inc_counter(character_id, "guild_contributions", 40)
        print(color(" +300 EXP  +40 Contribution", C.GREEN))
    else:
        return
    pause()


def _member_list(character_id):
    members = get_guild_members(character_id)
    clear()
    if not members:
        print(box("MEMBERS", [" Belum ada NPC yang bergabung."]))
        pause()
        return
    lines = []
    for m in members:
        npc = get_npc(m["npc_id"])
        name = npc["name"] if npc else m["npc_id"]
        lines.append(f" [{m['rank']}] {name:<20} Power {m['power']}")
    print(box(f"MEMBERS ({len(members)})", lines))
    pause()


def _recruitment(character_id):
    while True:
        apps = get_applications(character_id, "pending")
        clear()
        lines = [f" Pending applications: {len(apps)}", ""]
        if not apps:
            lines.append(" Belum ada aplikasi baru.")
            lines.append("")
            lines.append(" 1. Cek aplikasi baru (random event)")
            lines.append(" 0. Kembali")
            print(box("RECRUITMENT", lines))
            ch = prompt("> ")
            if ch == "0":
                return
            elif ch == "1":
                from guild_system import maybe_spawn_application
                npc = maybe_spawn_application(character_id)
                if npc:
                    clear()
                    print(box("NEW APPLICATION", [
                        color(f" {npc['name']} mengirim aplikasi!", C.GREEN + C.BOLD),
                        "",
                        f' "{npc.get("application_reason","...")}"',
                    ]))
                    pause()
                else:
                    print(color(" Tidak ada aplikasi baru saat ini.", C.YELLOW))
                    pause()
            continue
        for i, a in enumerate(apps, 1):
            npc = get_npc(a["npc_id"])
            name = npc["name"] if npc else a["npc_id"]
            lines.append(f" [{i}] {name}  ({npc.get('role','?') if npc else '?'})")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("RECRUITMENT", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            app = apps[int(ch) - 1]
            _app_detail(character_id, app)
        except Exception:
            pass


def _app_detail(character_id, app):
    npc = get_npc(app["npc_id"])
    if not npc:
        return
    clear()
    lines = [
        color(npc["name"], C.CYAN + C.BOLD),
        f" Race  : {npc['race']}",
        f" Role  : {npc['role']}",
        f" Level : {npc['level']}",
        f" Skill : {npc.get('skill','?')}",
        "",
        color("SURAT APLIKASI:", C.YELLOW),
        color(f' "{app["reason"]}"', C.GRAY),
        "",
        " 1. Accept",
        " 2. Reject",
        " 3. Interview",
        " 0. Kembali",
    ]
    print(box("APPLICATION", lines))
    ch = prompt("> ")
    if ch == "1":
        ok, status = resolve_application(character_id, app["id"], accept=True)
        if ok:
            print(color(f" ✓ {npc['name']} bergabung dengan guild!", C.GREEN))
            pause()
    elif ch == "2":
        ok, _ = resolve_application(character_id, app["id"], accept=False)
        print(color(f" {npc['name']} ditolak.", C.YELLOW))
        pause()
    elif ch == "3":
        _interview(character_id, npc, app)


def _interview(character_id, npc, app):
    clear()
    lines = [
        color(f"Interview dengan {npc['name']}", C.CYAN + C.BOLD),
        "",
        f" Personality: {npc.get('personality','?')}",
        "",
        " 1. Tanya soal motivasi",
        " 2. Tanya soal skill",
        " 3. Tanya soal pengalaman",
        " 4. Terima langsung",
        " 5. Tolak",
        " 0. Kembali",
    ]
    print(box("INTERVIEW", lines))
    ch = prompt("> ")
    if ch == "1":
        clear()
        print(box("INTERVIEW", [
            f" {npc['name']}:",
            f' "{app["reason"]}"',
        ]))
        pause()
    elif ch == "2":
        clear()
        print(box("INTERVIEW", [
            f" {npc['name']} menunjukkan kemampuannya:",
            f" Skill: {npc.get('skill','?')}",
            f" Level: {npc['level']}",
        ]))
        pause()
    elif ch == "3":
        clear()
        print(box("INTERVIEW", [
            f" {npc['name']}:",
            f' "Aku telah melalui banyak pertempuran. Level {npc["level"]} bukan tanpa alasan."',
        ]))
        pause()
    elif ch == "4":
        ok, _ = resolve_application(character_id, app["id"], accept=True)
        print(color(f" ✓ {npc['name']} bergabung!", C.GREEN)); pause()
    elif ch == "5":
        ok, _ = resolve_application(character_id, app["id"], accept=False)
        print(color(f" {npc['name']} ditolak.", C.YELLOW)); pause()


def _ranking():
    clear()
    guilds = by_rank()
    lines = [color(" TOP 10 GUILDS", C.YELLOW + C.BOLD), ""]
    for g in guilds:
        col = guild_color(g["id"])
        lines.append(f" #{g['rank_global']:>2} {color(g['name'], col)}")
        lines.append(f"     Power  : {g['power']:,}")
        lines.append(f"     Bounty : {g['total_bounty']:,}")
        lines.append(f"     Kills  : {g['total_kill']:,}")
        lines.append("")
    print(box("GUILD RANKING", lines))
    pause()


def _confirm(msg):
    clear()
    print(box("CONFIRM", [f" {msg}", "", " 1. Ya   0. Batal"]))
    return prompt("> ") == "1"
