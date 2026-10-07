"""UI farming + cooking."""
from ui import C, color, clear, box, prompt, pause, progress_bar
import database as db
import settings
from farming import get_plots, plant, water, harvest, plot_progress, get_crop_by_seed, plot_count
from cooking import load_recipes, can_cook, cook
from items import get_item


def life_menu(character_id):
    while True:
        clear()
        lines = [
            " 1. Farming",
            " 2. Cooking",
            " 0. Kembali",
        ]
        print(box("LIFE SKILLS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _farming(character_id)
        elif ch == "2":
            _cooking(character_id)


# ---------- FARMING ----------
def _farming(character_id):
    while True:
        plots = get_plots(character_id)
        clear()
        lines = []
        for p in plots:
            idx = p["plot_index"]
            state = p["state"]
            if state == "empty":
                lines.append(f" [{idx+1}] (kosong)")
            elif state == "growing":
                ready, pct, rem = plot_progress(p)
                crop = get_item(p["crop_id"]) or {"name": p["crop_id"]}
                status = "SIAP PANEN" if ready else f"{rem}s lagi"
                lines.append(
                    f" [{idx+1}] {crop.get('name','?'):<12} "
                    f"{progress_bar(pct, 14)} {status} (air x{p['water_count']})"
                )
        lines.append("")
        lines.append(" 1. Tanam")
        lines.append(" 2. Siram")
        lines.append(" 3. Panen")
        lines.append(" 0. Kembali")
        print(box("FARMING", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            _plant_menu(character_id)
        elif ch == "2":
            _water_menu(character_id)
        elif ch == "3":
            _harvest_menu(character_id)


def _plant_menu(character_id):
    inv = db.get_inventory(character_id)
    seeds = [it for it in inv if (get_item(it["item_id"]) or {}).get("type") == "seed"]
    if not seeds:
        clear()
        print(box("PLANT", [" Tidak punya benih.", "", " Beli benih di Market / cooking section."]))
        pause(); return
    clear()
    lines = []
    for i, s in enumerate(seeds, 1):
        item = get_item(s["item_id"]) or {}
        lines.append(f" [{i}] {item.get('name', s['item_id'])} x{s['quantity']}")
    lines.append(""); lines.append(" 0. Batal")
    print(box("PILIH BENIH", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        seed = seeds[int(ch) - 1]
    except Exception:
        return
    # Pilih plot
    plots = get_plots(character_id)
    empty = [p for p in plots if p["state"] == "empty"]
    if not empty:
        print(color(" Tidak ada plot kosong.", C.YELLOW)); pause(); return
    clear()
    lines = []
    for i, p in enumerate(empty, 1):
        lines.append(f" [{i}] Plot {p['plot_index']+1}")
    lines.append(" 0. Batal")
    print(box("PILIH PLOT", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        plot = empty[int(ch) - 1]
    except Exception:
        return
    ok, res = plant(character_id, plot["plot_index"], seed["item_id"])
    if ok:
        print(color(f" ✓ Ditanam: {get_item(seed['item_id'])['name']} di plot {plot['plot_index']+1}", C.GREEN))
    else:
        print(color(f" ✗ {res}", C.RED))
    pause()


def _water_menu(character_id):
    plots = get_plots(character_id)
    growing = [p for p in plots if p["state"] == "growing"]
    if not growing:
        print(color(" Tidak ada tanaman.", C.YELLOW)); pause(); return
    clear()
    lines = []
    for i, p in enumerate(growing, 1):
        crop = get_item(p["crop_id"]) or {}
        lines.append(f" [{i}] Plot {p['plot_index']+1} — {crop.get('name','?')}")
    lines.append(" 0. Batal")
    print(box("PILIH PLOT", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        p = growing[int(ch) - 1]
        ok, msg = water(character_id, p["plot_index"])
        print(color(f" {'✓' if ok else '✗'} {msg}", C.GREEN if ok else C.RED))
        pause()
    except Exception:
        pass


def _harvest_menu(character_id):
    plots = get_plots(character_id)
    ready = []
    for p in plots:
        if p["state"] == "growing":
            r, _, _ = plot_progress(p)
            if r:
                ready.append(p)
    if not ready:
        print(color(" Belum ada yang siap panen.", C.YELLOW)); pause(); return
    clear()
    lines = []
    for i, p in enumerate(ready, 1):
        crop = get_item(p["crop_id"]) or {}
        lines.append(f" [{i}] Plot {p['plot_index']+1} — {crop.get('name','?')}")
    lines.append(" 0. Batal")
    print(box("PANEN", lines))
    ch = prompt("> ")
    if ch == "0": return
    try:
        p = ready[int(ch) - 1]
        ok, res = harvest(character_id, p["plot_index"])
        if ok:
            item = get_item(res["crop"]["yield"]["id"]) or {}
            clear()
            print(box("PANEN", [
                color(" ✓ Panen berhasil!", C.GREEN),
                f" Dapat: {item.get('name', res['crop']['yield']['id'])} x{res['amount']}",
                f" +{res['exp']} EXP",
            ]))
            pause()
        else:
            print(color(f" ✗ {res}", C.RED)); pause()
    except Exception:
        pass


# ---------- COOKING ----------
def _cooking(character_id):
    while True:
        recipes = load_recipes()
        clear()
        lines = []
        for i, r in enumerate(recipes, 1):
            ok, _ = can_cook(character_id, r)
            mark = color("•", C.WHITE) if ok else color("🔒", C.YELLOW)
            lines.append(f" {mark} [{i}] {r['name']:<24} (req {r.get('cooking_req',1)})")
        lines.append(""); lines.append(" 0. Kembali")
        print(box("COOKING", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            r = recipes[int(ch) - 1]
            _cook_recipe(character_id, r)
        except Exception:
            pass


def _cook_recipe(character_id, recipe):
    ok, reasons = can_cook(character_id, recipe)
    out = recipe["output"]
    out_item = get_item(out["id"]) or {}
    clear()
    lines = [
        color(recipe["name"], C.CYAN + C.BOLD),
        f" Req Lv : {recipe.get('cooking_req',1)}",
        "",
        color("OUTPUT:", C.YELLOW),
        f"  {out_item.get('name', out['id'])} x{out['amount']}",
    ]
    if out_item.get("effect"):
        lines.append(f"  Efek: {out_item['effect']}")
    lines.append("")
    lines.append(color("MATERIALS:", C.YELLOW))
    for m in recipe.get("materials", []):
        if m["amount"] <= 0:
            continue
        item = get_item(m["id"]) or {}
        have = db.get_item_count(character_id, m["id"])
        mark = color("✓", C.GREEN) if have >= m["amount"] else color("✗", C.RED)
        lines.append(f"  {mark} {item.get('name', m['id'])} x{m['amount']}  (punya {have})")
    lines.append("")
    if ok:
        lines.append(" 1. Masak")
    else:
        lines.append(color(" Syarat belum terpenuhi.", C.RED))
    lines.append(" 0. Kembali")
    print(box("COOK", lines))
    ch = prompt("> ")
    if ch == "1" and ok:
        ok2, res = cook(character_id, recipe)
        if ok2:
            clear()
            oi = get_item(res["output"]["id"]) or {}
            lns = [
                color(" ✓ Masakan selesai!", C.GREEN + C.BOLD),
                f" Dapat: {oi.get('name', res['output']['id'])} x{res['output']['amount']}",
                f" +{res['exp']} cooking EXP",
            ]
            for lv in res.get("level_ups", []):
                lns.append(color(f" ★ COOKING UP! Lv {lv}", C.MAGENTA))
            print(box("COOK", lns))
            pause()
