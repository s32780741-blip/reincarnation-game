"""Crafting UI."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from crafting import load_recipes, recipes_by_category, can_craft, craft, get_crafting_skill
from items import get_item


CATEGORIES = [
    ("weapon", "Weapons"),
    ("armor", "Armor & Shields"),
    ("tool", "Tools"),
    ("alchemy", "Alchemy"),
    ("smelt", "Smelting"),
    ("tailor", "Tailoring"),
    ("misc", "Misc"),
]


def crafting_menu(character_id):
    while True:
        clear()
        lv = get_crafting_skill(character_id)
        lines = [f" Crafting Level: {lv}", ""]
        for i, (cid, name) in enumerate(CATEGORIES, 1):
            n = len(recipes_by_category(cid))
            lines.append(f" {i}. {name}  ({n} recipes)")
        lines.append(" 0. Kembali")
        print(box("CRAFTING", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            cat_id = CATEGORIES[int(ch) - 1][0]
            _list_recipes(character_id, cat_id)
        except Exception:
            pass


def _list_recipes(character_id, cat):
    recipes = recipes_by_category(cat)
    while True:
        clear()
        if not recipes:
            print(box("CRAFTING", [" Tidak ada recipe di kategori ini."]))
            pause(); return
        lines = []
        for i, r in enumerate(recipes, 1):
            ok, _ = can_craft(character_id, r)
            mark = color("•", C.WHITE) if ok else color("🔒", C.YELLOW)
            out_item = get_item(r["output"]["id"]) or {}
            lines.append(f" {mark} [{i:2d}] {r['name']:<28} (req {r.get('crafting_req',1)})")
        lines.append(""); lines.append(" 0. Kembali")
        print(box(f"CRAFT — {cat}", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            r = recipes[int(ch) - 1]
            _recipe_detail(character_id, r)
        except Exception:
            pass


def _recipe_detail(character_id, recipe):
    while True:
        ok, reasons = can_craft(character_id, recipe)
        out = recipe["output"]
        out_item = get_item(out["id"]) or {}

        clear()
        lines = [
            color(recipe["name"], C.CYAN + C.BOLD),
            f" Kategori : {recipe.get('category','misc')}",
            f" Req Lv   : {recipe.get('crafting_req',1)}",
            "",
            color("OUTPUT:", C.YELLOW),
            f"  {out_item.get('name', out['id'])} x{out['amount']}",
            "",
            color("MATERIALS:", C.YELLOW),
        ]
        for m in recipe.get("materials", []):
            if m["amount"] <= 0:
                continue
            item = get_item(m["id"]) or {}
            have = db.get_item_count(character_id, m["id"])
            mark = color("✓", C.GREEN) if have >= m["amount"] else color("✗", C.RED)
            lines.append(f"  {mark} {item.get('name', m['id'])} x{m['amount']}  (punya {have})")

        if recipe.get("desc"):
            lines.append("")
            lines.append(color(recipe["desc"], C.GRAY))

        lines.append("")
        if ok:
            lines.append(" 1. Craft")
        else:
            lines.append(color(" Syarat belum terpenuhi.", C.RED))
        lines.append(" 0. Kembali")
        print(box("RECIPE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        if ch == "1" and ok:
            success, result = craft(character_id, recipe)
            if success:
                clear()
                out_item = get_item(result["output"]["id"]) or {}
                lns = [
                    color(f" ✓ {recipe['name']} selesai!", C.GREEN + C.BOLD),
                    f" Dapat: {out_item.get('name', result['output']['id'])} x{result['output']['amount']}",
                    f" +{result['exp']} crafting EXP",
                ]
                for lv in result.get("level_ups", []):
                    from mastery import get_level_info
                    info = get_level_info("blacksmithing", lv)
                    lns.append(color(f" ★ CRAFTING UP! Lv {lv} — {info['name'] if info else '?'}", C.MAGENTA))
                print(box("CRAFT", lns))
                try:
                    from achievements import check_all
                    check_all(character_id, silent=True)
                except Exception:
                    pass
                pause()
                # Refresh — return to list
                return
            else:
                print(color(" ✗ Craft gagal.", C.RED))
                pause()
                return
