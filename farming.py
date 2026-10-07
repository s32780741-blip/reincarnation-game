"""Farming logic — real-time growth."""
import json, os, time, random
from config import DATA_DIR
import database as db
from items import get_item

_F = None


def load_farming():
    global _F
    if _F is not None:
        return _F
    path = os.path.join(DATA_DIR, "farming.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _F = json.load(f)
    except Exception:
        _F = {"crops": [], "plot_count": 6}
    return _F


def get_crop(crop_id):
    for c in load_farming().get("crops", []):
        if c["id"] == crop_id:
            return c
    return None


def get_crop_by_seed(seed_id):
    for c in load_farming().get("crops", []):
        if c["seed"] == seed_id:
            return c
    return None


def plot_count():
    return load_farming().get("plot_count", 6)


def ensure_plots(character_id):
    """Pastikan baris plot ada di DB."""
    c = db.conn()
    for i in range(plot_count()):
        c.execute(
            "INSERT OR IGNORE INTO farming_plots(character_id, plot_index, state) VALUES (?,?, 'empty')",
            (character_id, i)
        )
    c.commit()


def get_plots(character_id):
    ensure_plots(character_id)
    c = db.conn()
    rows = c.execute(
        "SELECT plot_index, state, seed_id, crop_id, planted_at, water_count "
        "FROM farming_plots WHERE character_id=? ORDER BY plot_index",
        (character_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def plant(character_id, plot_index, seed_id):
    crop = get_crop_by_seed(seed_id)
    if not crop:
        return False, "Benih tidak valid."
    if db.get_item_count(character_id, seed_id) < 1:
        return False, "Tidak punya benih."
    db.remove_item(character_id, seed_id, 1)
    c = db.conn()
    c.execute(
        "UPDATE farming_plots SET state='growing', seed_id=?, crop_id=?, planted_at=?, water_count=0 "
        "WHERE character_id=? AND plot_index=?",
        (seed_id, crop["id"], int(time.time()), character_id, plot_index)
    )
    c.commit()
    return True, crop


def water(character_id, plot_index):
    c = db.conn()
    row = c.execute(
        "SELECT state, water_count FROM farming_plots WHERE character_id=? AND plot_index=?",
        (character_id, plot_index)
    ).fetchone()
    if not row or row["state"] != "growing":
        return False, "Tidak ada tanaman di plot ini."
    c.execute(
        "UPDATE farming_plots SET water_count=water_count+1 WHERE character_id=? AND plot_index=?",
        (character_id, plot_index)
    )
    c.commit()
    return True, "Tanaman disiram."


def plot_progress(plot):
    """Return (ready, pct, remaining_sec)."""
    if plot["state"] != "growing":
        return False, 0, 0
    crop = get_crop(plot["crop_id"])
    if not crop:
        return False, 0, 0
    elapsed = int(time.time()) - plot["planted_at"]
    base_time = crop.get("grow_time", 60)
    # water bonus mempercepat
    bonus = plot.get("water_count", 0) * crop.get("water_bonus", 0.4)
    effective = max(5, int(base_time * (1 - min(0.8, bonus))))
    pct = min(100, int(elapsed / effective * 100))
    remaining = max(0, effective - elapsed)
    return (elapsed >= effective), pct, remaining


def harvest(character_id, plot_index):
    c = db.conn()
    row = c.execute(
        "SELECT state, crop_id, planted_at, water_count FROM farming_plots "
        "WHERE character_id=? AND plot_index=?",
        (character_id, plot_index)
    ).fetchone()
    if not row or row["state"] != "growing":
        return False, "Plot kosong."
    plot = dict(row)
    plot["plot_index"] = plot_index
    ready, _, _ = plot_progress(plot)
    if not ready:
        return False, "Belum siap panen."
    crop = get_crop(plot["crop_id"])
    if not crop:
        return False, "Crop tidak valid."
    # Yield
    y = crop.get("yield", {})
    amt = random.randint(y.get("amount", [1, 1])[0], y.get("amount", [1, 1])[1])
    amt += plot.get("water_count", 0) // 2
    db.add_item(character_id, y["id"], amt)
    # Reset plot
    c.execute(
        "UPDATE farming_plots SET state='empty', seed_id=NULL, crop_id=NULL, "
        "planted_at=NULL, water_count=0 WHERE character_id=? AND plot_index=?",
        (character_id, plot_index)
    )
    c.commit()
    from character import grant_exp
    exp = crop.get("exp", 10)
    grant_exp(character_id, exp)
    return True, {"crop": crop, "amount": amt, "exp": exp}
