"""Hunt / Adventure — encounter monster di region."""
import random, time
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from world import load_regions, get_region, random_travel_event
from cities import get_city, danger_label
from monsters import pick_random_monster, scale_monster
from combat import start_combat

def _lang():
    return settings.get("language", "id")

def hunt_menu(character_id):
    char = db.get_character(character_id)
    if not char:
        return
    while True:
        clear()
        lines = [
            f" Lokasi: {char['location']}",
            f" Level : {char['level']}",
            "",
            " 1. Cari monster di region sekitar",
            " 2. Lihat semua region",
            " 3. Berburu target spesifik (by rank)",
            " 0. Kembali",
        ]
        print(box("HUNT", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _hunt_region(character_id)
        elif ch == "2":
            _list_regions(character_id)
        elif ch == "3":
            _hunt_by_rank(character_id)

def _region_pick(character_id):
    char = db.get_character(character_id)
    city = get_city(char["location"])
    if not city:
        return None
    regions = [r for r in load_regions() if r["kingdom"] == city["kingdom"]]
    if not regions:
        regions = load_regions()
    clear()
    lines = []
    for i, r in enumerate(regions, 1):
        rl = r.get("recommended_level", ["?", "?"])
        danger = r.get("danger", 1)
        warn = ""
        if char["level"] < rl[0]:
            warn = color(" ⚠ DANGER", C.RED)
        lines.append(f" [{i}] {r['name']:<22} Lv{rl[0]}-{rl[1]}  D:{danger}{warn}")
    lines.append("")
    lines.append(" 0. Kembali")
    print(box("PILIH REGION", lines))
    ch = prompt("> ")
    if ch == "0":
        return None
    try:
        idx = int(ch) - 1
        if 0 <= idx < len(regions):
            return regions[idx]
    except ValueError:
        pass
    return None

def _hunt_region(character_id):
    char = db.get_character(character_id)
    region = _region_pick(character_id)
    if not region:
        return
    rl = region.get("recommended_level", [1, 30])
    if char["level"] < rl[0]:
        clear()
        print(box("⚠ EXTREME DANGER", [
            f" Region: {region['name']}",
            f" Rekomendasi Level: {rl[0]}-{rl[1]}",
            f" Level kamu: {char['level']}",
            "",
            color(" Memasuki area ini bisa berakibat fatal.", C.RED),
            "",
            " 1. Tetap masuk",
            " 0. Kembali",
        ]))
        if prompt("> ") != "1":
            return

    # Session loop
    total_kills = 0
    while True:
        clear()
        lines = [
            color(f" {region['name']}", C.CYAN + C.BOLD),
            f" Danger: {danger_label(region.get('danger',1))}",
            f" Biome : {region.get('biome','?')}",
            "",
            f" Kills sejauh ini: {total_kills}",
            "",
            " 1. Explore",
            " 2. Search for monsters",
            " 3. Return to city",
        ]
        print(box("HUNTING", lines))
        ch = prompt("> ")
        if ch == "3":
            break
        elif ch == "1":
            r = _explore_event(character_id, region)
            if r == "combat":
                total_kills += 1
        elif ch == "2":
            _search_monster(character_id, region)
            total_kills += 1

    if total_kills:
        # Autosave
        db.update_character(character_id)
        clear()
        print(box("HUNT COMPLETE", [
            f" Region: {region['name']}",
            f" Monster dikalahkan: {total_kills}",
            "",
            color(" [✓] Progress tersimpan.", C.GREEN),
        ]))
        pause()

def _explore_event(character_id, region):
    ev = random_travel_event()
    t = ev["type"]
    if t == "encounter":
        clear()
        print(box("ENCOUNTER", [f" {ev['text']}"]))
        pause()
        return _spawn_combat(character_id, region)
    elif t == "merchant":
        clear()
        print(box("MERCHANT", [
            f" {ev['text']}",
            "",
            color(" (Sistem jual-beli akan aktif di Phase 8.)", C.YELLOW),
        ]))
        pause()
        return "merchant"
    elif t == "traveler":
        clear()
        print(box("TRAVELER", [
            f" {ev['text']}",
            "",
            color(" (Quest traveler akan aktif di Phase 5.)", C.YELLOW),
        ]))
        pause()
        return "traveler"
    elif t == "weather":
        clear()
        print(box("WEATHER", [
            f" {ev['text']}",
            "",
            " Kamu memutuskan menunggu badai reda.",
        ]))
        pause()
        return "weather"
    elif t == "treasure":
        clear()
        silver = random.randint(15, 60) + region.get("danger",1) * 10
        char = db.get_character(character_id)
        db.update_character(character_id, silver=char["silver"] + silver)
        print(box("TREASURE", [
            f" {ev['text']}",
            f" Kamu menemukan {silver} Silver!",
        ]))
        pause()
        return "treasure"
    else:
        clear()
        print(box("EXPLORE", [f" {ev['text']}"]))
        pause()
        return "none"

def _search_monster(character_id, region):
    return _spawn_combat(character_id, region)

def _spawn_combat(character_id, region):
    char = db.get_character(character_id)
    m = pick_random_monster(char["level"], region.get("danger", 1))
    if not m:
        clear()
        print(box("HUNT", [" Tidak ada monster ditemukan."]))
        pause()
        return "none"
    result = start_combat(character_id, m)
    return result

def _hunt_by_rank(character_id):
    from monsters import RANK_ORDER
    clear()
    lines = []
    for i, r in enumerate(RANK_ORDER, 1):
        lines.append(f" [{i:2d}] {r.replace('_',' ').title()}")
    lines.append("")
    lines.append(" 0. Kembali")
    print(box("PILIH RANK", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        rank = RANK_ORDER[int(ch) - 1]
    except Exception:
        return
    from monsters import load_monsters
    char = db.get_character(character_id)
    pool = [m for m in load_monsters() if m["rank"] == rank]
    if not pool:
        print(color(" Tidak ada monster rank ini.", C.YELLOW)); pause(); return
    # level terdekat
    pool.sort(key=lambda m: abs(m["level"] - char["level"]))
    target = pool[0]
    start_combat(character_id, target)

def _list_regions(character_id):
    clear()
    rs = load_regions()
    lines = []
    for i, r in enumerate(rs, 1):
        rl = r.get("recommended_level", ["?", "?"])
        lines.append(f" [{i:2d}] {r['name']:<22} [{r['kingdom']}] Lv{rl[0]}-{rl[1]}  D:{r.get('danger',1)}")
    print(box("ALL REGIONS", lines))
    pause()
