"""NPC loader + schedule + relationship + mentor support."""
import json, os, time
from config import DATA_DIR

_N = None


def load_npcs():
    global _N
    if _N is not None:
        return _N
    path = os.path.join(DATA_DIR, "npcs.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _N = json.load(f).get("npcs", [])
    except Exception:
        _N = []
    return _N


def reload():
    """Force reload NPC data (berguna saat edit JSON tanpa restart)."""
    global _N
    _N = None
    return load_npcs()


def get_npc(nid):
    for n in load_npcs():
        if n["id"] == nid:
            return n
    return None


def npc_name(nid):
    n = get_npc(nid)
    return n["name"] if n else nid


def time_of_day():
    """Real-world hour → in-game time phase."""
    h = time.localtime().tm_hour
    if 5 <= h < 12:
        return "morning"
    if 12 <= h < 17:
        return "afternoon"
    if 17 <= h < 21:
        return "evening"
    return "night"


def time_label():
    return {
        "morning": "Pagi",
        "afternoon": "Siang",
        "evening": "Sore",
        "night": "Malam",
    }[time_of_day()]


def npcs_at(character_id, location, use_schedule=True):
    """NPCs di suatu lokasi berdasarkan jadwal."""
    tod = time_of_day()
    out = []
    for n in load_npcs():
        if use_schedule and n.get("schedule"):
            if n["schedule"].get(tod) == location:
                out.append(n)
        else:
            if n.get("location") == location:
                out.append(n)
    return out


def recruitable_npcs():
    return [n for n in load_npcs() if n.get("recruitable")]


def mentor_npcs():
    """NPC yang mengajarkan role (punya field 'teaches')."""
    return [n for n in load_npcs() if n.get("teaches")]


def mentors_at(location, use_schedule=True):
    """Mentor di lokasi tertentu."""
    tod = time_of_day()
    out = []
    for n in mentor_npcs():
        if use_schedule and n.get("schedule"):
            if n["schedule"].get(tod) == location:
                out.append(n)
        else:
            if n.get("location") == location:
                out.append(n)
    return out


def relationship_label(value):
    if value >= 80:
        return ("Soulmate", "magenta")
    if value >= 50:
        return ("Best Friend", "green")
    if value >= 20:
        return ("Friend", "cyan")
    if value >= 0:
        return ("Neutral", "white")
    if value >= -20:
        return ("Cold", "yellow")
    return ("Hostile", "red")


# ---------- Dialog helper ----------
DIALOGS = {
    "Kind":          "\"Semoga harimu menyenangkan, pengembara.\"",
    "Rough":         "\"Apa yang kau lihat? Cepat katakan.\"",
    "Calm":          "\"Tenang. Tidak perlu terburu-buru.\"",
    "Serene":        "\"Kedamaian menyertaimu, pengembara.\"",
    "Greedy":        "\"Kalau kau punya koin, aku punya barang.\"",
    "Cheerful":      "\"Halo! Hari yang cerah, bukan?\"",
    "Stern":         "\"Jangan buang waktuku. Apa urusanmu?\"",
    "Booming":       "\"HAHAHA! Selamat datang, kawan!\"",
    "Eccentric":     "\"Menarik... sangat menarik! Kau punya bakat.\"",
    "Ambitious":     "\"Aku ingin jadi yang terkuat. Kau bisa bantu?\"",
    "Quiet":         "... (dia mengangguk pelan)",
    "Wild":          "\"Aku ingin bertarung! Ada monster di dekat sini?\"",
    "Compassionate": "\"Kau terlihat lelah. Istirahatlah.\"",
    "Curious":       "\"Kau dari mana? Ceritakan!\"",
    "Silent":        "... (dia memandangmu tanpa bicara)",
    "Grumpy":        "\"Cepat. Waktuku berharga.\"",
    "Mischievous":   "\"Hehe... kau terlihat menarik.\"",
    "Loyal":         "\"Aku siap melayanimu.\"",
    "Mysterious":    "\"Ada sesuatu tentangmu... aku tak yakin apa.\"",
    "Talkative":     "\"Oh! Kau harus dengar ceritaku!\"",
    "Cold":          "\"Kematian mengikutimu. Aku suka itu.\"",
    "Warm":          "\"Kau butuh bantuan? Aku di sini.\"",
    "Dreamy":        "\"Spirit-spirit bercerita tentangmu...\"",
    "Wise":          "\"Setiap langkah adalah pelajaran, pengembara muda.\"",
    "Veteran":       "\"Aku sudah melalui perang. Kau muda, tapi aku melihat tekad.\"",
    "Noble":         "\"Aku tidak biasa berurusan dengan rakyat jelata.\"",
    "Friendly":      "\"Hai! Ada yang bisa kubantu?\"",
    "Serious":       "\"Jangan senyum. Ini bukan waktu bermain.\"",
    "Playful":       "\"Hehe! Kau lucu sekali!\"",
    "Devoted":       "\"Aku mengabdi sepenuhnya pada tujuan ini.\"",
    "Proud":         "\"Aku adalah yang terbaik di bidangku.\"",
    "Humble":        "\"Aku hanya seorang pelajar. Sama sepertimu.\"",
}


def get_dialog(npc):
    """Ambil dialog berdasarkan personality NPC."""
    p = npc.get("personality", "Neutral")
    return DIALOGS.get(p, "\"Halo, pengembara.\"")
