"""Balancing — centralized tuning untuk combat, economy, progression.

Semua magic number ada di sini supaya mudah di-tuning.
Combat dan sistem lain dapat memakai nilai dari modul ini.
"""

# ============================================================
# DAMAGE
# ============================================================
DAMAGE = {
    "physical_str_mult": 2.0,
    "physical_level_mult": 2.0,
    "magic_int_mult": 3.0,
    "magic_level_mult": 2.0,
    "defense_div": 2.0,             # defense dibagi untuk efek
    "crit_mult_base": 1.5,          # multiplier default crit
    "crit_mult_cap": 3.0,           # max crit
    "variance_min": 0.9,
    "variance_max": 1.1,
    "heavy_mult": 1.7,
    "quick_mult": 0.6,
    "skill_min_mult": 1.0,
    "skill_max_mult": 6.0,
    "min_damage": 1,
}

# ============================================================
# HIT / ACCURACY
# ============================================================
HIT = {
    "base_accuracy": 5,
    "accuracy_floor": 5,            # minimal roll untuk hit
    "miss_threshold": 5,
    "crit_chance_div": 200.0,       # (crit + luck)/200
    "dodge_chance_base": 0.30,
    "dodge_agi_div": 100.0,
}

# ============================================================
# ESCAPE
# ============================================================
ESCAPE = {
    "base_chance": 0.35,
    "spd_div": 100.0,
    "min_chance": 0.05,
    "max_chance": 0.9,
}

# ============================================================
# EXP / LEVEL
# ============================================================
EXP = {
    "level_formula_base": 50,
    "level_formula_exp": 1.6,
    "monster_exp_mult": 1.0,
    "quest_exp_mult": 1.0,
    "gather_exp_mult": 1.0,
    "cit_multiplier": 1.5,
    "attribute_points_per_level": 3,
}

# ============================================================
# ECONOMY
# ============================================================
ECONOMY = {
    "silver_to_gold": 100,
    "gold_to_zambrut": 100,
    "sell_price_mult": 0.4,
    "buy_price_mult_base": 1.0,
    "capital_price_mult": 1.15,
    "city_price_mult": 1.05,
    "village_price_mult": 0.9,
    "reputation_discount_max": 0.10,
    "black_market_fake_chance": 0.15,
}

# ============================================================
# COMBAT ROLL
# ============================================================
COMBAT = {
    "player_first_spd_roll": 5,     # random 0-5
    "max_turns": 50,
    "timeout_result": "timeout",
    "enemy_flee_chance": 0.5,
    "enemy_defend_chance": 0.3,
    "enemy_spell_chance": 0.5,
    "enemy_ambush_chance": 0.6,
    "enemy_special_hp_threshold": 0.5,
    "enemy_special_chance": 0.4,
}

# ============================================================
# MONSTER SCALING
# ============================================================
MONSTER = {
    "scale_factor_per_level": 0.08,
    "min_scale": 0.3,
    "mutation_chance_normal": 0.02,
    "mutation_chance_rare": 0.06,
    "mutation_hp_mult": 1.5,
    "mutation_atk_mult": 1.4,
    "mutation_def_mult": 1.2,
    "mutation_exp_mult": 2.0,
}

# ============================================================
# DUNGEON
# ============================================================
DUNGEON = {
    "base_floors_min": 3,
    "base_floors_max": 7,
    "trap_damage_min": 20,
    "trap_damage_max": 60,
    "rest_heal_pct": 0.25,
    "boss_bonus_silver": 200,
    "boss_bonus_gold": 2,
}

# ============================================================
# FARMING / CRAFTING
# ============================================================
LIFE = {
    "crop_water_bonus_mult": 0.4,
    "crop_max_speedup": 0.8,
    "crop_yield_water_bonus_div": 2,
    "crafting_fail_chance": 0.0,    # untuk sekarang selalu berhasil
    "upgrade_base_chance": 0.95,
    "upgrade_chance_decay": 0.08,
    "upgrade_min_chance": 0.30,
    "upgrade_silver_mult": 0.5,
    "upgrade_silver_exp_base": 1.5,
}

# ============================================================
# ENCOUNTER
# ============================================================
ENCOUNTER = {
    "base_encounter_chance": 0.55,
    "danger_mult_per_level": 0.08,
    "danger_mult_base": 0.8,
    "treasure_search_base": 0.20,
    "hidden_location_chance": 0.35,
    "boss_encounter_chance": 0.03,
}

# ============================================================
# DEATH PENALTY
# ============================================================
DEATH = {
    "exp_loss_pct": 0.10,
    "hp_on_respawn": 1,
    "durability_loss": 0,
    "item_loss_chance": 0.0,
}


def damage_roll(attack, defense, mult=1.0):
    """Standard damage formula."""
    raw = (attack * mult) - (defense / DAMAGE["defense_div"])
    return max(DAMAGE["min_damage"], int(raw))


def crit_multiplier(crit_damage_bonus_pct=50):
    base = DAMAGE["crit_mult_base"]
    extra = crit_damage_bonus_pct / 100.0
    return min(DAMAGE["crit_mult_cap"], base + extra)


def exp_to_next(level):
    return int(EXP["level_formula_base"] + (level ** EXP["level_formula_exp"]))


def monster_scale_factor(base_level, new_level):
    f = 1 + (new_level - base_level) * MONSTER["scale_factor_per_level"]
    return max(MONSTER["min_scale"], f)
