"""Market UI — buy, sell, black market."""
from ui import C, color, clear, box, prompt, pause
import database as db
import settings
from items import get_item
from market import (
    generate_market_stock, generate_black_market_stock,
    get_buy_price, get_sell_price, buy_item, sell_item,
    SHOP_CATEGORIES,
)
from equipment import QUALITY_COLOR, QUALITY_ORDER
from cities import get_city


def _qc(quality):
    name = QUALITY_COLOR.get(quality, "white")
    return getattr(C, name.upper(), C.WHITE)


def market_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        city = get_city(char["location"])
        has_bm = city.get("black_market", False) if city else False

        clear()
        lines = [
            f" Kota   : {city['name'] if city else char['location']}",
            f" Silver : {char['silver']}",
            f" Gold   : {char['gold']}",
            "",
            " 1. Weapons",
            " 2. Shields",
            " 3. Armor",
            " 4. Potions",
            " 5. Accessories",
            " 6. Materials",
            " 7. Arrows",
            " 8. Sell Items",
        ]
        if has_bm:
            lines.append(color(" 9. Black Market", C.MAGENTA))
        lines.append(" 0. Kembali")
        print(box("MARKET", lines))
        ch = prompt("> ")

        if ch == "0":
            return
        elif ch == "1":
            _shop(character_id, "weapons")
        elif ch == "2":
            _shop(character_id, "shields")
        elif ch == "3":
            _shop(character_id, "armor")
        elif ch == "4":
            _shop(character_id, "potions")
        elif ch == "5":
            _shop(character_id, "accessories")
        elif ch == "6":
            _shop(character_id, "materials")
        elif ch == "7":
            _shop(character_id, "arrows")
        elif ch == "8":
            _sell_menu(character_id)
        elif ch == "9" and has_bm:
            _black_market(character_id)


