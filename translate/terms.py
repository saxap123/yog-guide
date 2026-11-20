"""Where glossary terms occur in data/zh, and how structured strings are split into terms.

Shared by build_glossary.py (which terms exist) and build_en.py (how to render them).
"""
from __future__ import annotations

import re

# "17532魔力", "43%暴击伤害减免", "0.25吸血抗性", "%法术强度", "+15%攻击力"
STAT_RE = re.compile(r"^(?P<num>[+\-]?\d+(?:\.\d+)?%?|%)?(?P<term>[^\d%].*?)$")
# "全伤害类型减免（PVE要95%）" -> term + editorial note in brackets
NOTE_RE = re.compile(r"^(?P<body>.+?)[（(](?P<note>[^（）()]+)[）)]$")
LIST_SEP = "、"


def split_stat(s: str):
    """'43%暴击伤害减免' -> ('43%', '暴击伤害减免'); returns None if it does not look like a stat."""
    m = STAT_RE.match(s.strip())
    if not m or not m.group("term"):
        return None
    term = m.group("term").strip()
    if re.search(r"\d", term):
        return None
    return (m.group("num") or ""), term


# field paths (as produced by walk() in build_glossary) whose values are single terms
TERM_FIELDS = {
    "char.element": "element",
    "char.rarity": None,
    "char.profile.gender": "profile",
    "char.profile.race": "profile",
    "char.skills[].slot": "skill_slot",
    "char.skills[].category": "skill_slot",
    "char.skills[].scaling[].stat": "stat",
    "char.skills[].scaling[].effect": "damage",
    "char.battle_grid[].template": "battle_grid",
    "char.divinity.levels[].cost[].item": "material",
    "char.divinity.total_cost[].item": "material",
    "gear.items[].slot": "slot",
    "gear.items[].quality": "quality",
    "gear.items[].extract_skill": "item_flag",
    "gear.items[].embed_recommendations_raw": "item_flag",
    "gear.items[].obtain[]": "source",
    "relics.items[].type": "relic_type",
    "relics.items[].quality": "quality",
    "relics.items[].obtain[]": "source",
    "runes.items[].type": "rune_type",
    "runes.items[].edges[].color_name": "rune_colour",
    "runes.items[].obtain[]": "source",
    "factions.items[].type": "faction_type",
}

# field paths whose values are stat strings ("17532魔力") or 、-lists of them
STAT_FIELDS = {
    "gear.items[].prefixes[]", "gear.items[].suffixes[]", "gear.items[].exclusive[]",
    "gear.items[].main_stat", "gear.items[].sub_stats[]",
    "relics.items[].prefixes[]", "relics.items[].suffixes[]", "relics.items[].exclusive[]",
    "runes.items[].prefixes[]", "runes.items[].suffixes[]", "runes.items[].exclusive[]",
    "runes.items[].attribute", "runes.items[].exclusive_attribute",
    "char.affix_recommendations.primary[]", "char.affix_recommendations.secondary[]",
}

# slot names are dict keys in builds
SLOT_KEY_FIELDS = {"char.builds[].slots", "char.builds[].alternatives", "char.builds[].extracts"}
