"""Global configuration for REINCARNATION."""
import os

GAME_TITLE = "REINCARNATION"
GAME_SUBTITLE = "CHRONICLES OF THE NEW WORLD"
VERSION = "0.1.0"
SAVE_VERSION = 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LANG_DIR = os.path.join(DATA_DIR, "lang")
DB_PATH = os.path.join(DATA_DIR, "game.db")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LANG_DIR, exist_ok=True)

# Rank system
RANKS = [
    {"id": 1,  "name": "Awakening",    "min": 0,   "max": 14},
    {"id": 2,  "name": "Initiate",     "min": 14,  "max": 24},
    {"id": 3,  "name": "Adventurer",   "min": 24,  "max": 42},
    {"id": 4,  "name": "Veteran",      "min": 42,  "max": 60},
    {"id": 5,  "name": "Elite",        "min": 60,  "max": 80},
    {"id": 6,  "name": "Master",       "min": 80,  "max": 100},
    {"id": 7,  "name": "Grandmaster",  "min": 100, "max": 145},
    {"id": 8,  "name": "Transcendent", "min": 145, "max": 190},
    {"id": 9,  "name": "Sovereign",    "min": 190, "max": 250},
    {"id": 10, "name": "Worldbreaker", "min": 250, "max": 600},
]

MAX_LEVEL_NORMAL = 600
MAX_LEVEL_CIT = 1111
STARTING_LEVEL = 15
ATTRIBUTE_POINTS_PER_LEVEL = 3
STARTING_ATTRIBUTE_POINTS = 15

# Stats dasar
STAT_KEYS = [
    "strength", "intelligence", "defense", "endurance",
    "dexterity", "agility", "speed", "jump",
    "mana", "hp", "stamina", "swimming",
    "perception", "stealth", "luck", "critical",
    "accuracy", "carry", "mining", "gathering",
    "crafting", "persuasion",
]

DEFAULT_STATS = {
    "strength": 5, "intelligence": 5, "defense": 5, "endurance": 5,
    "dexterity": 5, "agility": 5, "speed": 5, "jump": 3,
    "mana": 5, "hp": 10, "stamina": 8, "swimming": 3,
    "perception": 5, "stealth": 3, "luck": 5, "critical": 3,
    "accuracy": 5, "carry": 10, "mining": 1, "gathering": 1,
    "crafting": 1, "persuasion": 3,
}

# Loading stages (untuk loading screen)
LOADING_STAGES = [
    "Initializing Core",
    "Loading Account System",
    "Loading Character Data",
    "Loading World",
    "Loading Kingdoms",
    "Loading Cities",
    "Loading Guilds",
    "Loading NPCs",
    "Loading Monsters",
    "Loading Quest Database",
    "Loading Items",
    "Loading Skills",
    "Loading Story",
    "Synchronizing World State",
    "Awakening Character",
]
