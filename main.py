"""REINCARNATION: CHRONICLES OF THE NEW WORLD — FINAL main entry.

Phase 1-12 terintegrasi:
- Phase 1 : Account, Character, Save, Settings, Rank
- Phase 2 : Role, Skill, Mastery, Mentor, Training
- Phase 3 : World, Kingdom, City, Teleport
- Phase 4 : Combat, Monster, Element, Loot, Inventory, Hunt
- Phase 5 : Quest, Bounty, Achievement, Reputation
- Phase 6 : Guild, NPC, Examination, Recruitment
- Phase 7 : Market, Equipment, Blacksmith, Black Market
- Phase 8 : Crafting, Mining, Gathering, Farming, Cooking
- Phase 9 : Explore, Weather, Events, Dungeon, World Boss
- Phase 10: Story, Lore, Endings
- Phase 11: Race System, CIT MODE, Secret Commands
- Phase 12: Balancing, NG+, Post-game
"""
import sys
import os
import time

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import config
import database as db
import settings
from ui import C, color, clear, box, prompt, pause, term_width
from i18n import t
import loading
import account as account_mod
from rank import rank_text, exp_to_next
from character import (
    show_status, spend_attr_points, grant_exp,
    create_character_flow, max_hp, max_mp, max_stamina,
)


def _lang():
    return settings.get("language", "id")


