"""Simple internationalization — ID / EN."""
import json, os
from config import LANG_DIR

DEFAULT_LANG = "id"

_cache = {}

def _load(lang):
    if lang in _cache:
        return _cache[lang]
    path = os.path.join(LANG_DIR, f"{lang}.json")
    if not os.path.exists(path):
        _cache[lang] = {}
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            _cache[lang] = json.load(f)
    except Exception:
        _cache[lang] = {}
    return _cache[lang]

def t(key, lang=DEFAULT_LANG, **kwargs):
    data = _load(lang)
    text = data.get(key, _load(DEFAULT_LANG).get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text
