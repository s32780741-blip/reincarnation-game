"""Market logic — stocks, pricing, buy/sell."""
import random
import database as db
from items import get_item, load_items
from cities import get_city
from equipment import QUALITY_ORDER, get_quality_mult

# Kategori item yang dijual di market biasa
SHOP_CATEGORIES = {
    "weapons": ["weapon"],
    "shields": ["shield"],
    "armor":   ["helmet", "chest", "gloves", "legs", "boots"],
    "potions": ["potion"],
    "accessories": ["ring", "necklace"],
    "materials": ["material"],
    "arrows": ["arrow"],
}

# Black market categories (rare + forbidden theme)
BLACK_MARKET_CATEGORIES = {
    "weapons_rare": ["weapon"],
    "materials_rare": ["material"],
    "cores": ["element_core"],
    "potions_rare": ["potion"],
}


def generate_quality(item):
    """Roll quality berdasarkan rarity & random."""
    if item["type"] in ("potion", "material", "arrow", "currency"):
        return "normal"
    r = random.random()
    if r < 0.05: return "poor"
    if r < 0.15: return "low"
    if r < 0.30: return "average"
    if r < 0.60: return "normal"
    if r < 0.78: return "good"
    if r < 0.90: return "high"
    if r < 0.96: return "superior"
    if r < 0.99: return "excellent"
    if r < 0.998: return "masterwork"
    return "legendary"


def price_of(item, quality="normal"):
    base = item.get("price", 10)
    mult = get_quality_mult(quality)
    # Non-equipment tidak kena mult
    if item["type"] in ("potion", "material", "arrow", "currency"):
        mult = 1.0
    return max(1, int(base * mult))


def city_price_mult(city_id):
    """Beberapa kota lebih mahal (capital, kota kaya)."""
    c = get_city(city_id)
    if not c:
        return 1.0
    if c["type"] == "capital":
        return 1.15
    if c["type"] == "city":
        return 1.05
    if c["type"] == "village":
        return 0.9
    return 1.0


def reputation_discount(character_id, city_id):
    """Reputasi dengan kota = diskon beli."""
    rep = db.get_reputation(character_id, "city", city_id)
    # -10% max untuk rep 50+
    discount = min(0.10, max(-0.10, rep / 500.0))
    return discount


def get_buy_price(character_id, item, quality="normal", city_id="aurelia"):
    base = price_of(item, quality)
    mult = city_price_mult(city_id)
    disc = reputation_discount(character_id, city_id)
    final = base * mult * (1 - disc)
    return max(1, int(final))


def get_sell_price(character_id, item, quality="normal", durability=100, max_dur=100):
    base = price_of(item, quality)
    # Sell = 40% base
    price = base * 0.4
    if item["type"] not in ("potion", "material", "arrow", "currency"):
        # durability affects
        if max_dur > 0:
            price *= (0.5 + 0.5 * durability / max_dur)
    return max(1, int(price))


def generate_market_stock(city_id, category, seed=None):
    """Return list of {item, quality, quantity}."""
    if seed is not None:
        random.seed(seed)
    c = get_city(city_id)
    if not c:
        return []
    types = SHOP_CATEGORIES.get(category, [])
    all_items = load_items()
    pool = [it for it in all_items if it["type"] in types]

    # Filter by level / city danger
    city_danger = c.get("danger", 1)
    # Higher danger cities = better items
    results = []
    sample_size = min(len(pool), random.randint(6, 10))
    picked = random.sample(pool, sample_size) if pool else []
    for it in picked:
        # Filter for very strong items in low-danger cities
        if it["type"] == "weapon" and it.get("attack", 0) > 40 and city_danger < 4:
            continue
        if it["type"] == "chest" and it.get("defense", 0) > 35 and city_danger < 5:
            continue
        qty = 1
        if it["type"] in ("potion", "material", "arrow"):
            qty = random.randint(2, 12)
        quality = generate_quality(it)
        results.append({"item": it, "quality": quality, "quantity": qty})
    return results


def generate_black_market_stock(city_id, seed=None):
    if seed is not None:
        random.seed(seed)
    all_items = load_items()
    # Filter rare/expensive items
    pool = [it for it in all_items if it.get("price", 0) >= 300]
    if not pool:
        pool = all_items
    results = []
    picked = random.sample(pool, min(6, len(pool)))
    for it in picked:
        # Higher quality guaranteed
        q = random.choice(["high", "superior", "excellent", "masterwork"])
        results.append({
            "item": it,
            "quality": q,
            "quantity": 1,
            "black_price_mult": random.uniform(1.5, 2.5),
        })
    return results


def buy_item(character_id, item, quantity, quality, total_price):
    """Deduct currency & add to inventory."""
    char = db.get_character(character_id)
    if char["silver"] < total_price:
        return False, "Silver tidak cukup."
    db.update_character(character_id, silver=char["silver"] - total_price)
    db.add_item(character_id, item["id"], quantity)
    return True, f"Bought {item['name']} x{quantity}."


def sell_item(character_id, inventory_id):
    """Sell 1 unit dari inventory."""
    c = db.conn()
    row = c.execute(
        "SELECT id, item_id, quantity, quality, durability, max_durability "
        "FROM character_inventory WHERE id=? AND character_id=?",
        (inventory_id, character_id)
    ).fetchone()
    if not row:
        return False, "Item tidak ditemukan."
    item = get_item(row["item_id"])
    if not item:
        return False, "Item tidak valid."
    price = get_sell_price(character_id, item, row["quality"],
                           row["durability"], row["max_durability"])
    # Remove 1
    db.remove_item(character_id, row["item_id"], 1)
    char = db.get_character(character_id)
    db.update_character(character_id, silver=char["silver"] + price)
    return True, price, item["name"]
