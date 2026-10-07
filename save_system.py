"""Save / Load system — berbasis SQLite (character sebagai save)."""
import time
from ui import C, color, clear, box, prompt, pause
from i18n import t
import database as db
import settings

def _lang():
    return settings.get("language", "id")

def autosave(character_id, silent=False):
    if not settings.get("auto_save", True):
        return
    try:
        db.update_character(character_id)  # touch updated_at
        if not silent:
            print(color(" [✓] Progress tersimpan.", C.GREEN))
    except Exception as e:
        print(color(f" [!] Autosave gagal: {e}", C.RED))

def save_menu(character_id):
    lang = _lang()
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        clear()
        from rank import rank_text
        lines = [
            f" Character : {char['name']}",
            f" Level     : {char['level']}",
            f" Rank      : {rank_text(char['level'], bool(char.get('cit_mode')))}",
            f" Location  : {char['location']}",
            "",
            " 1. Simpan sekarang",
            " 2. Lihat info save",
            " 0. Kembali",
        ]
        print(box("SAVE", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            autosave(character_id)
            pause()
        elif ch == "2":
            clear()
            print(box("SAVE INFO", [
                f" ID        : {char['id']}",
                f" Dibuat    : {time.strftime('%Y-%m-%d %H:%M', time.localtime(char['created_at']))}",
                f" Diperbarui: {time.strftime('%Y-%m-%d %H:%M', time.localtime(char['updated_at']))}",
            ]))
            pause()

def delete_character_confirm(character_id):
    clear()
    print(box("HAPUS KARAKTER", [
        color("PERINGATAN!", C.RED + C.BOLD),
        "Karakter ini akan dihapus permanen.",
        "",
        " 1. Ya, hapus",
        " 0. Batal",
    ]))
    if prompt("> ") == "1":
        db.delete_character(character_id)
        print(color(" Karakter dihapus.", C.YELLOW))
        pause()
        return True
    return False
