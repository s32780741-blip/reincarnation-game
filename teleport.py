"""Teleport — Royal & Underground routes."""
import random, time
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from cities import get_city, city_name

# Biaya teleport
ROYAL_BASE_FEE_GOLD = 3
UNDERGROUND_BASE_FEE_GOLD = 5
UNDERGROUND_RISK = 0.20  # 20% chance of ambush

def _lang():
    return settings.get("language", "id")

def can_use_royal(character_id):
    """Cek izin kerajaan."""
    val = db.get_world_state(character_id, "royal_teleport_permit", "0")
    return val == "1"

def grant_royal_permit(character_id):
    db.set_world_state(character_id, "royal_teleport_permit", "1")

def teleport_menu(character_id):
    char = db.get_character(character_id)
    if not char:
        return
    while True:
        clear()
        from cities import city_name
        lines = [
            f" Lokasi sekarang: {city_name(char['location'])}",
            "",
            " 1. Royal Teleport",
            " 2. Underground Route",
            " 3. Beli izin Royal (10 Gold)",
            " 0. Kembali",
        ]
        print(box("TELEPORT", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _royal_route(character_id)
        elif ch == "2":
            _underground_route(character_id)
        elif ch == "3":
            if char["gold"] >= 10:
                db.update_character(character_id, gold=char["gold"] - 10)
                grant_royal_permit(character_id)
                print(color(" ✓ Izin Royal Teleport diperoleh!", C.GREEN))
            else:
                print(color(" Gold tidak cukup.", C.RED))
            pause()
        else:
            print(color(" Invalid.", C.RED)); pause()

def _pick_destination(character_id, exclude_current=True):
    from cities import load_cities
    char = db.get_character(character_id)
    cities = load_cities()
    if exclude_current:
        cities = [c for c in cities if c["id"] != char["location"]]
    clear()
    lines = []
    for i, c in enumerate(cities, 1):
        lines.append(f" [{i:2d}] {c['name']:<14} ({c['kingdom']})  D:{c.get('danger',1)}")
    lines.append("")
    lines.append(" 0. Batal")
    print(box("PILIH TUJUAN", lines))
    ch = prompt("> ")
    if ch == "0":
        return None
    try:
        idx = int(ch) - 1
        if 0 <= idx < len(cities):
            return cities[idx]
    except ValueError:
        pass
    return None

def _royal_route(character_id):
    if not can_use_royal(character_id):
        print(color(" ✗ Kamu belum punya izin Royal Teleport.", C.RED))
        print(color("   Beli izin atau gunakan Underground Route.", C.YELLOW))
        pause()
        return
    char = db.get_character(character_id)
    dest = _pick_destination(character_id)
    if not dest:
        return
    from world import travel_time
    time_min = travel_time(char["location"], dest["id"])
    fee = ROYAL_BASE_FEE_GOLD

    clear()
    print(box("ROYAL TELEPORT", [
        f" Dari  : {city_name(char['location'])}",
        f" Ke    : {dest['name']}",
        f" Waktu : {time_min} menit",
        f" Biaya : {fee} Gold",
        "",
        " 1. Konfirmasi",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    if char["gold"] < fee:
        print(color(" Gold tidak cukup.", C.RED)); pause(); return
    db.update_character(character_id, gold=char["gold"] - fee, location=dest["id"])

    # Loading singkat
    import loading
    try:
        loading.show(total_time=1.8, message=f"Traveling to {dest['name']}...")
    except KeyboardInterrupt:
        pass

    print(color(f"\n ✓ Kamu tiba di {dest['name']}.", C.GREEN))
    print(color(f"   {dest.get('desc','')}", C.GRAY))
    db.update_character(character_id)  # autosave touch
    pause()

def _underground_route(character_id):
    char = db.get_character(character_id)
    dest = _pick_destination(character_id)
    if not dest:
        return
    from world import travel_time
    time_min = int(travel_time(char["location"], dest["id"]) * 0.6)
    fee = UNDERGROUND_BASE_FEE_GOLD

    clear()
    print(box("UNDERGROUND ROUTE", [
        f" Dari  : {city_name(char['location'])}",
        f" Ke    : {dest['name']}",
        f" Waktu : {time_min} menit",
        f" Biaya : {fee} Gold",
        "",
        color("⚠ Risiko: kemungkinan diserang di jalan.", C.YELLOW),
        "",
        " 1. Lanjutkan",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    if char["gold"] < fee:
        print(color(" Gold tidak cukup.", C.RED)); pause(); return

    db.update_character(character_id, gold=char["gold"] - fee)

    # Risk check
    if random.random() < UNDERGROUND_RISK:
        print()
        print(color(" 🗡 AMBUSH! Kamu diserang di jalan bawah tanah!", C.RED + C.BOLD))
        # Phase 4 akan integrasi combat penuh. Untuk sekarang: HP loss
        dmg = random.randint(10, 40) + char["level"]
        stats = db.get_stats(character_id)
        from character import max_hp
        mhp = max_hp(stats, char["level"])
        new_hp = max(1, char["hp_current"] - dmg)
        db.update_character(character_id, hp_current=new_hp, location=dest["id"])
        print(color(f" Kamu kehilangan {dmg} HP. HP sekarang: {new_hp}/{mhp}", C.YELLOW))
        print(color(f" Kamu berhasil kabur ke {dest['name']}.", C.GREEN))
        pause()
        return

    # Aman
    db.update_character(character_id, location=dest["id"])
    import loading
    try:
        loading.show(total_time=1.5, message="Traveling through dark tunnels...")
    except KeyboardInterrupt:
        pass
    print(color(f"\n ✓ Kamu tiba di {dest['name']}.", C.GREEN))
    print(color(f"   {dest.get('desc','')}", C.GRAY))
    pause()
