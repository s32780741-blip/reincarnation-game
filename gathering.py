"""Gathering logic — herb, wood, fiber."""
import random
import database as db
from items import get_item
from tools import find_axe, find_sickle, tool_tier_bonus


def load_gathering_nodes():
    from mining import load_resources
    return load_resources().get("gathering_nodes", [])


def get_gathering_node(node_id):
    for n in load_gathering_nodes():
        if n["id"] == node_id:
            return n
    return None


def gathering_nodes_in(region_id):
    from mining import load_resources
    region = load_resources().get("region_nodes", {}).get(region_id, {})
    return [get_gathering_node(n) for n in region.get("gathering", []) if get_gathering_node(n)]


def gather(character_id, node):
    char = db.get_character(character_id)
    stats = db.get_stats(character_id)

    req_tool = node.get("req_tool", "sickle")
    if req_tool == "iron_axe":
        tool = find_axe(character_id)
    else:
        tool = find_sickle(character_id)
    if not tool:
        return {"ok": False, "reason": f"Butuh {req_tool.replace('_',' ').title()}."}

    stamina = node.get("stamina", 2)
    if char["stamina_current"] < stamina:
        return {"ok": False, "reason": f"Stamina tidak cukup ({char['stamina_current']}/{stamina})."}

    luck = stats.get("luck", 5)
    gather_skill = stats.get("gathering", 1)
    tier_bonus = tool_tier_bonus(tool)

    drops = []
    for drop_id in node.get("drops", []):
        base_chance = node.get("chance", {}).get(drop_id, 0.5)
        chance = min(1.0, base_chance + gather_skill * 0.005 + tier_bonus * 0.05)
        if random.random() <= chance:
            amount = 1
            if random.random() < 0.25 + luck * 0.01:
                amount = 2
            if random.random() < 0.05:
                amount += 1
            drops.append({"id": drop_id, "amount": amount})

    exp_gain = node.get("exp", 6)
    db.update_character(character_id, stamina_current=char["stamina_current"] - stamina)
    for d in drops:
        db.add_item(character_id, d["id"], d["amount"])
    from character import grant_exp
    grant_exp(character_id, exp_gain)
    from mastery import check_levelup
    new_exp = db.add_mastery_exp(character_id, "gathering", exp_gain)
    check_levelup(character_id, "gathering", new_exp)
    db.inc_counter(character_id, "gathering_done", 1)

    return {"ok": True, "drops": drops, "exp": exp_gain, "stamina_cost": stamina}
