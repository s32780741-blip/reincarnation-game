"""UI untuk Mining & Gathering (dipilih dari region)."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from mining import mining_nodes_in, mine
from gathering import gathering_nodes_in, gather
from items import get_item
from world import get_region


def resource_menu(character_id):
    while True:
        char = db.get_character(character_id)
        # Ambil region dari kota
        from cities import get_city
        city = get_city(char["location"])
        if not city:
            clear()
            print(box("RESOURCE", [" Tidak ada region di lokasi ini."]))
            pause(); return

        clear()
        lines = [
            f" Kota   : {city['name']}",
            f" Kingdom: {city['kingdom']}",
            "",
            " 1. Mining  (butuh pickaxe)",
            " 2. Gathering (butuh sickle/axe)",
            " 0. Kembali",
        ]
        print(box("RESOURCE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _pick_region_mining(character_id, city["kingdom"])
        elif ch == "2":
            _pick_region_gathering(character_id, city["kingdom"])


def _regions_of_kingdom(kingdom_id):
    from world import load_regions
    return [r for r in load_regions() if r["kingdom"] == kingdom_id]


def _pick_region_mining(character_id, kingdom):
    regions = _regions_of_kingdom(kingdom)
    clear()
    lines = []
    for i, r in enumerate(regions, 1):
        n = len(mining_nodes_in(r["id"]))
        lines.append(f" [{i}] {r['name']:<22} ({n} mining nodes)")
    lines.append(""); lines.append(" 0. Batal")
    print(box("PILIH REGION — MINING", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        r = regions[int(ch) - 1]
        _mine_session(character_id, r)
    except Exception:
        pass


def _mine_session(character_id, region):
    while True:
        nodes = mining_nodes_in(region["id"])
        if not nodes:
            clear()
            print(box("MINING", [f" Tidak ada node mining di {region['name']}."]))
            pause(); return
        char = db.get_character(character_id)
        clear()
        lines = [
            f" Region  : {region['name']}",
            f" Stamina : {char['stamina_current']}",
            "",
        ]
        for i, n in enumerate(nodes, 1):
            lines.append(f" [{i}] {n['name']:<20} T{n['tier']} ({n['stamina']}st)")
        lines.append(""); lines.append(" 0. Selesai")
        print(box("MINING", lines))
        ch = prompt("> ")
        if ch == "0":
            db.update_character(character_id)
            return
        try:
            node = nodes[int(ch) - 1]
            res = mine(character_id, node)
            _show_result(res, "MINING")
        except Exception:
            pass


def _pick_region_gathering(character_id, kingdom):
    regions = _regions_of_kingdom(kingdom)
    clear()
    lines = []
    for i, r in enumerate(regions, 1):
        n = len(gathering_nodes_in(r["id"]))
        lines.append(f" [{i}] {r['name']:<22} ({n} gather nodes)")
    lines.append(""); lines.append(" 0. Batal")
    print(box("PILIH REGION — GATHERING", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        r = regions[int(ch) - 1]
        _gather_session(character_id, r)
    except Exception:
        pass


def _gather_session(character_id, region):
    while True:
        nodes = gathering_nodes_in(region["id"])
        if not nodes:
            clear()
            print(box("GATHERING", [f" Tidak ada node di {region['name']}."]))
            pause(); return
        char = db.get_character(character_id)
        clear()
        lines = [
            f" Region  : {region['name']}",
            f" Stamina : {char['stamina_current']}",
            "",
        ]
        for i, n in enumerate(nodes, 1):
            lines.append(f" [{i}] {n['name']:<20} T{n['tier']} ({n['stamina']}st)")
        lines.append(""); lines.append(" 0. Selesai")
        print(box("GATHERING", lines))
        ch = prompt("> ")
        if ch == "0":
            db.update_character(character_id)
            return
        try:
            node = nodes[int(ch) - 1]
            res = gather(character_id, node)
            _show_result(res, "GATHERING")
        except Exception:
            pass


def _show_result(res, title):
    clear()
    if not res["ok"]:
        print(box(title, [color(f" ✗ {res['reason']}", C.RED)]))
        pause(); return
    lines = [
        color(f" ✓ {title} berhasil!", C.GREEN),
        f" +{res['exp']} EXP  (stamina -{res['stamina_cost']})",
        "",
        color("Hasil:", C.YELLOW),
    ]
    if res["drops"]:
        for d in res["drops"]:
            item = get_item(d["id"]) or {}
            lines.append(f"  • {item.get('name', d['id'])} x{d['amount']}")
    else:
        lines.append(color("  (tidak dapat apa-apa kali ini)", C.GRAY))
    print(box(title, lines))
    pause()
