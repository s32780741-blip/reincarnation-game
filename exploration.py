"""Exploration engine — gabungkan weather, daynight, events."""
import random
import database as db
from weather import current_weather_for_region, weather_modifier
from daynight import encounter_mult as dn_encounter_mult, is_night, phase_label


def compute_encounter_chance(base, region_id, weather, danger):
    """Chance untuk encounter (0-1)."""
    w_mult = weather_modifier(weather, "encounter_mult", 1.0)
    d_mult = 0.8 + danger * 0.08
    dn_mult = dn_encounter_mult()
    chance = base * w_mult * d_mult * dn_mult
    return min(0.95, chance)


def explore_once(character_id, region_id):
    """Satu iterasi explore. Return dict hasil."""
    from world import get_region
    region = get_region(region_id)
    if not region:
        return {"type": "error", "msg": "Region tidak ditemukan"}

    biome = region.get("biome", "plains")
    danger = region.get("danger", 1)
    weather = current_weather_for_region(region_id)

    # Roll encounter type
    base_encounter = 0.55
    chance = compute_encounter_chance(base_encounter, region_id, weather, danger)

    if random.random() > chance:
        return {"type": "nothing", "weather": weather,
                "msg": "Kamu menjelajah tanpa kejadian berarti."}

    # Roll event
    from events import roll_event
    event = roll_event(biome, exclude_types=["world_boss"])
    if not event:
        return {"type": "nothing", "weather": weather,
                "msg": "Tidak ada yang menarik."}

    return {
        "type": "event",
        "event": event,
        "weather": weather,
        "region": region,
    }


def check_world_boss(character_id, region_id):
    from world_boss import roll_boss_encounter
    return roll_boss_encounter(character_id, region_id)
