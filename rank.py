"""Rank calculation based on level."""
from config import RANKS, MAX_LEVEL_NORMAL, MAX_LEVEL_CIT

def get_rank(level, cit_mode=False):
    max_lv = MAX_LEVEL_CIT if cit_mode else MAX_LEVEL_NORMAL
    for r in RANKS:
        if r["min"] <= level < r["max"]:
            return r
    return RANKS[-1]

def rank_text(level, cit_mode=False):
    r = get_rank(level, cit_mode)
    return f"RANK {_roman(r['id'])} — {r['name'].upper()}"

def _roman(n):
    pairs = [(10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for v, s in pairs:
        while n >= v:
            out += s
            n -= v
    return out

def exp_to_next(level):
    """EXP curve dasar untuk phase 1."""
    return int(50 + (level ** 1.6))
