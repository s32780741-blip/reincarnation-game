"""World menu — view kingdoms, cities, regions, teleport."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from kingdoms import load_kingdoms, get_kingdom
from cities import load_cities, get_city, cities_in_kingdom, danger_label, city_name
from world import load_regions, regions_in_kingdom

def _lang():
    return settings.get("language", "id")

def world_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        current = get_city(char["location"])
        lines = [
            f" Lokasi saat ini : {color(current['name'] if current else char['location'], C.GREEN)}",
            f" Kingdom         : {current['kingdom'] if current else '?'}",
            "",
            " 1. Lihat Kerajaan",
            " 2. Lihat Kota",
            " 3. Lihat Region",
            " 4. Teleport / Perjalanan",
            " 0. Kembali",
        ]
        print(box("WORLD", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _kingdom_list()
        elif ch == "2":
            _city_list()
        elif ch == "3":
            _region_list()
        elif ch == "4":
            from teleport import teleport_menu
            teleport_menu(character_id)
        else:
            print(color(" Invalid.", C.RED)); pause()

def _kingdom_list():
    while True:
        clear()
        ks = load_kingdoms()
        lines = []
        for i, k in enumerate(ks, 1):
            lines.append(f" [{i}] {k['name']}")
            lines.append(f"     Ruler   : {k['ruler']}")
            lines.append(f"     Culture : {k['culture']}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("KINGDOMS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            idx = int(ch) - 1
            _kingdom_detail(ks[idx])
        except Exception:
            pass

def _kingdom_detail(k):
    clear()
    lines = [
        color(k["name"], C.CYAN + C.BOLD),
        "",
        f" Ruler        : {k['ruler']}",
        f" Royal family : {', '.join(k['royal_family'])}",
        f" Military     : {k['military']}/10",
        f" Economy      : {k['economy']}/10",
        f" Culture      : {k['culture']}",
        f" Territory    : {k['territory']}",
        f" Specialty    : {k['specialty']}",
        f" Conflict     : {k['conflict']}",
        "",
        color(k["desc"], C.GRAY),
        "",
        f" Capital : {city_name(k['capital'])}",
        f" Kota    : {len(cities_in_kingdom(k['id']))}",
    ]
    print(box("KINGDOM DETAIL", lines))
    pause()

def _city_list():
    while True:
        clear()
        cs = load_cities()
        lines = []
        for i, c in enumerate(cs, 1):
            t = c["type"][:3].upper()
            lines.append(f" [{i:2d}] {c['name']:<14} [{t}]  {danger_label(c.get('danger',1))}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"CITIES ({len(cs)})", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            idx = int(ch) - 1
            _city_detail(cs[idx])
        except Exception:
            pass

def _city_detail(c):
    clear()
    lines = [
        color(c["name"], C.CYAN + C.BOLD),
        f" Kingdom       : {c['kingdom']}",
        f" Type          : {c['type']}",
        f" Population    : {c['population']:,}",
        f" Danger        : {danger_label(c.get('danger',1))} ({c.get('danger',1)}/10)",
        f" Rec. Level    : {c.get('recommended_level',['?','?'])[0]} - {c.get('recommended_level',['?','?'])[1]}",
        "",
        color(c["desc"], C.GRAY),
        "",
        f" Guild Hub     : {'Ya' if c.get('guild_hub') else 'Tidak'}",
        f" Academy       : {'Ya' if c.get('academy') else 'Tidak'}",
        f" Black Market  : {'Ya' if c.get('black_market') else 'Tidak'}",
        f" Teleport      : {c.get('teleport','-')}",
    ]
    print(box("CITY DETAIL", lines))
    pause()

def _region_list():
    while True:
        clear()
        rs = load_regions()
        lines = []
        for i, r in enumerate(rs, 1):
            rl = r.get("recommended_level", ["?", "?"])
            lines.append(f" [{i:2d}] {r['name']:<22} [{r['biome'][:6]}]  D:{r['danger']}  Lv{rl[0]}-{rl[1]}")
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"REGIONS ({len(rs)})", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            idx = int(ch) - 1
            _region_detail(rs[idx])
        except Exception:
            pass

def _region_detail(r):
    clear()
    rl = r.get("recommended_level", ["?", "?"])
    lines = [
        color(r["name"], C.CYAN + C.BOLD),
        f" Kingdom       : {r['kingdom']}",
        f" Biome         : {r['biome']}",
        f" Danger        : {danger_label(r['danger'])} ({r['danger']}/10)",
        f" Rec. Level    : {rl[0]} - {rl[1]}",
        "",
        color("Adventure di region ini akan tersedia di Phase 9.", C.YELLOW),
    ]
    print(box("REGION DETAIL", lines))
    pause()
