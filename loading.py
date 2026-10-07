"""Loading screen with animated progress bar + random messages."""
import time, random, sys
from ui import C, color, clear, term_width, _strip_ansi
from config import LOADING_STAGES, GAME_TITLE, GAME_SUBTITLE

TITLE_SMALL = r"""
╦═╗╔═╗╦╔╗╔╔═╗╔═╗╦═╗╔╗╔╔═╗╔╦╗╦╔═╗╔╗╔
╠╦╝║╣ ║║║║║  ╠═╣╠╦╝║║║╠═╣ ║ ║║ ║║║║
╩╚═╚═╝╩╝╚╝╚═╝╩ ╩╩╚═╝╚╝╩ ╩ ╩ ╩╚═╝╝╚╝
""".strip("\n")

TITLE_BIG = r"""
██████╗ ███████╗██╗███╗   ██╗ ██████╗ █████╗ ██████╗ ███╗   ██╗ █████╗ ████████╗██╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██║████╗  ██║██╔════╝██╔══██╗██╔══██╗████╗  ██║██╔══██╗╚══██╔══╝██║██╔═══██╗████╗  ██║
██████╔╝█████╗  ██║██╔██╗ ██║██║     ███████║██████╔╝██╔██╗ ██║███████║   ██║   ██║██║   ██║██╔██╗ ██║
██╔══██╗██╔══╝  ██║██║╚██╗██║██║     ██╔══██║██╔══██╗██║╚██╗██║██╔══██║   ██║   ██║██║   ██║██║╚██╗██║
██║  ██║███████╗██║██║ ╚████║╚██████╗██║  ██║██║  ██║██║ ╚████║██║  ██║   ██║   ██║╚██████╔╝██║ ╚████║
╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
""".strip("\n")

MESSAGES = [
    "Awakening another soul...",
    "Opening the gates of the new world...",
    "Remembering a forgotten life...",
    "Summoning the adventurer guilds...",
    "Searching for ancient magic...",
    "Preparing the first encounter...",
    "Synchronizing the world...",
    "The world remembers...",
    "Your second life is beginning...",
    "Loading ancient memories...",
]

TIPS = [
    ("TIP",  "Some monsters change their abilities\nwhen exposed to elemental crystals."),
    ("LORE", "The five kingdoms were once a single empire."),
    ("TIP",  "Higher reputation unlocks exclusive\nguild quests."),
    ("LORE", "They say every reincarnated soul\ncarries a fragment of the old world."),
]

def _fit(text):
    w = term_width()
    if any(len(l) > w for l in text.splitlines()):
        return TITLE_SMALL
    return text

def _center(text, w):
    out = []
    for line in text.splitlines():
        s = _strip_ansi(line)
        pad = max(0, (w - len(s)) // 2)
        out.append(" " * pad + line)
    return "\n".join(out)

def show(total_time=6.0, quick=False, message=None):
    """Loading screen. total_time in seconds."""
    if quick:
        total_time = 1.2

    clear()
    w = term_width()
    title = _fit(TITLE_BIG)

    # frame 1: title only
    print()
    print(color(_center(title, w), C.CYAN + C.BOLD))
    print(color(_center(GAME_SUBTITLE, w), C.MAGENTA))
    print()
    print(color(_center("— PRESS CTRL+C TO ABORT —", w), C.DIM))
    time.sleep(0.6)

    stages = LOADING_STAGES
    steps = len(stages)
    start = time.time()
    done = False
    last_msg = message or random.choice(MESSAGES)

    try:
        while not done:
            elapsed = time.time() - start
            pct = min(100, int(elapsed / total_time * 100))
            idx = min(steps - 1, pct * steps // 100)
            stage = stages[idx]

            clear()
            print()
            print(color(_center(title, w), C.CYAN + C.BOLD))
            print(color(_center(GAME_SUBTITLE, w), C.MAGENTA))
            print()
            print("  " + color("┌" + "─" * (w - 4) + "┐", C.GRAY))
            print("  " + color("│", C.GRAY) +
                  f" {color(f'[{idx+1:02d}/{steps:02d}]', C.YELLOW)} {stage:<30}" +
                  color("│", C.GRAY))
            print("  " + color("├" + "─" * (w - 4) + "┤", C.GRAY))
            bar = _bar(pct, w - 8)
            print("  " + color("│", C.GRAY) + " " + bar + " " + color("│", C.GRAY))
            print("  " + color("├" + "─" * (w - 4) + "┤", C.GRAY))
            print("  " + color("│", C.GRAY) +
                  f" {color(last_msg, C.DIM):<{w - 4}}" + color("│", C.GRAY))
            print("  " + color("└" + "─" * (w - 4) + "┘", C.GRAY))

            # random tip on higher progress
            if pct > 40 and random.random() < 0.25:
                tag, txt = random.choice(TIPS)
                print()
                print(color(f"  [{tag}] ", C.MAGENTA) + color(txt.replace("\n", "\n       "), C.GRAY))

            if pct >= 100:
                done = True
            time.sleep(0.12)
    except KeyboardInterrupt:
        print("\n" + color("  Loading dibatalkan.", C.RED))
        raise

    # short finish flash
    clear()
    print()
    print(color(_center(title, w), C.CYAN + C.BOLD))
    print(color(_center(GAME_SUBTITLE, w), C.MAGENTA))
    print()
    print(color(_center("▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  READY  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓", w), C.GREEN))
    time.sleep(0.5)

def _bar(pct, width):
    width = max(10, width)
    filled = int(width * pct / 100)
    col = C.GREEN if pct > 66 else C.YELLOW if pct > 33 else C.RED
    b = "█" * filled + "░" * (width - filled)
    return f"{col}{b}{C.RESET} {pct:3d}%"
