"""User settings persistence (JSON)."""
import json, os
from config import SETTINGS_PATH

DEFAULTS = {
    "language": "id",           # id | en
    "text_speed": "normal",     # slow | normal | fast | instant
    "animation": True,
    "auto_save": True,
    "confirm_actions": True,
    "show_damage_numbers": True,
}

_cache = None

def load():
    global _cache
    if _cache is not None:
        return _cache
    if not os.path.exists(SETTINGS_PATH):
        _cache = dict(DEFAULTS)
        save(_cache)
        return _cache
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = dict(DEFAULTS)
        merged.update({k: v for k, v in data.items() if k in DEFAULTS})
        _cache = merged
    except Exception:
        _cache = dict(DEFAULTS)
    return _cache

def save(data=None):
    global _cache
    if data is not None:
        _cache = data
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(_cache, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[settings] gagal simpan: {e}")
        return False

def get(key, default=None):
    return load().get(key, default)

def set_value(key, value):
    data = load()
    data[key] = value
    save(data)

def type_delay():
    sp = get("text_speed", "normal")
    return {"slow": 0.035, "normal": 0.015, "fast": 0.006, "instant": 0.0}.get(sp, 0.015)
