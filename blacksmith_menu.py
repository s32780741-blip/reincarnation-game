"""Blacksmith UI."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from items import get_item
from equipment import get_equipped, SLOTS, SLOT_LABEL, QUALITY_COLOR
from blacksmith import (
    repair_cost, repair_slot, upgrade_cost, upgrade_slot,
    upgrade_chance, _material_for,
)


def blacksmith_menu(character_id):
    while True:
        clear()
        print(box("BLACKSMITH", [
            " 1. Repair equipment",
            " 2. Upgrade equipment",
            " 0. Kembali",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _repair_menu(character_id)
        elif ch == "2":
            _upgrade_menu(character_id)


def _repair_menu(character_id):
    while True:
        eq = get_equipped(character_id)
        clear()
        lines = []
        for slot in SLOTS:
            row = eq.get(slot)
            if row:
                item = get_item(row["item_id"])
                nm = item["name"] if item else row["item_id"]
                cost = repair_cost(row)
                lines.append(
                    f" {SLOT_LABEL[slot]:<12} : {nm:<20} "
                    f"[{row['durability']}/{row['max_durability']}] {cost}s"
                )
            else:
                lines.append(color(f" {SLOT_LABEL[slot]:<12} : (kosong)", C.GRAY))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("REPAIR", lines))
        ch = prompt(" Pilih nomor slot / nama: ")
        if ch == "0":
            return
        # Cari slot by nomor
        filled = [s for s in SLOTS if eq.get(s)]
        try:
            idx = int(ch) - 1
            if 0 <= idx < len(filled):
                slot = filled[idx]
                _do_repair(character_id, slot)
        except ValueError:
            pass


def _do_repair(character_id, slot):
    eq = get_equipped(character_id)
    row = eq.get(slot)
    if not row:
        return
    item = get_item(row["item_id"])
    cost = repair_cost(row)
    if cost == 0:
        print(color(" Durability sudah penuh.", C.YELLOW)); pause(); return
    clear()
    print(box("REPAIR", [
        f" Item : {item['name'] if item else row['item_id']}",
        f" Biaya: {cost}s",
        "",
        " 1. Konfirmasi",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    ok, res = repair_slot(character_id, slot)
    if ok:
        print(color(f" ✓ Diperbaiki! -{res}s", C.GREEN))
    else:
        print(color(f" ✗ {res}", C.RED))
    pause()


def _upgrade_menu(character_id):
    while True:
        eq = get_equipped(character_id)
        clear()
        lines = []
        for slot in SLOTS:
            row = eq.get(slot)
            if row:
                item = get_item(row["item_id"])
                nm = item["name"] if item else row["item_id"]
                lv = row.get("upgrade_level", 0)
                sc, mats = upgrade_cost(row)
                mat_str = ", ".join(f"{get_item(m)['name'] if get_item(m) else m} x{q}"
                                    for m, q in mats.items())
                lines.append(
                    f" {SLOT_LABEL[slot]:<12} : {nm:<20} +{lv} ({sc}s + {mat_str})"
                )
            else:
                lines.append(color(f" {SLOT_LABEL[slot]:<12} : (kosong)", C.GRAY))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("UPGRADE", lines))
        ch = prompt(" Pilih nomor: ")
        if ch == "0":
            return
        filled = [s for s in SLOTS if eq.get(s)]
        try:
            idx = int(ch) - 1
            if 0 <= idx < len(filled):
                _do_upgrade(character_id, filled[idx])
        except ValueError:
            pass


def _do_upgrade(character_id, slot):
    eq = get_equipped(character_id)
    row = eq.get(slot)
    if not row:
        return
    item = get_item(row["item_id"])
    lv = row.get("upgrade_level", 0)
    sc, mats = upgrade_cost(row)
    chance = int(upgrade_chance(lv) * 100)

    clear()
    print(box("UPGRADE", [
        f" Item     : {item['name'] if item else row['item_id']}",
        f" Level    : +{lv} → +{lv+1}",
        f" Biaya    : {sc}s",
        f" Material : {', '.join(f'{m} x{q}' for m,q in mats.items())}",
        f" Chance   : {chance}%",
        "",
        color(" ⚠ Gagal = material & silver hangus.", C.YELLOW),
        "",
        " 1. Konfirmasi",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    ok, res = upgrade_slot(character_id, slot)
    if not ok:
        print(color(f" ✗ {res}", C.RED)); pause(); return
    if res == "success":
        print(color(f" ★ UPGRADE BERHASIL! +{lv+1}", C.GREEN + C.BOLD))
    else:
        print(color(" ✗ Upgrade gagal. Material & silver hangus.", C.RED))
    pause()
