"""Role system — load, unlock, activate, gender rules."""
import json, os
from config import DATA_DIR

_ROLES = None

def load_roles():
    global _ROLES
    if _ROLES is not None:
        return _ROLES
    path = os.path.join(DATA_DIR, "roles.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _ROLES = json.load(f).get("roles", [])
    except Exception:
        _ROLES = []
    return _ROLES

def get_role(role_id):
    for r in load_roles():
        if r["id"] == role_id:
            return r
    return None

def available_for_gender(gender):
    """Roles unlocked directly by gender (no mentor needed)."""
    return [r for r in load_roles() if gender in r.get("gender", [])]

def mentor_locked_for_gender(gender):
    """Roles that exist but are locked for this gender (unlockable via mentor)."""
    return [r for r in load_roles() if gender not in r.get("gender", [])]

def count_by_gender():
    roles = load_roles()
    male = [r for r in roles if "male" in r.get("gender", [])]
    female = [r for r in roles if "female" in r.get("gender", [])]
    return len(male), len(female)

def stat_bias(role_id):
    r = get_role(role_id)
    return r.get("bias", {}) if r else {}

def weapon_pref(role_id):
    r = get_role(role_id)
    return r.get("weapon", []) if r else []

def mastery_tree(role_id):
    r = get_role(role_id)
    return r.get("mastery", "combat_arts") if r else "combat_arts"

def role_menu_list(gender, unlocked_ids):
    """Return roles available + which are mentor-locked."""
    all_roles = load_roles()
    unlocked = set(unlocked_ids)
    result = []
    for r in all_roles:
        status = "available"
        if r["id"] in unlocked:
            status = "owned"
        elif gender not in r.get("gender", []):
            status = "mentor_locked"
        result.append((r, status))
    return result
