"""Day/Night cycle — affects gameplay."""
import time


def hour():
    return time.localtime().tm_hour


def minute():
    return time.localtime().tm_min


def day_phase():
    """Return: dawn, morning, noon, afternoon, dusk, evening, night, midnight."""
    h = hour()
    if 4 <= h < 6:   return "dawn"
    if 6 <= h < 10:  return "morning"
    if 10 <= h < 14: return "noon"
    if 14 <= h < 17: return "afternoon"
    if 17 <= h < 19: return "dusk"
    if 19 <= h < 22: return "evening"
    if 22 <= h < 24: return "night"
    return "midnight"


PHASE_INFO = {
    "dawn":     {"label": "Dawn",     "icon": "🌅", "color": "yellow", "encounter_mult": 0.9,  "monster_buff": 0.9},
    "morning":  {"label": "Morning",  "icon": "🌄", "color": "yellow", "encounter_mult": 1.0,  "monster_buff": 1.0},
    "noon":     {"label": "Noon",     "icon": "☀",  "color": "yellow", "encounter_mult": 0.9,  "monster_buff": 1.0, "stamina_drain": 1.3},
    "afternoon":{"label": "Afternoon","icon": "🌇", "color": "yellow", "encounter_mult": 1.0,  "monster_buff": 1.0},
    "dusk":     {"label": "Dusk",     "icon": "🌆", "color": "magenta","encounter_mult": 1.2,  "monster_buff": 1.1},
    "evening":  {"label": "Evening",  "icon": "🌃", "color": "blue",   "encounter_mult": 1.3,  "monster_buff": 1.2, "dark_bonus": 1.2},
    "night":    {"label": "Night",    "icon": "🌙", "color": "blue",   "encounter_mult": 1.5,  "monster_buff": 1.3, "dark_bonus": 1.5},
    "midnight": {"label": "Midnight", "icon": "🌑", "color": "magenta","encounter_mult": 1.7,  "monster_buff": 1.4, "dark_bonus": 2.0},
}


def get_phase_info():
    return PHASE_INFO.get(day_phase(), PHASE_INFO["morning"])


def phase_label():
    return get_phase_info()["label"]


def phase_icon():
    return get_phase_info()["icon"]


def encounter_mult():
    return get_phase_info().get("encounter_mult", 1.0)


def monster_buff():
    return get_phase_info().get("monster_buff", 1.0)


def is_night():
    return day_phase() in ("evening", "night", "midnight")


def is_day():
    return not is_night()
