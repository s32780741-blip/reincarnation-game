"""Post-game menu."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from postgame import (
    load_postgame, is_postgame_unlocked,
    endless_start_floor, endless_best_floor, endless_next_floor,
    endless_reward, endless_update_floor, endless_reset,
    arena_get_wave, arena_next_wave, arena_clear_wave, arena_complete_reward,
    arena_reset,
    boss_rush_index, boss_rush_next, boss_rush_advance,
    boss_rush_complete_reward, boss_rush_reset, boss_rush_total,
)


def postgame_menu(character_id):
    if not is_postgame_unlocked(character_id):
        clear()
        print(box("POST-GAME", [
            color(" Terkunci.", C.RED),
            "",
            " Selesaikan main story untuk membuka konten post-game.",
        ]))
        pause()
        return

    while True:
        clear()
        from ng_plus import get_ng_plus_level
        ng = get_ng_plus_level(character_id)
        lines = [
            f" NG+ Level : {ng}",
            f" Endless   : Floor {endless_best_floor(character_id)} (best)",
            f" Arena     : Wave {arena_get_wave(character_id)}/10",
            f" Boss Rush : {boss_rush_index(character_id)}/{boss_rush_total()}",
            "",
            " 1. The Endless Spiral",
            " 2. Champion's Arena",
            " 3. Rush of Titans",
            " 4. Reset progress (Endless)",
            " 0. Kembali",
        ]
        print(box("POST-GAME", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _endless(character_id)
        elif ch == "2":
            _arena(character_id)
        elif ch == "3":
            _boss_rush(character_id)
        elif ch == "4":
            endless_reset(character_id)
            print(color(" Endless progress reset.", C.YELLOW))
            pause()


def _endless(character_id):
    while True:
        cfg = load_postgame().get("endless_dungeon", {})
        cur = endless_start_floor(character_id)
        best = endless_best_floor(character_id)
        clear()
        lines = [
            color(f" {cfg.get('name', 'Endless Spiral')}", C.MAGENTA + C.BOLD),
            "",
            color(cfg.get("desc", ""), C.GRAY),
            "",
            f" Current Floor : {cur}",
            f" Best Floor    : {best}",
            "",
            " 1. Lanjut ke floor berikutnya",
            " 2. Reset progress",
            " 0. Keluar",
        ]
        print(box("ENDLESS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _endless_fight(character_id)
        elif ch == "2":
            endless_reset(character_id)
            print(color(" Endless reset.", C.YELLOW))
            pause()


def _endless_fight(character_id):
    from combat import start_combat
    cur = endless_start_floor(character_id)
    monster = endless_next_floor(character_id, cur)
    if not monster:
        clear()
        print(box("ENDLESS", [" Tidak bisa spawn monster."]))
        pause()
        return

    result = start_combat(character_id, monster)
    if result == "win":
        next_floor = cur + 1
        endless_update_floor(character_id, next_floor)
        rw = endless_reward(character_id, next_floor)
        clear()
        print(box("FLOOR CLEARED", [
            color(f" Floor {next_floor} selesai!", C.GREEN + C.BOLD),
            "",
            f" Silver: +{rw['silver']}",
            f" Gold  : +{rw['gold']}",
            f" EXP   : +{rw['exp']}",
        ]))
        pause()
    else:
        endless_reset(character_id)
        clear()
        print(box("ENDLESS OVER", [
            color(" Perjalananmu di Endless Spiral berakhir.", C.RED),
            f" Tercapai floor: {cur}",
            "",
            " Progress reset. Coba lagi untuk mengalahkan rekor.",
        ]))
        pause()


def _arena(character_id):
    while True:
        wave_idx = arena_get_wave(character_id)
        cfg = load_postgame().get("arena", {})
        clear()
        lines = [
            color(f" {cfg.get('name', 'Arena')}", C.YELLOW + C.BOLD),
            "",
            f" Wave: {wave_idx}/10",
            "",
            " 1. Lanjut bertarung",
            " 2. Reset arena",
            " 0. Keluar",
        ]
        print(box("ARENA", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _arena_next(character_id)
        elif ch == "2":
            arena_reset(character_id)
            print(color(" Arena reset.", C.YELLOW))
            pause()


def _arena_next(character_id):
    from combat import start_combat
    wave = arena_next_wave(character_id)
    if not wave:
        # Complete!
        arena_complete_reward(character_id)
        clear()
        print(box("ARENA CLEARED", [
            color(" ★ KAU MENYELESAIKAN ARENA!", C.YELLOW + C.BOLD),
            "",
            " Reward besar diterima.",
        ]))
        pause()
        return

    clear()
    print(box("ARENA WAVE", [
        color(wave["name"], C.YELLOW + C.BOLD),
        "",
        f" Musuh: {', '.join(wave['monsters'])}",
        f" Level bonus: +{wave.get('level_bonus', 0)}",
    ]))
    pause(" Tekan Enter untuk bertarung...")

    from monsters import get_monster, scale_monster
    for mid in wave["monsters"]:
        base = get_monster(mid)
        if not base:
            continue
        scaled = scale_monster(base, level_offset=wave.get("level_bonus", 0))
        result = start_combat(character_id, scaled)
        if result == "lose":
            arena_reset(character_id)
            clear()
            print(box("ARENA FAILED", [
                color(" Kau gugur di arena.", C.RED),
                f" Wave tercapai: {arena_get_wave(character_id)}",
            ]))
            pause()
            return
    arena_clear_wave(character_id)
    print(color(f" ✓ Wave {arena_get_wave(character_id)} selesai!", C.GREEN))
    pause()


def _boss_rush(character_id):
    while True:
        idx = boss_rush_index(character_id)
        total = boss_rush_total()
        cfg = load_postgame().get("boss_rush", {})
        clear()
        lines = [
            color(f" {cfg.get('name', 'Boss Rush')}", C.RED + C.BOLD),
            "",
            f" Progress: {idx}/{total}",
            "",
            " 1. Hadapi boss berikutnya",
            " 2. Reset progress",
            " 0. Keluar",
        ]
        print(box("BOSS RUSH", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _boss_rush_fight(character_id)
        elif ch == "2":
            boss_rush_reset(character_id)
            print(color(" Boss rush reset.", C.YELLOW))
            pause()


def _boss_rush_fight(character_id):
    boss = boss_rush_next(character_id)
    if not boss:
        boss_rush_complete_reward(character_id)
        clear()
        print(box("BOSS RUSH CLEARED", [
            color(" ★ SEMUA BOSS DIKALAHKAN!", C.YELLOW + C.BOLD),
            "",
            " Kau adalah legenda.",
        ]))
        pause()
        return

    clear()
    print(box("BOSS RUSH", [
        color(f" {boss.get('title','Boss')}", C.RED + C.BOLD),
        "",
        f" Level: {boss['level']}",
        "",
        " 1. Hadapi",
        " 0. Kabur",
    ]))
    if prompt("> ") != "1":
        return

    from monsters import get_monster, scale_monster
    m = get_monster(boss["monster"])
    if not m:
        return
    scaled = scale_monster(m, level_offset=max(0, boss["level"] - m["level"]))
    from combat import start_combat
    result = start_combat(character_id, scaled)
    if result == "win":
        boss_rush_advance(character_id)
        print(color(f" ✓ Boss dikalahkan! Progress: {boss_rush_index(character_id)}/{boss_rush_total()}", C.GREEN))
        pause()
    else:
        boss_rush_reset(character_id)
        print(color(" Boss rush gagal. Reset.", C.RED))
        pause()
