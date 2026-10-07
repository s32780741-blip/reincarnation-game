"""Turn-based combat system."""
import random, time
from ui import C, color, clear, box, prompt, pause, progress_bar
from i18n import t
import database as db
import settings
import elements as elems
from monsters import rank_color, rank_label

def _lang():
    return settings.get("language", "id")

def _calc_max_hp(stats, level):
    return 100 + stats["hp"] * 10 + level * 5

def _calc_max_mp(stats, level):
    return 50 + stats["mana"] * 8 + level * 2

# ---------- stat effect handling ----------
def _apply_mastery_bonus(char_id, dmg, kind="physical"):
    """Apply mastery passive bonuses."""
    from mastery import total_bonus
    b = total_bonus(char_id)
    pct = 0
    if kind == "physical":
        pct = b.get("damage_pct", 0)
    elif kind == "magic":
        pct = b.get("magic_damage_pct", 0)
    elif kind == "heal":
        pct = b.get("heal_pct", 0)
    return dmg * (1 + pct / 100.0)

def _player_attack_power(char, stats, weapon_bonus=0):
    base = stats["strength"] * 2 + char["level"] * 2 + weapon_bonus
    return base

def _player_magic_power(char, stats, weapon_bonus=0):
    return stats["intelligence"] * 3 + char["level"] * 2 + weapon_bonus

def _enemy_defense(m):
    return m["defense"]

def _roll_damage(attack, defense, mult=1.0, crit_chance=0.05, crit_damage=50):
    raw = (attack * mult) - (defense * 0.5)
    raw = max(1, raw)
    crit = random.random() < crit_chance
    if crit:
        raw *= (1 + crit_damage / 100.0)
    # variance ±10%
    raw *= random.uniform(0.9, 1.1)
    return int(raw), crit

# ---------- status effects ----------
def _apply_dot_and_status(entity):
    """entity = {'hp','status':{...}, ...}. Tick every turn."""
    dmg_total = 0
    for k in list(entity.get("status", {}).keys()):
        v = entity["status"][k]
        if k == "poison":
            dmg_total += max(2, entity.get("max_hp", 100) * 0.04)
        elif k == "burn":
            dmg_total += max(3, entity.get("max_hp", 100) * 0.05)
        # decrement
        v -= 1
        if v <= 0:
            del entity["status"][k]
        else:
            entity["status"][k] = v
    if dmg_total:
        entity["hp"] = max(0, entity["hp"] - int(dmg_total))
    return int(dmg_total)