def _shop(character_id, category):
    char = db.get_character(character_id)
    stock = generate_market_stock(char["location"], category)
    if not stock:
        clear()
        print(box("SHOP", [" Tidak ada barang di kategori ini."]))
        pause()
        return

    while True:
        clear()
        lines = []
        for i, s in enumerate(stock, 1):
            it = s["item"]
            q = s["quality"]
            price = get_buy_price(character_id, it, q, char["location"])
            qc = _qc(q)
            lines.append(
                f" [{i:2d}] {color(it['name'], qc):<32} x{s['quantity']:<3} {price:>6}s  ({q})"
            )
        lines.append("")
        lines.append(" 0. Kembali")
        print(box(f"SHOP — {category}", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            s = stock[int(ch) - 1]
            _buy_detail(character_id, s)
        except Exception:
            pass


def _buy_detail(character_id, stock_item):
    char = db.get_character(character_id)
    it = stock_item["item"]
    q = stock_item["quality"]
    clear()
    lines = [
        color(it["name"], _qc(q) + C.BOLD),
        f" Quality    : {q}",
        f" Tipe       : {it['type']}",
        f" Berat      : {it.get('weight', 0)} kg",
    ]
    if it.get("attack"): lines.append(f" Attack     : +{it['attack']}")
    if it.get("magic_attack"): lines.append(f" Magic Atk  : +{it['magic_attack']}")
    if it.get("defense"): lines.append(f" Defense    : +{it['defense']}")
    if it.get("magic_defense"): lines.append(f" Magic Def  : +{it['magic_defense']}")
    if it.get("speed"): lines.append(f" Speed      : {it['speed']:+}")
    if it.get("crit"): lines.append(f" Crit       : +{it['crit']}%")
    if it.get("hp"): lines.append(f" HP         : +{it['hp']}")
    if it.get("mana"): lines.append(f" Mana       : +{it['mana']}")
    if it.get("durability"): lines.append(f" Durability : {it['durability']}")
    if it.get("element"): lines.append(f" Elemen     : {it['element']}")
    if it.get("effect"): lines.append(f" Efek       : {it['effect']}")

    unit_price = get_buy_price(character_id, it, q, char["location"])
    lines.append("")
    lines.append(f" Harga satuan : {unit_price}s")
    lines.append(f" Stock        : {stock_item['quantity']}")
    lines.append("")
    lines.append(" 1. Beli 1")
    if stock_item["quantity"] > 1:
        lines.append(" 2. Beli beberapa")
    lines.append(" 0. Batal")
    print(box("BUY", lines))
    ch = prompt("> ")
    if ch == "0":
        return
    if ch == "1":
        qty = 1
    elif ch == "2":
        try:
            qty = int(prompt(" Jumlah: ") or "1")
            qty = max(1, min(stock_item["quantity"], qty))
        except ValueError:
            return
    else:
        return

    total = unit_price * qty
    if char["silver"] < total:
        print(color(f" Silver tidak cukup. Butuh {total}s.", C.RED))
        pause()
        return
    ok, msg = buy_item(character_id, it, qty, q, total)
    if ok:
        print(color(f" ✓ Beli {it['name']} x{qty} seharga {total}s.", C.GREEN))
        stock_item["quantity"] -= qty
    else:
        print(color(f" ✗ {msg}", C.RED))
    pause()


def _sell_menu(character_id):
    inv = db.get_inventory(character_id)
    sellable = [it for it in inv
                if (get_item(it["item_id"]) or {}).get("type") not in ("currency", "quest_item")]
    if not sellable:
        clear()
        print(box("SELL", [" Tidak ada item untuk dijual."]))
        pause()
        return
    while True:
        clear()
        lines = []
        for i, s in enumerate(sellable[:25], 1):
            it = get_item(s["item_id"])
            if not it: continue
            price = get_sell_price(character_id, it, s["quality"], s["durability"], s["max_durability"])
            qc = _qc(s["quality"])
            lines.append(f" [{i:2d}] {color(it['name'], qc):<30} x{s['quantity']:<3} {price:>5}s")
        if len(sellable) > 25:
            lines.append(color(f" ... {len(sellable)-25} lainnya belum tampil", C.GRAY))
        lines.append("")
        lines.append(" 0. Kembali")
        print(box("SELL ITEMS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            s = sellable[int(ch) - 1]
            _sell_detail(character_id, s)
        except Exception:
            pass


def _sell_detail(character_id, inv_item):
    it = get_item(inv_item["item_id"])
    if not it:
        return
    price = get_sell_price(character_id, it, inv_item["quality"],
                           inv_item["durability"], inv_item["max_durability"])
    clear()
    print(box("SELL", [
        color(it["name"], _qc(inv_item["quality"]) + C.BOLD),
        f" Quality : {inv_item['quality']}",
        f" Jumlah  : {inv_item['quantity']}",
        f" Harga jual: {price}s",
        "",
        " 1. Jual 1",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    ok, p, name = sell_item(character_id, inv_item["id"])
    if ok:
        print(color(f" ✓ Jual {name} seharga {p}s.", C.GREEN))
    else:
        print(color(f" ✗ {p}", C.RED))
    pause()


def _black_market(character_id):
    char = db.get_character(character_id)
    stock = generate_black_market_stock(char["location"])
    if not stock:
        clear()
        print(box("BLACK MARKET", [" Kosong."]))
        pause()
        return
    while True:
        clear()
        lines = [color(" ⚠ BARANG ILEGAL / LANGKA — harga tinggi, ada risiko.", C.YELLOW), ""]
        for i, s in enumerate(stock, 1):
            it = s["item"]
            q = s["quality"]
            base = get_buy_price(character_id, it, q, char["location"])
            final = int(base * s["black_price_mult"])
            lines.append(f" [{i:2d}] {color(it['name'], _qc(q)):<30} {final}s ({q})")
        lines.append("")
        lines.append(" 0. Keluar")
        print(box("BLACK MARKET", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        try:
            s = stock[int(ch) - 1]
            _bm_buy(character_id, s)
        except Exception:
            pass


def _bm_buy(character_id, s):
    char = db.get_character(character_id)
    it = s["item"]
    q = s["quality"]
    base = get_buy_price(character_id, it, q, char["location"])
    final = int(base * s["black_price_mult"])

    clear()
    print(box("BLACK MARKET", [
        color(it["name"], _qc(q) + C.BOLD),
        f" Quality : {q}",
        f" Harga   : {final}s",
        "",
        color("⚠ Risiko: 15% barang palsu (duit hangus).", C.YELLOW),
        "",
        " 1. Beli",
        " 0. Batal",
    ]))
    if prompt("> ") != "1":
        return
    if char["silver"] < final:
        print(color(" Silver tidak cukup.", C.RED)); pause(); return

    import random
    db.update_character(character_id, silver=char["silver"] - final)
    if random.random() < 0.15:
        print(color(" ✗ Barang palsu! Uangmu hangus.", C.RED))
    else:
        db.add_item(character_id, it["id"], 1)
        print(color(f" ✓ Membeli {it['name']} secara rahasia.", C.GREEN))
        # Reputasi turun tipis
        db.add_reputation(character_id, "city", char["location"], -1)
    pause()
