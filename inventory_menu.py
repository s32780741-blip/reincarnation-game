"""Inventory menu — Phase 4-7 lengkap.

Fitur:
- Lihat inventory (Phase 4)
- Item detail dengan quality & stats (Phase 7)
- Equipment view dengan total bonus (Phase 7)
- Equip item (Phase 7)
- Unequip slot (Phase 7)
- Weight / Carry capacity (Phase 4)
- Sell hint dari market (Phase 7)
"""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from items import get_item
from inventory import total_weight, carry_capacity, is_overweight
from equipment import (
    get_equipped, SLOTS, SLOT_LABEL, get_total_equipment_bonus,
    equip_item, unequip_slot, QUALITY_COLOR, QUALITY_ORDER,
    can_equip, item_effective_stat,
)


def _lang():
    return settings.get("language", "id")


def _qc(quality):
    """Quality color."""
    name = QUALITY_COLOR.get(quality, "white")
    return getattr(C, name.upper(), C.WHITE)


# ============================================================
# MAIN MENU
# ============================================================
def inventory_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        inv = db.get_inventory(character_id)
        w = total_weight(character_id)
        cap = carry_capacity(character_id)
        overweight = is_overweight(character_id)

        # Count equipped
        eq = get_equipped(character_id)
        eq_count = sum(1 for s in SLOTS if eq.get(s))

        clear()
        warn = color(" ⚠ OVERWEIGHT!", C.RED) if overweight else ""
        lines = [
            f" Berat  : {w}/{cap} kg{warn}",
            f" Item   : {len(inv)} jenis",
            f" Equip  : {eq_count}/{len(SLOTS)} slot",
            "",
            " 1. Lihat inventory",
            " 2. Equipment",
            " 3. Equip item",
            " 4. Unequip slot",
            " 5. Stat comparison",
            " 0. Kembali",
        ]
        print(box("INVENTORY", lines))
        ch = prompt("> ")

        if ch == "0":
            return
        elif ch == "1":
            _show_inventory(character_id)
        elif ch == "2":
            _show_equipment(character_id)
        elif ch == "3":
            _equip_flow(character_id)
        elif ch == "4":
            _unequip_flow(character_id)
        elif ch == "5":
            _compare_stats(character_id)
        else:
            print(color(" Invalid.", C.RED))
            pause()