# ============================================================
# SETTINGS MENU
# ============================================================
def settings_menu():
    while True:
        lang = _lang()
        s = settings.load()
        clear()
        lines = [
            f" 1. {t('settings.language', lang)}       : {s['language']}",
            f" 2. {t('settings.text_speed', lang)}     : {s['text_speed']}",
            f" 3. {t('settings.animation', lang)}      : {s['animation']}",
            f" 4. {t('settings.auto_save', lang)}      : {s['auto_save']}",
            f" 5. {t('settings.confirm_actions', lang)}: {s['confirm_actions']}",
            "",
            " 0. Kembali",
        ]
        print(box("SETTINGS", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        elif ch == "1":
            settings.set_value("language", "en" if s["language"] == "id" else "id")
        elif ch == "2":
            opts = ["slow", "normal", "fast", "instant"]
            try:
                idx = (opts.index(s["text_speed"]) + 1) % len(opts)
            except ValueError:
                idx = 1
            settings.set_value("text_speed", opts[idx])
        elif ch == "3":
            settings.set_value("animation", not s["animation"])
        elif ch == "4":
            settings.set_value("auto_save", not s["auto_save"])
        elif ch == "5":
            settings.set_value("confirm_actions", not s["confirm_actions"])
        else:
            print(color(" Invalid.", C.RED))
            pause()


# ============================================================
# SECRET COMMAND HANDLER (Phase 11)
# ============================================================
def _handle_secret_command(character_id, cmd):
    """Return True kalau command dikenali."""
    try:
        from race_menu import handle_secret_command
        return handle_secret_command(character_id, cmd)
    except Exception as e:
        print(color(f" Secret cmd error: {e}", C.RED))
        pause()
        return False


# ============================================================
# NEW GAME+ MENU (Phase 12)
# ============================================================
def _ng_plus_menu(character_id):
    from ng_plus import get_ng_plus_level, can_start_ng_plus, apply_ng_plus, ng_bonus_label

    while True:
        clear()
        ng = get_ng_plus_level(character_id)
        ok, reason = can_start_ng_plus(character_id)
        bonus = ng_bonus_label(character_id)

        lines = [
            f" NG+ Level : {ng}",
            f" Bonus     : {bonus if bonus else '(belum NG+)'}",
            "",
            color("BONUS SETIAP NG+:", C.YELLOW),
            "  +10% EXP",
            "  +5%  Gold reward",
            "  +5   attr points awal",
            "  +500 Silver awal",
            "  +5   Gold awal",
            "",
        ]
        if ok:
            lines.append(" 1. Mulai New Game+")
        else:
            lines.append(color(f" 1. (Terkunci) {reason}", C.YELLOW))
        lines.append(" 0. Kembali")
        print(box("NEW GAME+", lines))
        ch = prompt("> ")
        if ch == "0":
            return
        if ch == "1" and ok:
            clear()
            print(box("NG+ KONFIRMASI", [
                color(" Mulai New Game+?", C.YELLOW + C.BOLD),
                "",
                " Level & inventory akan di-reset ke awal.",
                " Achievement, story, lore, CIT tetap tersimpan.",
                "",
                " 1. Ya, mulai NG+",
                " 0. Batal",
            ]))
            if prompt("> ") != "1":
                continue
            success, result = apply_ng_plus(character_id)
            if success:
                try:
                    db.log_ng_plus(character_id, result)
                except Exception:
                    pass
                clear()
                print(box("NG+ DIMULAI", [
                    color(f" ★ NG+{result} DIMULAI!", C.MAGENTA + C.BOLD),
                    "",
                    f" +{5 * result} attr points awal",
                    f" +{500 * result} silver",
                    f" +{5 * result} gold",
                    "",
                    color(" Dunia baru menantimu.", C.CYAN),
                ]))
                pause()
                return
            else:
                print(color(f" ✗ {result}", C.RED))
                pause()


# ============================================================
# IN-GAME MENU (Phase 1-12)
# ============================================================
def in_game_menu(character_id):
    while True:
        char = db.get_character(character_id)
        if not char:
            return
        clear()
        stats = db.get_stats(character_id)
        mhp = max_hp(stats, char["level"])
        mmp = max_mp(stats, char["level"])
        mst = max_stamina(stats, char["level"])
        exp_need = exp_to_next(char["level"])

        # Info lokasi (Phase 3)
        try:
            from cities import get_city
            city = get_city(char["location"])
            city_name = city["name"] if city else char["location"]
            kingdom_id = city["kingdom"] if city else "?"
        except Exception:
            city_name = char["location"]
            kingdom_id = "?"

        attr_info = f" ({char['attr_points']})" if char["attr_points"] else ""

        # Quest & bounty (Phase 5)
        try:
            active_q = len(db.get_quests(character_id, status="active"))
            ready_b = len(db.get_bounties(character_id, status="ready_to_turn_in"))
        except Exception:
            active_q = 0
            ready_b = 0

        # Guild (Phase 6)
        try:
            from guild_system import get_player_guild
            pg = get_player_guild(character_id)
            if pg:
                from guilds import guild_name
                guild_line = f" Guild: {guild_name(pg['guild_id'])} [{pg['rank']}]"
            else:
                guild_line = " Guild: (belum bergabung)"
        except Exception:
            guild_line = ""

        # Waktu (Phase 6/9)
        try:
            from daynight import phase_icon, phase_label
            time_line = f" Waktu : {phase_icon()} {phase_label()}"
        except Exception:
            try:
                from npc import time_label
                time_line = f" Waktu : {time_label()}"
            except Exception:
                time_line = ""

        # Story progress (Phase 10)
        try:
            from story import progress_percent
            story_pct = progress_percent(character_id)
            story_line = f" Story : {story_pct}% selesai"
        except Exception:
            story_line = ""

        # Race info (Phase 11)
        try:
            from races import race_name
            race_line = f" Race  : {race_name(char['race'])}"
        except Exception:
            race_line = f" Race  : {char['race']}"

        # CIT badge + NG+ badge
        try:
            from cit_mode import is_cit_active
            cit_badge = color(" [CIT]", C.MAGENTA + C.BOLD) if is_cit_active(character_id) else ""
        except Exception:
            cit_badge = ""

        try:
            from ng_plus import get_ng_plus_level
            ng = get_ng_plus_level(character_id)
            ng_badge = color(f" [NG+{ng}]", C.YELLOW + C.BOLD) if ng > 0 else ""
        except Exception:
            ng_badge = ""

        lines = [
            color(f" {char['name']}", C.CYAN + C.BOLD) + cit_badge + ng_badge +
            f"  Lv {char['level']}  " + rank_text(char["level"], bool(char.get("cit_mode"))),
            race_line,
            f" HP {char['hp_current']}/{mhp}  MP {char['mp_current']}/{mmp}  ST {char['stamina_current']}/{mst}",
            f" EXP {char['exp']}/{exp_need}",
            f" Lokasi : {city_name} ({kingdom_id})",
            time_line,
            f" Currency: {char['silver']}s  {char['gold']}g  {char['zambrut']}z",
            f" Quests: {active_q} aktif    Bounties: {ready_b} siap klaim",
            guild_line,
            story_line,
            "",
            " ── CHARACTER ──",
            " 1. Status",
            " 2. Role & Skill",
            " 3. Training",
            " 4. Alokasi Attribute" + attr_info,
            " 5. Inventory & Equipment",
            " ── ACTIVITY ──",
            " 6. Hunt / Adventure",
            " 7. Explore",
            " 8. Quest Journal",
            " 9. Bounty Board",
            " k. World",
            " ── LIFE ──",
            " a. Crafting",
            " b. Mining & Gathering",
            " c. Farming & Cooking",
            " ── SOCIAL ──",
            " d. Market",
            " e. Blacksmith",
            " f. Guild",
            " g. People (NPC)",
            " ── STORY ──",
            " l. Story",
            " m. Lore Archive",
            " ── RACE ──",
            " r. Race & CIT",
            " ── POST-GAME ──",
            " n. Post-game (Endless, Arena, Boss Rush)",
            " o. New Game+",
            " ── META ──",
            " h. Achievements & Reputation",
            " i. Save",
            " j. Settings",
            " 0. Logout",
            "",
            color(" Tip: /cit untuk coba unlock CIT MODE", C.DIM),
        ]
        print(box("MAIN MENU", lines))
        ch = prompt("> ").lower()

        # ============================================================
        # SECRET COMMAND (Phase 11)
        # ============================================================
        if ch.startswith("/"):
            if _handle_secret_command(character_id, ch):
                continue
            print(color(" Unknown command.", C.RED))
            pause()
            continue

        # ============================================================
        # LOGOUT
        # ============================================================
        if ch == "0":
            if settings.get("auto_save", True):
                db.update_character(character_id)
                print(color(" [✓] Progress tersimpan (autosave).", C.GREEN))
            print(color(" Logout...", C.GRAY))
            time.sleep(0.6)
            return

        # ============================================================
        # CHARACTER
        # ============================================================
        elif ch == "1":
            show_status(character_id)

        elif ch == "2":
            try:
                from role_menu import role_menu
                role_menu(character_id)
            except Exception as e:
                print(color(f" Role error: {e}", C.RED))
                pause()

        elif ch == "3":
            try:
                from training import training_menu
                training_menu(character_id)
            except Exception as e:
                print(color(f" Training error: {e}", C.RED))
                pause()

        elif ch == "4":
            if char["attr_points"] <= 0:
                print(color(" Tidak ada poin.", C.YELLOW))
                pause()
            else:
                spend_attr_points(character_id)

        elif ch == "5":
            try:
                from inventory_menu import inventory_menu
                inventory_menu(character_id)
            except Exception as e:
                print(color(f" Inventory error: {e}", C.RED))
                pause()

        # ============================================================
        # ACTIVITY
        # ============================================================
        elif ch == "6":
            try:
                from hunt import hunt_menu
                hunt_menu(character_id)
            except Exception as e:
                print(color(f" Hunt error: {e}", C.RED))
                pause()

        elif ch == "7":
            try:
                from explore_menu import explore_menu
                explore_menu(character_id)
            except Exception as e:
                print(color(f" Explore error: {e}", C.RED))
                pause()

        elif ch == "8":
            try:
                from quest_menu import quest_menu
                quest_menu(character_id)
            except Exception as e:
                print(color(f" Quest error: {e}", C.RED))
                pause()

        elif ch == "9":
            try:
                from bounty_menu import bounty_menu
                bounty_menu(character_id)
            except Exception as e:
                print(color(f" Bounty error: {e}", C.RED))
                pause()

        elif ch == "k":
            try:
                from world_menu import world_menu
                world_menu(character_id)
            except Exception as e:
                print(color(f" World error: {e}", C.RED))
                pause()

        # ============================================================
        # LIFE (Phase 8)
        # ============================================================
        elif ch == "a":
            try:
                from crafting_menu import crafting_menu
                crafting_menu(character_id)
            except Exception as e:
                print(color(f" Crafting error: {e}", C.RED))
                pause()

        elif ch == "b":
            try:
                from resource_menu import resource_menu
                resource_menu(character_id)
            except Exception as e:
                print(color(f" Resource error: {e}", C.RED))
                pause()

        elif ch == "c":
            try:
                from life_menu import life_menu
                life_menu(character_id)
            except Exception as e:
                print(color(f" Life error: {e}", C.RED))
                pause()

        # ============================================================
        # SOCIAL
        # ============================================================
        elif ch == "d":
            try:
                from market_menu import market_menu
                market_menu(character_id)
            except Exception as e:
                print(color(f" Market error: {e}", C.RED))
                pause()

        elif ch == "e":
            try:
                from blacksmith_menu import blacksmith_menu
                blacksmith_menu(character_id)
            except Exception as e:
                print(color(f" Blacksmith error: {e}", C.RED))
                pause()

        elif ch == "f":
            try:
                from guild_menu import guild_menu
                guild_menu(character_id)
            except Exception as e:
                print(color(f" Guild error: {e}", C.RED))
                pause()

        elif ch == "g":
            try:
                from npc_menu import npc_menu
                npc_menu(character_id)
            except Exception as e:
                print(color(f" NPC error: {e}", C.RED))
                pause()

        # ============================================================
        # STORY (Phase 10)
        # ============================================================
        elif ch == "l":
            try:
                from story_menu import story_menu
                story_menu(character_id)
            except Exception as e:
                print(color(f" Story error: {e}", C.RED))
                pause()

        elif ch == "m":
            try:
                from lore import lore_menu
                lore_menu(character_id)
            except Exception as e:
                print(color(f" Lore error: {e}", C.RED))
                pause()

        # ============================================================
        # RACE (Phase 11)
        # ============================================================
        elif ch == "r":
            try:
                from race_menu import race_menu
                race_menu(character_id)
            except Exception as e:
                print(color(f" Race error: {e}", C.RED))
                pause()

        # ============================================================
        # POST-GAME & NG+ (Phase 12)
        # ============================================================
        elif ch == "n":
            try:
                from postgame_menu import postgame_menu
                postgame_menu(character_id)
            except Exception as e:
                print(color(f" Post-game error: {e}", C.RED))
                pause()

        elif ch == "o":
            _ng_plus_menu(character_id)

        # ============================================================
        # META
        # ============================================================
        elif ch == "h":
            try:
                from achievement_menu import achievement_menu
                achievement_menu(character_id)
            except Exception as e:
                print(color(f" Achievement error: {e}", C.RED))
                pause()

        elif ch == "i":
            try:
                from save_system import save_menu
                save_menu(character_id)
            except Exception as e:
                print(color(f" Save error: {e}", C.RED))
                pause()

        elif ch == "j":
            settings_menu()

        else:
            print(color(" Invalid.", C.RED))
            pause()


# ============================================================
# BOOT
# ============================================================
def boot():
    # Init DB
    try:
        db.init()
    except Exception as e:
        print(color(f" DB init gagal: {e}", C.RED))
        sys.exit(1)

    # Loading screen utama
    try:
        loading.show(total_time=6.0)
    except KeyboardInterrupt:
        print(color(" Keluar.", C.RED))
        sys.exit(0)

    # Account flow
    while True:
        acc = account_mod.account_menu()
        if not acc:
            print(color(" Sampai jumpa.", C.CYAN))
            break

        while True:
            cid = account_mod.account_hub(acc)
            if cid is None:
                break  # logout

            # Pastikan character valid
            char = db.get_character(cid)
            if not char:
                print(color(" Karakter tidak ditemukan.", C.RED))
                pause()
                break

            # Loading masuk dunia
            try:
                loading.show(
                    total_time=2.5,
                    message="Your second life is beginning...",
                )
            except KeyboardInterrupt:
                pass

            # Mark kota awal visited
            try:
                db.mark_city_visited(cid, char["location"])
            except Exception:
                pass

            # Pastikan plot farming ada
            try:
                db.ensure_farming_plots(cid, 6)
            except Exception:
                pass

            in_game_menu(cid)


# ============================================================
# ENTRY POINT
# ============================================================
def main():
    try:
        boot()
    except KeyboardInterrupt:
        print()
        print(color(" Game dihentikan.", C.YELLOW))
    except Exception as e:
        print()
        print(color(f" [FATAL] {e}", C.RED))
        import traceback
        traceback.print_exc()
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
