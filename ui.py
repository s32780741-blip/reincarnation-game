"""Terminal UI helpers — ANSI colors, boxes, progress bars."""
import os
import sys
import time
import shutil

# ANSI colors
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_width(default=52):
    try:
        return min(shutil.get_terminal_size((default, 24)).columns, 78)
    except Exception:
        return default

def color(text, col):
    return f"{col}{text}{C.RESET}"

def hr(char="─", width=None):
    return char * (width or term_width())

def box(title, lines, width=None):
    """Draw a bordered box. lines = list of strings."""
    w = width or term_width()
    inner = w - 4
    top = "╔" + "═" * (w - 2) + "╗"
    bottom = "╚" + "═" * (w - 2) + "╝"
    out = [top]
    if title:
        t = f" {title} "
        pad = (w - 2 - len(t)) // 2
        out.append("║" + " " * pad + color(t, C.BOLD + C.CYAN) + " " * (w - 2 - pad - len(t)) + "║")
        out.append("╠" + "═" * (w - 2) + "╣")
    for ln in lines:
        # strip ANSI for length
        stripped = _strip_ansi(ln)
        if len(stripped) > inner:
            ln = ln[:inner]
            stripped = stripped[:inner]
        out.append("║ " + ln + " " * (inner - len(stripped)) + " ║")
    out.append(bottom)
    return "\n".join(out)

def _strip_ansi(s):
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)

def progress_bar(pct, width=20, fill="█", empty="░", color_on=True):
    pct = max(0, min(100, pct))
    filled = int(width * pct / 100)
    bar = fill * filled + empty * (width - filled)
    if color_on:
        col = C.GREEN if pct > 66 else C.YELLOW if pct > 33 else C.RED
        bar = color(bar, col)
    return f"[{bar}] {pct:3d}%"

def typewrite(text, delay=0.015):
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def prompt(text="> "):
    try:
        return input(color(text, C.CYAN)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return ""

def safe_int(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def pause(msg="Tekan Enter untuk lanjut..."):
    try:
        input(color(msg, C.GRAY))
    except (EOFError, KeyboardInterrupt):
        pass