# ============================================================
# INVENTORY VIEW
# ============================================================
def _show_inventory(character_id):
    inv = db.get_inventory(character_id)
    w = total_weight(character_id)
    cap = carry_capacity(character_id)

    clear()
    if not inv:
        print(box("INVENTORY", [" Kosong.", "", " 0. Kembali"]))
        pause()
        return

    lines = [
        f" Berat: {w}/{cap} kg",
        f" Item : {len(inv)} jenis",
        "",
    ]
    for i, it in enumerate(inv[:25], 1):
        item = get_item(it["item_id"]) or {}
        nm = item.get("name", it["item_id"])
        typ = item.get("type", "misc")
        q = it.get("quality", "normal")
        q_mark = ""
        if typ not in ("potion", "material", "arrow", "currency"):
            q_mark = f" [{q}]"
        lines.append(
            f" [{i:2d}] {color(nm, _qc(q)):<30} x{it['quantity']:<4} [{typ}]{q_mark}"
        )
    if len(inv) > 25:
        lines.append(color(f" ... {len(inv)-25} item lainnya (belum tampil)", C.GRAY))
    lines.append("")
    lines.append(" 0. Kembali")
    print(box("INVENTORY", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        idx = int(ch) - 1
        if 0 <= idx < len(inv):
            _item_detail(character_id, inv[idx])
    except ValueError:
        pass


def _item_detail(character_id, inv_item):
    item = get_item(inv_item["item_id"]) or {}
    q = inv_item.get("quality", "normal")

    clear()
    lines = [
        color(item.get("name", inv_item["item_id"]), _qc(q) + C.BOLD),
        f" Tipe     : {item.get('type','misc')}",
        f" Subtype  : {item.get('subtype','-')}",
        f" Quality  : {color(q, _qc(q))}",
        f" Jumlah   : {inv_item['quantity']}",
        f" Berat    : {item.get('weight', 0.1)} kg",
        f" Harga    : {item.get('price', 0)}s",
    ]

    # Stats
    stat_keys = ["attack", "magic_attack", "defense", "magic_defense",
                 "speed", "crit", "accuracy", "hp", "mana", "stamina",
                 "luck", "critical", "intelligence", "strength", "endurance",
                 "agility", "persuasion", "block", "damage"]
    stat_lines = []
    for k in stat_keys:
        if item.get(k):
            v = item_effective_stat(item, k, q, 0)
            stat_lines.append(f"  {k.replace('_',' ').title():<12}: +{v}  (base {item[k]})")
    if stat_lines:
        lines.append("")
        lines.append(color("STATISTIK:", C.YELLOW))
        lines.extend(stat_lines)

    # Durability
    if item.get("durability"):
        lines.append("")
        lines.append(f" Durability : {inv_item['durability']}/{inv_item['max_durability']}")

    # Element
    if item.get("element"):
        from elements import element_color, element_label
        lines.append(f" Elemen     : {color(element_label(item['element']), element_color(item['element']))}")

    # Effect
    if item.get("effect"):
        lines.append("")
        lines.append(color("EFEK:", C.YELLOW))
        lines.append(f"  {item['effect']}")

    # Description
    if item.get("desc"):
        lines.append("")
        lines.append(color(item["desc"], C.GRAY))

    # Equip hint
    if item.get("type") in ("weapon", "shield", "helmet", "chest",
                             "gloves", "legs", "boots", "ring", "necklace"):
        lines.append("")
        lines.append(color(" → Bisa di-equip dari menu utama.", C.CYAN))

    lines.append("")
    lines.append(" 0. Kembali")
    print(box("ITEM DETAIL", lines))
    prompt("> ")


# ============================================================
# EQUIPMENT VIEW
# ============================================================
def _show_equipment(character_id):
    eq = get_equipped(character_id)
    bonus = get_total_equipment_bonus(character_id)

    clear()
    lines = []
    for slot in SLOTS:
        row = eq.get(slot)
        if row:
            item = get_item(row["item_id"]) or {}
            up = f" +{row.get('upgrade_level', 0)}" if row.get("upgrade_level", 0) > 0 else ""
            nm = item.get("name", "?")
            dur = f"[{row['durability']}/{row['max_durability']}]"
            lines.append(
                f" {SLOT_LABEL[slot]:<12}: {color(nm, _qc(row['quality']))}{up}  {dur}"
            )
        else:
            lines.append(color(f" {SLOT_LABEL[slot]:<12}: (kosong)", C.GRAY))

    lines.append("")
    lines.append(color("TOTAL BONUS EQUIPMENT:", C.YELLOW + C.BOLD))
    if bonus:
        for k, v in sorted(bonus.items()):
            lines.append(f"  {k.replace('_',' ').title():<12}: +{v}")
    else:
        lines.append(color("  (tidak ada bonus)", C.GRAY))

    print(box("EQUIPMENT", lines))
    pause()


# ============================================================
# EQUIP FLOW
# ============================================================
def _equip_flow(character_id):
    inv = db.get_inventory(character_id)
    equippable = []
    for it in inv:
        item = get_item(it["item_id"])
        if not item:
            continue
        if item.get("type") in ("weapon", "shield", "helmet", "chest",
                                 "gloves", "legs", "boots", "ring", "necklace"):
            equippable.append(it)

    if not equippable:
        clear()
        print(box("EQUIP", [
            " Tidak ada item yang bisa di-equip.",
            "",
            " Beli di Market atau dapatkan dari loot.",
            "",
            " 0. Kembali",
        ]))
        pause()
        return

    clear()
    lines = []
    for i, it in enumerate(equippable, 1):
        item = get_item(it["item_id"]) or {}
        lines.append(
            f" [{i:2d}] {color(item.get('name','?'), _qc(it['quality'])):<28} "
            f"[{item.get('type','?')}]"
        )
    lines.append("")
    lines.append(" 0. Batal")
    print(box("EQUIP — Pilih item", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        inv_item = equippable[int(ch) - 1]
    except (ValueError, IndexError):
        return

    item = get_item(inv_item["item_id"])
    if not item:
        return

    # Tentukan slot options berdasarkan tipe
    t = item.get("type")
    slots_options = []
    if t == "weapon":
        # Kalau 2-handed weapon, off_hand harus kosong. Sederhanakan: main_weapon atau off_hand
        slots_options = ["main_weapon", "off_hand"]
    elif t == "shield":
        slots_options = ["off_hand"]
    elif t == "helmet":
        slots_options = ["helmet"]
    elif t == "chest":
        slots_options = ["chest"]
    elif t == "gloves":
        slots_options = ["gloves"]
    elif t == "legs":
        slots_options = ["legs"]
    elif t == "boots":
        slots_options = ["boots"]
    elif t == "ring":
        slots_options = ["ring1", "ring2"]
    elif t == "necklace":
        slots_options = ["necklace"]

    if not slots_options:
        print(color(" Tidak bisa di-equip.", C.RED))
        pause()
        return

    # Show comparison sebelum equip
    _equip_with_compare(character_id, inv_item, slots_options)


def _equip_with_compare(character_id, inv_item, slots_options):
    """Tampilkan perbandingan dengan slot saat ini."""
    item = get_item(inv_item["item_id"])
    q = inv_item.get("quality", "normal")
    eq = get_equipped(character_id)

    clear()
    lines = [
        color("ITEM BARU", C.YELLOW + C.BOLD),
        f" {color(item['name'], _qc(q))}",
        f" Quality : {q}",
    ]
    _append_stats_lines(lines, item, q, 0)

    # Bandingkan dengan setiap slot options
    for slot in slots_options:
        lines.append("")
        cur = eq.get(slot)
        if cur:
            cur_item = get_item(cur["item_id"]) or {}
            lines.append(color(f"CURRENT — {SLOT_LABEL[slot]}", C.CYAN))
            lines.append(f" {color(cur_item.get('name','?'), _qc(cur['quality']))}")
            lines.append(f" Quality : {cur['quality']}")
            _append_stats_lines(lines, cur_item, cur["quality"], cur.get("upgrade_level", 0))
        else:
            lines.append(color(f"CURRENT — {SLOT_LABEL[slot]}: (kosong)", C.GRAY))

    # Pilih slot
    if len(slots_options) == 1:
        lines.append("")
        lines.append(" 1. Equip ke " + SLOT_LABEL[slots_options[0]])
        lines.append(" 0. Batal")
        print(box("EQUIP", lines))
        if prompt("> ") != "1":
            return
        slot = slots_options[0]
    else:
        lines.append("")
        for i, s in enumerate(slots_options, 1):
            lines.append(f" {i}. Equip ke {SLOT_LABEL[s]}")
        lines.append(" 0. Batal")
        print(box("EQUIP — Pilih slot", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            slot = slots_options[int(ch) - 1]
        except (ValueError, IndexError):
            return

    ok, msg = equip_item(character_id, inv_item["id"], slot)
    if ok:
        print(color(f" ✓ {msg}", C.GREEN))
        # Auto-save
        try:
            db.update_character(character_id)
        except Exception:
            pass
    else:
        print(color(f" ✗ {msg}", C.RED))
    pause()


def _append_stats_lines(lines, item, quality, upgrade_level):
    """Helper — tambahkan stat lines ke list."""
    stat_keys = ["attack", "magic_attack", "defense", "magic_defense",
                 "speed", "crit", "accuracy", "hp", "mana", "stamina",
                 "luck", "critical", "block"]
    found = False
    for k in stat_keys:
        if item.get(k):
            v = item_effective_stat(item, k, quality, upgrade_level)
            lines.append(f"  {k.replace('_',' ').title():<12}: +{v}")
            found = True
    if not found:
        lines.append(color("  (tidak ada bonus stat)", C.GRAY))


# ============================================================
# UNEQUIP FLOW
# ============================================================
def _unequip_flow(character_id):
    eq = get_equipped(character_id)
    filled = [s for s in SLOTS if eq.get(s)]

    if not filled:
        clear()
        print(box("UNEQUIP", [
            " Tidak ada equipment yang terpasang.",
            "",
            " 0. Kembali",
        ]))
        pause()
        return

    clear()
    lines = []
    for i, s in enumerate(filled, 1):
        row = eq[s]
        item = get_item(row["item_id"]) or {}
        up = f" +{row.get('upgrade_level', 0)}" if row.get("upgrade_level", 0) > 0 else ""
        lines.append(
            f" [{i}] {SLOT_LABEL[s]:<12}: "
            f"{color(item.get('name','?'), _qc(row['quality']))}{up}"
        )
    lines.append("")
    lines.append(" 0. Batal")
    print(box("UNEQUIP", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    try:
        slot = filled[int(ch) - 1]
        ok, msg = unequip_slot(character_id, slot)
        if ok:
            print(color(f" ✓ {msg}", C.GREEN))
            try:
                db.update_character(character_id)
            except Exception:
                pass
        else:
            print(color(f" ✗ {msg}", C.RED))
        pause()
    except (ValueError, IndexError):
        pass


# ============================================================
# STAT COMPARISON
# ============================================================
def _compare_stats(character_id):
    """Tampilkan stat dengan dan tanpa equipment."""
    from character import max_hp, max_mp, max_stamina
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    bonus = get_total_equipment_bonus(character_id)

    clear()
    lines = [
        color("STAT COMPARISON (Base + Equipment = Total)", C.YELLOW + C.BOLD),
        "",
        f" HP  : {stats.get('hp', 0)} + {bonus.get('hp', 0)} = {stats.get('hp', 0) + bonus.get('hp', 0)}",
        f" MP  : {stats.get('mana', 0)} + {bonus.get('mana', 0)} = {stats.get('mana', 0) + bonus.get('mana', 0)}",
        f" STR : {stats.get('strength', 0)} + {bonus.get('strength', 0)} = {stats.get('strength', 0) + bonus.get('strength', 0)}",
        f" INT : {stats.get('intelligence', 0)} + {bonus.get('intelligence', 0)} = {stats.get('intelligence', 0) + bonus.get('intelligence', 0)}",
        f" DEF : {stats.get('defense', 0)} + {bonus.get('defense', 0)} = {stats.get('defense', 0) + bonus.get('defense', 0)}",
        f" SPD : {stats.get('speed', 0)} + {bonus.get('speed', 0)} = {stats.get('speed', 0) + bonus.get('speed', 0)}",
        f" AGI : {stats.get('agility', 0)} + {bonus.get('agility', 0)} = {stats.get('agility', 0) + bonus.get('agility', 0)}",
        f" LUK : {stats.get('luck', 0)} + {bonus.get('luck', 0)} = {stats.get('luck', 0) + bonus.get('luck', 0)}",
        f" CRT : {stats.get('critical', 0)} + {bonus.get('critical', 0)} = {stats.get('critical', 0) + bonus.get('critical', 0)}",
        "",
        color("EQUIPMENT-ONLY BONUS:", C.CYAN),
    ]
    if bonus:
        for k, v in sorted(bonus.items()):
            lines.append(f"  {k.replace('_',' ').title():<12}: +{v}")
    else:
        lines.append(color("  (kosong)", C.GRAY))

    lines.append("")
    lines.append(color("MAX VALUES:", C.YELLOW))
    lines.append(f"  Max HP      : {max_hp(stats, char['level']) + bonus.get('hp', 0) * 10}")
    lines.append(f"  Max MP      : {max_mp(stats, char['level']) + bonus.get('mana', 0) * 8}")
    lines.append(f"  Max Stamina : {max_stamina(stats, char['level']) + bonus.get('stamina', 0) * 6}")

    print(box("STAT COMPARISON", lines))
    pause()
