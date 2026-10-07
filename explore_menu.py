"""Exploration UI — random events, treasure, hidden locations."""
import random, time
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from world import load_regions, get_region
from weather import current_weather_for_region, weather_line, weather_modifier
from daynight import phase_label, phase_icon, is_night
from exploration import explore_once, check_world_boss
from events import roll_event, roll_treasure
from treasure import roll_hidden_location, claim_treasure
from items import get_item


def explore_menu(character_id):
    while True:
        clear()
        print(box("EXPLORATION", [
            " 1. Jelajahi region",
            " 2. Lihat cuaca & waktu",
            " 0. Kembali",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _pick_region(character_id)
        elif ch == "2":
            _show_weather_time(character_id)


def _pick_region(character_id):
    char = db.get_character(character_id)
    from cities import get_city
    city = get_city(char["location"])
    kingdom = city["kingdom"] if city else "neutral"

    regions = [r for r in load_regions() if r["kingdom"] in (kingdom, "neutral")]
    clear()
    lines = []
    for i, r in enumerate(regions, 1):
        w = current_weather_for_region(r["id"])
        wstr = f"{w.get('icon','')} {w.get('name','')}" if w else ""
        rl = r.get("recommended_level", ["?", "?"])
        lines.append(f" [{i:2d}] {r['name']:<22} Lv{rl[0]}-{rl[1]}  {wstr}")
    lines.append(""); lines.append(" 0. Batal")
    print(box("PILIH REGION", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        region = regions[int(ch) - 1]
        _explore_session(character_id, region)
    except Exception:
        pass


def _explore_session(character_id, region):
    while True:
        char = db.get_character(character_id)
        weather = current_weather_for_region(region["id"])
        clear()
        lines = [
            color(f" {region['name']}", C.CYAN + C.BOLD),
            f" Biome  : {region.get('biome', '?')}",
            f" Danger : {region.get('danger', 1)}/10",
            f" Cuaca  : {weather_line(weather)}",
            f" Waktu  : {phase_icon()} {phase_label()}",
            f" HP     : {char['hp_current']}  ST: {char['stamina_current']}",
            "",
            " 1. Explore",
            " 2. Cari treasure",
            " 3. Cari hidden location",
            " 4. Selesai",
        ]
        print(box("EXPLORE", lines))
        ch = prompt("> ")
        if ch == "4":
            db.update_character(character_id)
            return
        elif ch == "1":
            _do_explore(character_id, region)
        elif ch == "2":
            _search_treasure(character_id, region)
        elif ch == "3":
            _search_hidden(character_id, region)


def _do_explore(character_id, region):
    # Cek world boss dulu
    wb = check_world_boss(character_id, region["id"])
    if wb:
        _handle_world_boss(character_id, wb)
        return

    result = explore_once(character_id, region["id"])
    t = result["type"]
    weather = result.get("weather")

    if t == "nothing":
        clear()
        print(box("EXPLORATION", [
            weather_line(weather) if weather else "",
            "",
            f" {result['msg']}",
        ]))
        pause()
        return

    if t == "event":
        _handle_event(character_id, result["event"], region, weather)


def _handle_event(character_id, event, region, weather):
    etype = event.get("type")
    clear()
    print(box("EVENT", [
        color(f" {event['name']}", C.YELLOW + C.BOLD),
        "",
        f" {event['desc']}",
    ]))
    pause()

    if etype == "merchant":
        _ev_merchant(character_id)
    elif etype == "traveler":
        _ev_traveler(character_id, event)
    elif etype == "ambush":
        _ev_ambush(character_id, region, weather)
    elif etype == "treasure":
        _ev_treasure(character_id, "small")
    elif etype == "treasure_element":
        _ev_element_core(character_id)
    elif etype == "rare_monster":
        _ev_rare_monster(character_id, region)
    elif etype == "rescue":
        _ev_rescue(character_id)
    elif etype == "mystery":
        _ev_mystery(character_id, event)
    elif etype == "social":
        _ev_social(character_id, event)
    elif etype == "resource":
        _ev_resource(character_id)
    elif etype == "location":
        _ev_location(character_id, region)
    elif etype == "dungeon":
        _ev_dungeon(character_id, region)
    elif etype == "weather":
        _ev_weather(character_id, weather)
    elif etype == "world_boss":
        _ev_world_boss_placeholder(character_id)
    else:
        clear()
        print(box("EVENT", [" Tidak ada yang terjadi."]))
        pause()


# ============================================================
# EVENT HANDLERS
# ============================================================
def _ev_merchant(character_id):
    clear()
    print(box("MERCHANT", [
        " Pedagang keliling menawarkan barang langka.",
        "",
        color(" (Gunakan Market di kota untuk jual beli penuh.)", C.YELLOW),
    ]))
    pause()


def _ev_traveler(character_id):
    clear()
    char = db.get_character(character_id)
    reward_silver = random.randint(15, 50)
    db.update_character(character_id, silver=char["silver"] + reward_silver)
    print(box("TRAVELER", [
        " Musafir berterima kasih atas bantuanmu.",
        "",
        color(f" +{reward_silver} Silver", C.GREEN),
    ]))
    pause()


def _ev_ambush(character_id, region, weather):
    # Combat
    from hunt import _spawn_combat
    clear()
    print(box("AMBUSH", [
        color(" Kamu disergap!", C.RED + C.BOLD),
        "",
        " Bersiap bertarung!",
    ]))
    pause()
    _spawn_combat(character_id, region)


def _ev_treasure(character_id, table_name):
    from events import roll_treasure
    loot = roll_treasure(table_name)
    _show_loot_and_apply(character_id, loot, "TREASURE")


def _ev_element_core(character_id):
    from items import load_items
    cores = [it for it in load_items() if it.get("type") == "element_core"]
    if not cores:
        return
    core = random.choice(cores)
    db.add_item(character_id, core["id"], 1)
    clear()
    print(box("ELEMENT CORE", [
        color(f" Kamu menemukan {core['name']}!", C.MAGENTA + C.BOLD),
        "",
        color(" Gunakan untuk crafting atau pelajari affinity.", C.GRAY),
    ]))
    pause()


def _ev_rare_monster(character_id, region):
    from monsters import load_monsters, scale_monster
    from combat import start_combat
    rares = [m for m in load_monsters() if m.get("rank") in ("rare", "epic", "mythic")]
    if not rares:
        return
    char = db.get_character(character_id)
    target = random.choice(rares)
    clear()
    print(box("RARE MONSTER", [
        color(f" {target['name']} muncul!", C.MAGENTA + C.BOLD),
    ]))
    pause()
    start_combat(character_id, target)


def _ev_rescue(character_id):
    clear()
    char = db.get_character(character_id)
    reward_silver = random.randint(20, 60)
    reward_exp = random.randint(20, 50)
    db.update_character(character_id, silver=char["silver"] + reward_silver)
    from character import grant_exp
    grant_exp(character_id, reward_exp)
    print(box("RESCUE", [
        " Kamu menyelamatkan orang yang membutuhkan.",
        "",
        color(f" +{reward_silver} Silver  +{reward_exp} EXP", C.GREEN),
        "",
        " Reputasi baik meningkat.",
    ]))
    pause()


def _ev_mystery(character_id, event):
    clear()
    lines = [
        color(f" {event['name']}", C.MAGENTA + C.BOLD),
        "",
        f" {event['desc']}",
        "",
        color(" Ada sesuatu yang tidak biasa...", C.GRAY),
    ]
    # 30% bonus random
    if random.random() < 0.3:
        from character import grant_exp
        exp = random.randint(20, 60)
        grant_exp(character_id, exp)
        lines.append("")
        lines.append(color(f" +{exp} EXP", C.GREEN))
    print(box("MYSTERY", lines))
    pause()


def _ev_social(character_id, event):
    clear()
    print(box("SOCIAL", [
        f" {event['desc']}",
        "",
        " Kau berbincang sebentar dengan mereka.",
        "",
        color(" Reputasi lokal +1", C.GREEN),
    ]))
    pause()


def _ev_resource(character_id):
    from items import load_items
    resources = [it for it in load_items() if it.get("type") == "material"]
    if not resources:
        return
    r = random.choice(resources)
    amt = random.randint(1, 3)
    db.add_item(character_id, r["id"], amt)
    clear()
    print(box("RESOURCE", [
        f" Kamu menemukan {r['name']} x{amt}",
    ]))
    pause()


def _ev_location(character_id, region):
    clear()
    print(box("ANCIENT RUINS", [
        " Reruntuhan kuno muncul dari balik pepohonan.",
        "",
        " 1. Masuk",
        " 2. Lewati",
    ]))
    ch = prompt("> ")
    if ch != "1":
        return
    # 40% jadi dungeon, 60% treasure
    if random.random() < 0.4:
        _start_dungeon(character_id, region)
    else:
        loot = roll_treasure("medium")
        _show_loot_and_apply(character_id, loot, "RUINS TREASURE")


def _ev_dungeon(character_id, region):
    clear()
    print(box("HIDDEN DUNGEON", [
        color(" Pintu dungeon tersembunyi terbuka!", C.MAGENTA + C.BOLD),
        "",
        " 1. Masuk",
        " 2. Lewati",
    ]))
    ch = prompt("> ")
    if ch != "1":
        return
    _start_dungeon(character_id, region)


def _ev_weather(character_id, weather):
    clear()
    print(box("WEATHER CHANGE", [
        " Cuaca berubah secara dramatis!",
        "",
        weather_line(weather) if weather else "",
    ]))
    pause()


def _ev_world_boss_placeholder(character_id):
    clear()
    print(box("BOSS ENCOUNTER", [
        color(" Sosok raksasa muncul di kejauhan...", C.RED + C.BOLD),
        "",
        color(" (World boss di-handle lewat roll_boss_encounter)", C.GRAY),
    ]))
    pause()


# ============================================================
# TREASURE / HIDDEN
# ============================================================
def _search_treasure(character_id, region):
    from events import roll_treasure
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    luck = stats.get("luck", 5)
    perception = stats.get("perception", 5)

    # Chance
    base = 0.20 + luck * 0.005 + perception * 0.005
    if random.random() > base:
        clear()
        print(box("SEARCH", [" Tidak ditemukan treasure.", "", " Coba lagi."]))
        pause()
        return
    table = random.choice(["small", "small", "medium"])
    loot = roll_treasure(table)
    _show_loot_and_apply(character_id, loot, "TREASURE FOUND")


def _search_hidden(character_id, region):
    from treasure import roll_hidden_location
    stats = db.get_stats(character_id)
    perception = stats.get("perception", 5)
    loc = roll_hidden_location(region.get("biome", "plains"), perception)
    if not loc or random.random() > 0.35:
        clear()
        print(box("SEARCH", [" Tidak ada hidden location di sekitar."]))
        pause()
        return
    clear()
    print(box("HIDDEN LOCATION", [
        color(f" {loc['name']}", C.MAGENTA + C.BOLD),
        f" Rarity: {loc['rarity']}",
        "",
        f" {loc['desc']}",
        "",
        " 1. Buka",
        " 0. Lewati",
    ]))
    if prompt("> ") != "1":
        return
    loot = roll_treasure(loc.get("loot_table", "medium"))
    _show_loot_and_apply(character_id, loot, "HIDDEN LOOT")


# ============================================================
# DUNGEON
# ============================================================
def _start_dungeon(character_id, region):
    from dungeon import generate_dungeon, save_dungeon_progress, load_dungeon_progress
    char = db.get_character(character_id)
    existing = load_dungeon_progress(character_id)
    if existing:
        clear()
        print(box("DUNGEON", [
            f" Ada dungeon aktif: {existing['name']}",
            f" Floor: {existing['current_floor']}/{existing['total_floors']}",
            "",
            " 1. Lanjutkan",
            " 2. Buat baru",
            " 0. Batal",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return
        if ch == "1":
            _dungeon_run(character_id, existing)
            return
        if ch == "2":
            from dungeon import clear_dungeon_progress
            clear_dungeon_progress(character_id)

    biome = region.get("biome", "plains")
    dungeon = generate_dungeon(biome, char["level"])
    if not dungeon:
        clear()
        print(box("DUNGEON", [" Tidak ada dungeon yang cocok."]))
        pause()
        return
    save_dungeon_progress(character_id, dungeon)
    clear()
    print(box("DUNGEON GENERATED", [
        color(f" {dungeon['name']}", C.CYAN + C.BOLD),
        f" Floors: {dungeon['total_floors']}",
        "",
        color(dungeon["theme"]["desc"], C.GRAY),
        "",
        " 1. Masuk",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    _dungeon_run(character_id, dungeon)


def _dungeon_run(character_id, dungeon):
    from dungeon import (
        pick_monster_for_floor, pick_boss_for_dungeon,
        floor_type_label, save_dungeon_progress, clear_dungeon_progress
    )
    from combat import start_combat
    from events import roll_treasure

    while True:
        f = dungeon["current_floor"]
        total = dungeon["total_floors"]
        floor_data = dungeon["floors"][f - 1]
        ftype = floor_data["type"]

        clear()
        lines = [
            color(f" {dungeon['name']}", C.CYAN + C.BOLD),
            f" Floor  : {f}/{total}",
            f" Room   : {floor_type_label(ftype)}",
            "",
            f" HP  : {db.get_character(character_id)['hp_current']}",
        ]
        print(box("DUNGEON", lines))
        print(box("RUANGAN", [
            f" Kamu masuk ke {floor_type_label(ftype)}.",
            "",
            " 1. Lanjut",
            " 2. Keluar dungeon",
        ]))
        ch = prompt("> ")
        if ch == "2":
            save_dungeon_progress(character_id, dungeon)
            clear()
            print(box("DUNGEON", [" Kamu keluar dari dungeon."]))
            pause()
            return

        # Handle floor
        if ftype == "combat":
            m = pick_monster_for_floor(dungeon, f)
            if m:
                from monsters import scale_monster
                scaled = scale_monster(m, level_offset=max(0, dungeon["player_level"] - m["level"]))
                result = start_combat(character_id, scaled)
                if result == "lose":
                    clear_dungeon_progress(character_id)
                    return
        elif ftype == "treasure":
            loot = roll_treasure(dungeon["theme"].get("treasure_table", "medium"))
            _show_loot_and_apply(character_id, loot, "TREASURE")
        elif ftype == "trap":
            _trap_room(character_id)
        elif ftype == "puzzle":
            _puzzle_room(character_id)
        elif ftype == "rest":
            _rest_room(character_id)
        elif ftype == "boss":
            boss_m = pick_boss_for_dungeon(dungeon)
            if boss_m:
                from monsters import scale_monster
                scaled = scale_monster(boss_m, level_offset=max(0, dungeon["player_level"] - boss_m["level"]))
                result = start_combat(character_id, scaled)
                if result == "lose":
                    clear_dungeon_progress(character_id)
                    return
            clear()
            print(box("DUNGEON CLEARED!", [
                color(f" {dungeon['name']} diselesaikan!", C.GREEN + C.BOLD),
                "",
                " Bonus reward diberikan.",
            ]))
            # Bonus reward
            loot = roll_treasure(dungeon["theme"].get("treasure_table", "medium"))
            loot["silver"] = loot.get("silver", 0) + 200
            loot["gold"] = loot.get("gold", 0) + 2
            _show_loot_and_apply(character_id, loot, "DUNGEON BONUS")
            clear_dungeon_progress(character_id)
            # Achievement
            try:
                from achievements import check_all
                check_all(character_id, silent=False)
            except Exception:
                pass
            return

        floor_data["cleared"] = True
        dungeon["current_floor"] = f + 1
        save_dungeon_progress(character_id, dungeon)

        if f + 1 > total:
            break


def _trap_room(character_id):
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    danger = max(1, 20 - stats.get("agility", 5) - stats.get("perception", 5))
    if random.randint(1, 20) < danger:
        dmg = random.randint(20, 60) + char["level"] * 2
        new_hp = max(1, char["hp_current"] - dmg)
        db.update_character(character_id, hp_current=new_hp)
        clear()
        print(box("TRAP!", [
            color(f" Jebakan aktif! Kamu terkena {dmg} damage.", C.RED),
            f" HP sekarang: {new_hp}",
        ]))
        pause()
    else:
        clear()
        print(box("TRAP", [" Kamu berhasil menghindari jebakan."]))
        pause()


def _puzzle_room(character_id):
    stats = db.get_stats(character_id)
    intel = stats.get("intelligence", 5)
    roll = random.randint(1, 20) + intel
    if roll >= 18:
        clear()
        print(box("PUZZLE", [
            color(" Kamu memecahkan puzzle!", C.GREEN),
            "",
            " Hadiah: harta kecil.",
        ]))
        loot = roll_treasure("small")
        _show_loot_and_apply(character_id, loot, "PUZZLE")
    else:
        clear()
        print(box("PUZZLE", [" Kau gagal memecahkan puzzle. Tidak ada hadiah."]))
        pause()


def _rest_room(character_id):
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    from character import max_hp, max_mp
    mhp = max_hp(stats, char["level"])
    mmp = max_mp(stats, char["level"])
    heal = mhp // 4
    db.update_character(character_id,
                        hp_current=min(mhp, char["hp_current"] + heal),
                        mp_current=min(mmp, char["mp_current"] + heal // 2))
    clear()
    print(box("REST", [
        " Kamu beristirahat sejenak.",
        "",
        color(f" +{heal} HP", C.GREEN),
    ]))
    pause()


# ============================================================
# WORLD BOSS
# ============================================================
def _handle_world_boss(character_id, boss):
    clear()
    print(box("WORLD BOSS!", [
        color(f" {boss.get('title','World Boss')}", C.RED + C.BOLD),
        "",
        f" {boss.get('alert','')}",
        f" Level: {boss['level']}",
        "",
        " 1. Hadapi",
        " 0. Kabur",
    ]))
    if prompt("> ") != "1":
        return
    from monsters import get_monster
    m = get_monster(boss["monster"])
    if not m:
        return
    from monsters import scale_monster
    scaled = scale_monster(m, level_offset=max(0, boss["level"] - m["level"]))
    from combat import start_combat
    result = start_combat(character_id, scaled)
    if result == "win":
        from world_boss import grant_boss_reward
        rw = grant_boss_reward(character_id, boss)
        clear()
        print(box("WORLD BOSS DEFEATED!", [
            color(" Kamu mengalahkan world boss!", C.YELLOW + C.BOLD),
            "",
            f" Silver: +{rw.get('silver', 0)}",
            f" Gold  : +{rw.get('gold', 0)}",
            f" EXP   : +{rw.get('exp', 0)}",
        ]))
        pause()


# ============================================================
# UTILITIES
# ============================================================
def _show_loot_and_apply(character_id, loot, title):
    from treasure import claim_treasure
    claim_treasure(character_id, loot)
    clear()
    lines = [color(f" {title}", C.YELLOW + C.BOLD), ""]
    if loot.get("silver"):
        lines.append(f" Silver: +{loot['silver']}")
    if loot.get("gold"):
        lines.append(f" Gold  : +{loot['gold']}")
    for item in loot.get("items", []):
        it = get_item(item["id"]) or {}
        lines.append(f" Item  : {it.get('name', item['id'])} x{item['amount']}")
    if not any([loot.get("silver"), loot.get("gold"), loot.get("items")]):
        lines.append(color(" (tidak ada yang berharga)", C.GRAY))
    print(box("LOOT", lines))
    pause()


def _show_weather_time(character_id):
    char = db.get_character(character_id)
    from cities import get_city
    city = get_city(char["location"])
    if not city:
        return
    regions = [r for r in load_regions() if r["kingdom"] == city["kingdom"]]
    clear()
    lines = [
        f" Waktu : {phase_icon()} {phase_label()}",
        "",
        color("CUACA PER REGION:", C.YELLOW),
    ]
    for r in regions[:8]:
        w = current_weather_for_region(r["id"])
        lines.append(f"  {r['name']:<22}: {weather_line(w)}")
    print(box("WEATHER", lines))
    pause()
