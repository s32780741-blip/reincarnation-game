"""Cutscene player — animated text."""
import time
import sys
from ui import C, color, clear, box, prompt, pause, term_width
import settings


def _type(text, delay=None):
    if delay is None:
        delay = settings.type_delay()
    if delay <= 0:
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def play_scene(scene):
    stype = scene.get("type")
    if stype == "narration":
        clear()
        w = term_width()
        print()
        print(color(" " + "─" * (w - 2), C.GRAY))
        print()
        _type("  " + scene["text"])
        print()
        print(color(" " + "─" * (w - 2), C.GRAY))
        pause()
    elif stype == "voice":
        clear()
        who = scene.get("who", "???")
        print()
        print(color(f"  {who}:", C.YELLOW + C.BOLD))
        _type(f"  \"{scene['text']}\"")
        print()
        pause()
    elif stype == "memory":
        clear()
        print(color(" ╭─ MEMORY FRAGMENT ─╮", C.MAGENTA))
        _type(color(" " + scene["text"], C.MAGENTA))
        print(color(" ╰────────────────────╯", C.MAGENTA))
        pause()
    elif stype == "hint":
        clear()
        print(box("HINT", [
            color(f" {scene['text']}", C.CYAN),
        ]))
        pause()


def play_chapter(chapter):
    """Play semua scene dari chapter."""
    clear()
    print(box("CHAPTER", [
        color(f" {chapter['title']}", C.YELLOW + C.BOLD),
        "",
        color(chapter.get("desc", ""), C.GRAY),
        "",
        f" Lokasi: {chapter.get('location', '?')}",
        f" Req. Level: {chapter.get('level_req', 0)}",
    ]))
    pause(" Tekan Enter untuk memulai...")

    for scene in chapter.get("scenes", []):
        play_scene(scene)

    clear()
    print(box("CHAPTER COMPLETE", [
        color(f" {chapter['title']} selesai!", C.GREEN + C.BOLD),
        "",
        " Cerita berlanjut...",
    ]))
    pause()
