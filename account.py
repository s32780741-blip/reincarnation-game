"""Account creation & login flow — FIXED untuk Termux Android.

getpass() tidak bekerja normal di Termux. Gunakan input() biasa
dengan masking manual (tampilkan karakter *).
"""
import sys
from ui import C, color, clear, box, prompt, pause
from i18n import t
import database as db
import settings


def _lang():
    return settings.get("language", "id")


# ============================================================
# PASSWORD INPUT — FIX untuk Termux
# ============================================================
def _ask_password(label):
    """
    Input password tanpa getpass (fix bug Termux).
    
    Coba masking manual dulu. Kalau gagal, fallback ke input() biasa.
    """
    label_colored = color(f"{label}: ", C.CYAN)

    # Coba masking manual (Linux style)
    try:
        import termios, tty
        print(label_colored, end="", flush=True)
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            chars = []
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    print()
                    break
                elif ch == "\x7f" or ch == "\b":  # backspace
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                elif ch == "\x03":  # Ctrl+C
                    raise KeyboardInterrupt
                else:
                    chars.append(ch)
                    sys.stdout.write("*")
                    sys.stdout.flush()
            return "".join(chars).strip()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        # Fallback: input biasa (terlihat di layar, tapi bekerja di Termux)
        try:
            return input(label_colored).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return ""


# ============================================================
# ACCOUNT MENU
# ============================================================
def account_menu():
    lang = _lang()
    while True:
        clear()
        lines = [
            f" 1. {t('menu.login', lang)}",
            f" 2. {t('menu.create_account', lang)}",
            f" 3. {t('menu.exit', lang)}",
            "",
        ]
        print(box(t("app.title", lang), [
            color(t("app.subtitle", lang), C.MAGENTA),
            "",
            *lines,
        ]))
        choice = prompt("> ")
        if choice == "1":
            acc = do_login()
            if acc:
                return acc
        elif choice == "2":
            do_create()
        elif choice == "3":
            return None
        else:
            print(color(f" {t('common.invalid', lang)}", C.RED))
            pause()


# ============================================================
# LOGIN
# ============================================================
def do_login():
    lang = _lang()
    clear()
    print(box(t("menu.login", lang), [
        f"{t('account.username', lang)} :",
        f"{t('account.password', lang)} :",
    ]))
    u = prompt(f"{t('account.username', lang)}: ")
    if not u:
        print(color(f" {t('common.invalid', lang)}", C.RED))
        pause()
        return None
    p = _ask_password(t("account.password", lang))
    if not p:
        print(color(f" {t('common.invalid', lang)}", C.RED))
        pause()
        return None

    acc = db.verify_login(u, p)
    if acc:
        print(color(f"\n ✓ {t('account.login_ok', lang)}", C.GREEN))
        print(color(f"   Welcome back, {acc['username']}.", C.WHITE))
        pause()
        return acc
    print(color(f"\n ✗ {t('account.login_fail', lang)}", C.RED))
    pause()
    return None


# ============================================================
# CREATE ACCOUNT
# ============================================================
def do_create():
    lang = _lang()
    clear()
    print(box(t("menu.create_account", lang), [
        f"{t('account.username', lang)} :",
        f"{t('account.password', lang)} :",
        f"{t('account.confirm', lang)} :",
    ]))
    u = prompt(f"{t('account.username', lang)}: ")
    if not u:
        print(color(f" {t('common.invalid', lang)}", C.RED))
        pause()
        return
    p = _ask_password(t("account.password", lang))
    if not p:
        print(color(f" {t('common.invalid', lang)}", C.RED))
        pause()
        return
    c = _ask_password(t("account.confirm", lang))
    if p != c:
        print(color(" Password tidak sama.", C.RED))
        pause()
        return

    ok, err = db.create_account(u, p)
    if ok:
        print(color(f"\n ✓ {t('account.created', lang)}", C.GREEN))
        print(color(f"   Username: {u}", C.WHITE))
        pause()
    else:
        msg = {
            "empty_username": "Username tidak boleh kosong.",
            "short_username": "Username minimal 3 karakter.",
            "short_password": "Password minimal 4 karakter.",
            "username_exists": "Username sudah dipakai.",
        }.get(err, f"Gagal: {err}")
        print(color(f"\n ✗ {msg}", C.RED))
        pause()


# ============================================================
# ACCOUNT HUB
# ============================================================
def account_hub(account):
    lang = _lang()
    while True:
        chars = db.get_characters(account["id"])
        clear()
        lines = [
            f" Username   : {account['username']}",
            f" Characters : {len(chars)}",
            "",
            " 1. Continue",
            " 2. Character Select",
            " 3. Create Character",
            " 4. Logout",
        ]
        print(box("ACCOUNT", lines))
        ch = prompt("> ")
        if ch == "1":
            if not chars:
                print(color(" Belum ada karakter.", C.YELLOW))
                pause()
                continue
            return chars[0]["id"]
        elif ch == "2":
            cid = character_select(account)
            if cid:
                return cid
        elif ch == "3":
            from character import create_character_flow
            cid = create_character_flow(account["id"])
            return cid
        elif ch == "4":
            return None
        else:
            print(color(" Invalid.", C.RED))
            pause()


# ============================================================
# CHARACTER SELECT
# ============================================================
def character_select(account):
    chars = db.get_characters(account["id"])
    clear()
    if not chars:
        print(box("CHARACTER SELECT", [
            "",
            "   NO CHARACTER FOUND",
            "",
            "   Create your first",
            "   character to begin.",
            "",
            "   [ Tekan Enter untuk Buat Karakter ]",
            "",
        ]))
        prompt("")
        from character import create_character_flow
        return create_character_flow(account["id"])

    from rank import rank_text
    lines = []
    for i, c in enumerate(chars, 1):
        lines.append(f" {i}. {c['name']}")
        lines.append(f"    Level : {c['level']}")
        lines.append(f"    Rank  : {rank_text(c['level'])}")
        lines.append(f"    Race  : {c['race']}")
        lines.append("")
    lines.append(f" {len(chars)+1}. Create New Character")
    lines.append(f" {len(chars)+2}. Back")
    print(box("CHARACTER SELECT", lines))
    ch = prompt("> ")
    try:
        idx = int(ch)
        if 1 <= idx <= len(chars):
            return chars[idx - 1]["id"]
        elif idx == len(chars) + 1:
            from character import create_character_flow
            return create_character_flow(account["id"])
    except ValueError:
        pass
    return None