# ---------- battle ----------
class Battle:
    def __init__(self, character_id, monster):
        self.cid = character_id
        self.char = db.get_character(character_id)
        self.stats = db.get_stats(character_id)
        self.m = dict(monster)
        self.m["status"] = {}
        self.p = {
            "hp": self.char["hp_current"],
            "max_hp": _calc_max_hp(self.stats, self.char["level"]),
            "mp": self.char["mp_current"],
            "max_mp": _calc_max_mp(self.stats, self.char["level"]),
            "status": {},
        }
        self.turn = 0
        self.max_turns = 50
        self.over = False
        self.result = None  # 'win' | 'lose' | 'escape' | 'timeout'
        self.total_exp = 0

    # ---------- render ----------
    def render(self, message=""):
        clear()
        from character import max_hp, max_mp
        p_hp = int(self.p["hp"] / self.p["max_hp"] * 100)
        p_mp = int(self.p["mp"] / self.p["max_mp"] * 100) if self.p["max_mp"] else 0
        m_hp = int(self.m["hp"] / self.m["max_hp"] * 100) if self.m["max_hp"] else 0
        m_mp = int(self.m["mp"] / self.m["max_mp"] * 100) if self.m.get("max_mp") else 0

        rank_col = rank_color(self.m.get("rank", "common"))
        elem_col = elems.element_color(self.m.get("element", "none"))
        p_stat = self._status_line(self.p)
        m_stat = self._status_line(self.m)

        lines = [
            color(f" {self.char['name']} Lv.{self.char['level']}", C.CYAN + C.BOLD),
            f" HP  {progress_bar(p_hp, 16)} {self.p['hp']}/{self.p['max_hp']}",
            f" MP  {progress_bar(p_mp, 16)} {self.p['mp']}/{self.p['max_mp']}",
        ]
        if p_stat:
            lines.append(color(f" Status: {p_stat}", C.YELLOW))

        lines.append(color(" ─" * 20, C.GRAY))

        lines.append(
            color(f" {self.m['name']}", rank_col + C.BOLD) +
            f"  Lv.{self.m['level']}"
        )
        lines.append(f" Rank  : {color(rank_label(self.m.get('rank','common')), rank_col)}")
        lines.append(f" Elemen: {color(elems.element_label(self.m.get('element','none')), elem_col)}")
        lines.append(f" HP    {progress_bar(m_hp, 16)} {self.m['hp']}/{self.m['max_hp']}")
        if m_stat:
            lines.append(color(f" Status: {m_stat}", C.YELLOW))

        if message:
            lines.append("")
            lines.append(color(f" {message}", C.WHITE))
        lines.append("")
        lines.append(" 1. Attack   2. Skill   3. Item   4. Defend   5. Escape")
        print(box(f"BATTLE — Turn {self.turn}", lines, width=60))

    def _status_line(self, e):
        s = e.get("status", {})
        if not s:
            return ""
        return ", ".join(f"{k}({v})" for k, v in s.items())

    # ---------- player actions ----------
    def player_turn(self):
        while True:
            self.render()
            ch = prompt("> ")
            if ch == "1":
                if self._attack_menu():
                    return
            elif ch == "2":
                if self._skill_menu():
                    return
            elif ch == "3":
                if self._item_menu():
                    return
            elif ch == "4":
                if self._defend_menu():
                    return
            elif ch == "5":
                if self._escape():
                    return
            else:
                # invalid, ignore
                pass

    def _attack_menu(self):
        self.render()
        print(box("ATTACK", [
            " 1. Normal Attack (stabil)",
            " 2. Heavy Attack (besar, -accuracy)",
            " 3. Quick Attack (kecil, 2x)",
            " 0. Kembali",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return False
        if ch == "1":
            return self._do_attack(mult=1.0, acc_mod=0, kind="Normal")
        if ch == "2":
            return self._do_attack(mult=1.7, acc_mod=-15, kind="Heavy")
        if ch == "3":
            return self._do_attack(mult=0.6, acc_mod=5, kind="Quick", hits=2)
        return False

    def _do_attack(self, mult, acc_mod, kind, hits=1, element=None):
        atk = _player_attack_power(self.char, self.stats)
        atk = _apply_mastery_bonus(self.cid, atk, "physical")
        total_dmg = 0
        total_crit = False
        for _ in range(hits):
            accuracy = self.stats["accuracy"] + acc_mod + random.randint(-5, 5)
            if accuracy < 5:
                continue  # miss
            dmg, crit = _roll_damage(
                atk, _enemy_defense(self.m), mult,
                crit_chance=(self.stats["critical"] + self.stats["luck"]) / 200.0,
                crit_damage=50,
            )
            if element:
                dmg = int(dmg * elems.damage_multiplier(element, self.m.get("element", "none")))
            total_dmg += dmg
            total_crit = total_crit or crit
        if total_dmg == 0:
            self.render(f" {kind} Attack meleset!")
            time.sleep(0.6)
            return True
        self.m["hp"] = max(0, self.m["hp"] - total_dmg)
        msg = f" {kind} Attack: {total_dmg} damage"
        if total_crit:
            msg += color(" [CRIT!]", C.YELLOW + C.BOLD)
        self.render(msg)
        time.sleep(0.8)
        return True

    def _skill_menu(self):
        from skills import skills_for_role
        from roles import mastery_tree
        learned = {s["skill_id"] for s in db.get_skills(self.cid)}
        role_skills = skills_for_role(self.char["role"])
        avail = [s for s in role_skills if s["id"] in learned and s.get("type") in ("active", "ultimate")]
        if not avail:
            self.render(" Tidak ada skill aktif yang bisa digunakan.")
            time.sleep(0.8)
            return False
        self.render()
        lines = []
        for i, s in enumerate(avail, 1):
            cost = s.get("mana_cost", 0)
            lines.append(f" {i}. {s['name']}  MP:{cost}  [{s.get('type','active')}]")
        lines.append(" 0. Kembali")
        print(box("SKILL", lines))
        ch = prompt("> ")
        if ch == "0":
            return False
        try:
            s = avail[int(ch) - 1]
        except Exception:
            return False
        cost = s.get("mana_cost", 0)
        if self.p["mp"] < cost:
            self.render(" Mana tidak cukup!")
            time.sleep(0.8)
            return False
        self.p["mp"] -= cost
        db.use_skill(self.cid, s["id"])
        return self._do_skill(s)

    def _do_skill(self, s):
        stype = s.get("type", "active")
        # Heal skill
        if "heal_pct" in s:
            heal = int(self.p["max_hp"] * s["heal_pct"] / 100)
            heal = int(_apply_mastery_bonus(self.cid, heal, "heal"))
            self.p["hp"] = min(self.p["max_hp"], self.p["hp"] + heal)
            self.render(f" {s['name']}: +{heal} HP")
            time.sleep(0.8)
            return True
        # Buff/defensive
        if s.get("effect"):
            eff = s["effect"]
            applied = []
            if "invulnerable" in eff:
                self.p["status"]["invuln"] = eff["invulnerable"]
                applied.append("invulnerable")
            if "defense_buff" in eff:
                self.p["status"]["def_buff"] = 3
                self.p["def_buff_pct"] = eff["defense_buff"]
                applied.append("defense+")
            if "regen" in eff:
                self.p["status"]["regen"] = eff["regen"]
                applied.append("regen")
            if "cleanse" in eff:
                self.p["status"] = {}
                applied.append("cleanse")
            if applied:
                self.render(f" {s['name']}: {', '.join(applied)} aktif")
                time.sleep(0.8)
                return True
        # Damage skill
        mult = s.get("damage_mult", 1.0)
        hits = s.get("hits", 1)
        element = s.get("element")
        kind = "magic" if s.get("role") in ("mage", "sorcerer", "necromancer", "elementalist",
                                             "healer", "support", "summoner") else "physical"
        if kind == "magic":
            atk = _player_magic_power(self.char, self.stats)
            atk = _apply_mastery_bonus(self.cid, atk, "magic")
        else:
            atk = _player_attack_power(self.char, self.stats)
            atk = _apply_mastery_bonus(self.cid, atk, "physical")
        total = 0
        any_crit = False
        for _ in range(hits):
            acc = self.stats["accuracy"] + random.randint(-3, 3)
            if acc < 5:
                continue
            dmg, crit = _roll_damage(
                atk, _enemy_defense(self.m), mult,
                crit_chance=(self.stats["critical"] + s.get("crit_bonus", 0)) / 100.0,
                crit_damage=50,
            )
            if element:
                dmg = int(dmg * elems.damage_multiplier(element, self.m.get("element", "none")))
            total += dmg
            any_crit = any_crit or crit
        self.m["hp"] = max(0, self.m["hp"] - total)
        msg = f" {s['name']}: {total} damage"
        if any_crit:
            msg += color(" [CRIT!]", C.YELLOW + C.BOLD)
        # Apply status effects to enemy
        if s.get("effect"):
            for k, v in s["effect"].items():
                if k in ("poison", "burn", "slow", "stun", "weaken"):
                    self.m["status"][k] = v
        self.render(msg)
        time.sleep(0.9)
        return True

    def _item_menu(self):
        from items import get_item
        inv = db.get_inventory(self.cid)
        consumables = [it for it in inv if (get_item(it["item_id"]) or {}).get("type") == "potion"]
        if not consumables:
            self.render(" Tidak ada item yang bisa dipakai.")
            time.sleep(0.8)
            return False
        self.render()
        lines = []
        for i, it in enumerate(consumables, 1):
            nm = (get_item(it["item_id"]) or {}).get("name", it["item_id"])
            lines.append(f" {i}. {nm}  x{it['quantity']}")
        lines.append(" 0. Kembali")
        print(box("ITEM", lines))
        ch = prompt("> ")
        if ch == "0":
            return False
        try:
            it = consumables[int(ch) - 1]
        except Exception:
            return False
        item = get_item(it["item_id"])
        if not item:
            return False
        eff = item.get("effect", {})
        applied = []
        if "heal_hp" in eff:
            self.p["hp"] = min(self.p["max_hp"], self.p["hp"] + eff["heal_hp"])
            applied.append(f"+{eff['heal_hp']} HP")
        if "heal_mp" in eff:
            self.p["mp"] = min(self.p["max_mp"], self.p["mp"] + eff["heal_mp"])
            applied.append(f"+{eff['heal_mp']} MP")
        db.remove_item(self.cid, it["item_id"], 1)
        self.render(f" Menggunakan {item['name']}: {', '.join(applied)}")
        time.sleep(0.8)
        return True

    def _defend_menu(self):
        self.render()
        print(box("DEFEND", [
            " 1. Guard       (kurangi damage)",
            " 2. Perfect Guard (timing, buka counter)",
            " 3. Dodge       (mengandalkan agility)",
            " 4. Counter     (risiko tinggi, damage besar)",
            " 5. Retreat     (coba keluar dari pertempuran)",
            " 0. Kembali",
        ]))
        ch = prompt("> ")
        if ch == "0":
            return False
        if ch == "1":
            self.p["status"]["guard"] = 1
            self.render(" Guard stance aktif. Damage berikutnya -50%.")
            time.sleep(0.7)
            return True
        if ch == "2":
            self.p["status"]["perfect_guard"] = 1
            self.render(" Menanti serangan dengan sempurna...")
            time.sleep(0.7)
            return True
        if ch == "3":
            self.p["status"]["dodge"] = 1
            self.render(" Bersiap menghindar.")
            time.sleep(0.7)
            return True
        if ch == "4":
            self.p["status"]["counter"] = 1
            self.render(" Menanti serangan untuk counter!")
            time.sleep(0.7)
            return True
        if ch == "5":
            return self._escape(force=True)
        return False

    def _escape(self, force=False):
        spd = self.stats["speed"] + self.stats["agility"]
        mspd = self.m["speed"]
        chance = 0.35 + (spd - mspd) / 100.0
        chance = max(0.05, min(0.9, chance))
        if random.random() < chance:
            self.result = "escape"
            self.over = True
            self.render(" Kamu berhasil melarikan diri!")
            time.sleep(0.9)
            return True
        else:
            self.render(" Gagal melarikan diri!")
            time.sleep(0.8)
            return True

    # ---------- enemy turn ----------
    def enemy_turn(self):
        st = self.m.get("status", {})
        if "stun" in st:
            self.render(f" {self.m['name']} terkena stun!")
            time.sleep(0.7)
            return
        # Slow reduces chance of acting
        if "slow" in st and random.random() < 0.4:
            self.render(f" {self.m['name']} lambat, tidak bergerak.")
            time.sleep(0.6)
            return

        # Behavior-based decision
        behavior = self.m.get("behavior", "aggressive")
        hp_pct = self.m["hp"] / self.m["max_hp"]

        action = "attack"
        if behavior == "coward" and hp_pct < 0.35:
            action = "flee"
        elif behavior == "defensive" and hp_pct > 0.6 and random.random() < 0.3:
            action = "defend"
        elif behavior == "caster" and self.m.get("mp", 0) >= 20 and random.random() < 0.5:
            action = "spell"
        elif behavior == "ambusher" and self.turn <= 2 and random.random() < 0.6:
            action = "ambush"
        elif behavior == "boss" and hp_pct < 0.5 and random.random() < 0.4:
            action = "special"

        if action == "flee":
            if random.random() < 0.5:
                self.result = "escape"
                self.over = True
                self.render(f" {self.m['name']} melarikan diri!")
                time.sleep(0.8)
                return
        if action == "defend":
            self.m["status"]["guard"] = 1
            self.render(f" {self.m['name']} bertahan.")
            time.sleep(0.6)
            return

        # Calculate enemy attack
        mult = 1.0
        elem = self.m.get("element", "none")
        if action == "spell":
            self.m["mp"] -= 20
            mult = 1.6
        elif action == "ambush":
            mult = 1.4
        elif action == "special":
            mult = 2.2

        # Player defenses
        p = self.p
        if "invuln" in p["status"]:
            self.render(f" {self.m['name']} menyerang, tapi kamu kebal!")
            time.sleep(0.7)
            return
        # Dodge
        if "dodge" in p["status"]:
            dodge_chance = 0.3 + self.stats["agility"] / 100.0
            if random.random() < dodge_chance:
                del p["status"]["dodge"]
                self.render(f" Kamu menghindar dari serangan {self.m['name']}!")
                time.sleep(0.7)
                return
            del p["status"]["dodge"]
        if "perfect_guard" in p["status"]:
            del p["status"]["perfect_guard"]
            self.render(color(" PERFECT GUARD! Kamu menahan serangan dengan sempurna!", C.CYAN + C.BOLD))
            # counter damage
            counter = int(_player_attack_power(self.char, self.stats) * 0.8)
            self.m["hp"] = max(0, self.m["hp"] - counter)
            print(color(f" Counter: {counter} damage!", C.YELLOW))
            time.sleep(1.0)
            return

        e_atk = self.m["attack"]
        if "weaken" in self.m.get("status", {}):
            e_atk = int(e_atk * 0.7)
        p_def = self.stats["defense"] * 1.2
        if "def_buff" in p["status"]:
            p_def *= (1 + p.get("def_buff_pct", 0) / 100.0)
        dmg, crit = _roll_damage(e_atk, p_def, mult,
                                  crit_chance=0.05, crit_damage=40)
        if elem and elem != "none":
            dmg = int(dmg * elems.damage_multiplier(elem, "none"))  # player default none
        if "guard" in p["status"]:
            dmg = dmg // 2
            del p["status"]["guard"]

        p["hp"] = max(0, p["hp"] - dmg)
        msg = f" {self.m['name']} menyerang: {dmg} damage"
        if crit:
            msg += color(" [CRIT!]", C.RED + C.BOLD)
        self.render(msg)
        time.sleep(0.9)

    # ---------- main loop ----------
    def run(self):
        # Player initiative based on speed vs monster
        p_spd = self.stats["speed"] + self.stats["agility"] // 2
        m_spd = self.m["speed"]
        player_first = p_spd + random.randint(0, 5) >= m_spd

        while not self.over and self.turn < self.max_turns:
            self.turn += 1
            if player_first:
                self.player_turn()
                if self.over or self.m["hp"] <= 0:
                    break
                self._tick_status()
                if self.over:
                    break
                self.enemy_turn()
                if self.over:
                    break
                self._tick_status()
            else:
                self.enemy_turn()
                if self.over:
                    break
                self._tick_status()
                if self.over:
                    break
                self.player_turn()
                if self.over or self.m["hp"] <= 0:
                    break
                self._tick_status()

            if self.p["hp"] <= 0:
                self.result = "lose"
                self.over = True
                break
            if self.m["hp"] <= 0:
                self.result = "win"
                self.over = True
                break

        if not self.over:
            # timeout
            self.result = "timeout"
            self.over = True

        # Persist HP/MP
        db.update_character(self.cid, hp_current=self.p["hp"], mp_current=self.p["mp"])
        return self.result

    def _tick_status(self):
        # Player DoT
        d = _apply_dot_and_status(self.p)
        if d:
            self.render(f" Kamu terkena status! -{d} HP")
            time.sleep(0.7)
        # Enemy DoT
        d = _apply_dot_and_status(self.m)
        if d:
            self.render(f" {self.m['name']} terkena status! -{d} HP")
            time.sleep(0.7)


# ---------- entry point ----------
def start_combat(character_id, monster, difficulty_mult=1.0):
    """Returns result string. Handles victory / defeat screen & rewards."""
    from monsters import scale_monster, maybe_mutate
    from loot import roll_loot, apply_loot_to_char
    from character import grant_exp

    # Scale + mutation
    monster = scale_monster(monster, difficulty_mult=difficulty_mult)
    monster, mutated, mlabel = maybe_mutate(monster)

    if mutated:
        clear()
        print(box("MUTATION!", [
            color(f" {monster['name']}", C.MAGENTA + C.BOLD),
            color(f" Mutation: {mlabel}", C.YELLOW),
            "",
            " Statistik monster meningkat drastis!",
        ]))
        pause()

    # Encounter screen
    clear()
    rank_col = rank_color(monster.get("rank", "common"))
    elem_col = elems.element_color(monster.get("element", "none"))
    print(box("ENCOUNTER!", [
        f" Nama   : {color(monster['name'], rank_col + C.BOLD)}",
        f" Race   : {monster.get('race','?')}",
        f" Level  : {monster['level']}",
        f" Rank   : {color(rank_label(monster.get('rank','common')), rank_col)}",
        f" Elemen : {color(elems.element_label(monster.get('element','none')), elem_col)}",
        f" Range  : {monster.get('range','melee')}",
        f" HP     : {monster['max_hp']}",
    ]))
    pause(" Tekan Enter untuk bertarung...")

    battle = Battle(character_id, monster)
    result = battle.run()

    if result == "win":
        _victory_screen(character_id, monster)
    elif result == "lose":
        _defeat_screen(character_id)
    elif result == "escape":
        clear()
        print(box("ESCAPED", [" Kamu melarikan diri dengan selamat."]))
        pause()
    elif result == "timeout":
        clear()
        print(box("BATTLE ENDED", [
            " Pertempuran terlalu lama. Semua pihak mundur.",
        ]))
        pause()

    # record combat log
    exp_gain = monster.get("exp", 0) if result == "win" else 0
    db.log_combat(character_id, monster["id"], monster["level"], result, battle.turn, exp_gain)
    return result


def _victory_screen(character_id, monster):
    from loot import roll_loot, apply_loot_to_char
    from character import grant_exp
    from items import get_item

    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    luck = stats.get("luck", 5)

    exp_gain = monster.get("exp", 0)
    loot = roll_loot(monster, luck_bonus=luck)
    applied = apply_loot_to_char(character_id, loot)
    db.record_kill(character_id, monster["id"])

    # Level up
    events = grant_exp(character_id, exp_gain)

    clear()
    lines = [
        color(f" {monster['name']} dikalahkan!", C.GREEN + C.BOLD),
        "",
        f" EXP    : +{exp_gain}",
    ]
    if applied["silver"]:
        lines.append(f" Silver : +{applied['silver']}")
    if applied["gold"]:
        lines.append(f" Gold   : +{applied['gold']}")
    if applied["zambrut"]:
        lines.append(f" Zambrut: +{applied['zambrut']}")
    if applied["items"]:
        lines.append("")
        lines.append(color(" DROPS:", C.YELLOW))
        for iid, amt in applied["items"]:
            nm = (get_item(iid) or {}).get("name", iid)
            lines.append(f"  • {nm} x{amt}")

    if events:
        lines.append("")
        for lv in events:
            lines.append(color(f" ★ LEVEL UP! → Lv {lv}", C.MAGENTA + C.BOLD))
        lines.append(f" +{3 * len(events)} Attribute Points")

    print(box("VICTORY", lines))
    pause()


def _defeat_screen(character_id):
    char = db.get_character(character_id)
    # Death penalty ringan
    lost_exp = max(0, char["exp"] // 10)
    new_exp = max(0, char["exp"] - lost_exp)
    # HP balik ke 1
    db.update_character(character_id, exp=new_exp, hp_current=1)
    clear()
    print(box("YOU HAVE FALLEN", [
        color(" Kamu tumbang di medan perang...", C.RED + C.BOLD),
        "",
        f" Kehilangan {lost_exp} EXP.",
        " Kamu bangun di kota terakhir dengan 1 HP.",
        "",
        " Pelajaran berharga untuk kehidupan berikutnya.",
    ]))
    pause()
