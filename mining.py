"""Mining logic."""
import json, os, random
from config import DATA_DIR
import database as db
from items import get_item
from tools import find_pickaxe, tool_tier_bonus

_R = None


def load_resources():
    global _R
    if _R is not None:
        return _R
    path = os.path.join(DATA_DIR, "resources.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            _R = json.load(f)
    except Exception:
        _R = {"mining_nodes": [], "gathering_nodes": [], "region_nodes": {}}
    return _R


def get_mining_node(node_id):
    for n in load_resources().get("mining_nodes", []):
        if n["id"] == node_id:
            return n
    return None


def mining_nodes_in(region_id):
    region = load_resources().get("region_nodes", {}).get(region_id, {})
    return [get_mining_node(n) for n in region.get("mining", []) if get_mining_node(n)]


def mine(character_id, node):
    """Return dict result."""
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)
    pick = find_pickaxe(character_id)
    if not pick:
        return {"ok": False, "reason": "Butuh pickaxe (Iron/Steel)."}

    # Cek tier pickaxe
    req_pick = node.get("req_pickaxe", "iron_pickaxe")
    if req_pick == "steel_pickaxe" and pick != "steel_pickaxe":
        return {"ok": False, "reason": f"Butuh Steel Pickaxe untuk node ini."}

    stamina = node.get("stamina", 4)
    if char["stamina_current"] < stamina:
        return {"ok": False, "reason": f"Stamina tidak cukup ({char['stamina_current']}/{stamina})."}

    # Roll drops
    luck = stats.get("luck", 5)
    mining_skill = stats.get("mining", 1)
    tier_bonus = tool_tier_bonus(pick)

    drops = []
    for drop_id in node.get("drops", []):
        base_chance = node.get("chance", {}).get(drop_id, 0.5)
        chance = min(1.0, base_chance + mining_skill * 0.005 + tier_bonus * 0.05)
        if random.random() <= chance:
            amount = 1
            if random.random() < 0.2 + luck * 0.01:
                amount = 2
            drops.append({"id": drop_id, "amount": amount})

    # Exp
    exp_gain = node.get("exp", 10)
    if tier_bonus > 0:
        exp_gain = int(exp_gain * (1 + tier_bonus * 0.2))

    # Apply
    db.update_character(character_id, stamina_current=char["stamina_current"] - stamina)
    for d in drops:
        db.add_item(character_id, d["id"], d["amount"])
    from character import grant_exp
    grant_exp(character_id, exp_gain)
    # Mining skill naik
    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, "mining", exp_gain)
    check_levelup(character_id, "mining", new_exp)
    db.inc_counter(character_id, "mining_done", 1)

    return {"ok": True, "drops": drops, "exp": exp_gain, "stamina_cost": stamina}
