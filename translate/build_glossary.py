"""Step 3.2: data/glossary.json — game terms used in data/zh.

Term = stat, affix, status, slot, quality, element, resource (怒气, 源力 …) or other
fixed game word. English comes from the game dictionary by exact Chinese match
(totalLanguageDicText.json, zhcn == term; several entries -> the most frequent English,
others in `variants`). No exact match -> our translation from translate/manual/glossary.json
with source "translated". Only terms that occur in data/zh are written.

In-text terms: names of game statuses/stats (tpl_Buff, tpl_HeroInfoTips, affix names,
tpl_typeDes) and every structured term are searched as substrings of the free texts; a hit
with an exact dictionary entry is added (category "in_text").
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedict  # noqa: E402
import terms  # noqa: E402

ROOT = gamedict.ROOT
ZH = os.path.join(ROOT, "data", "zh")
OUT = os.path.join(ROOT, "data", "glossary.json")
MANUAL = os.path.join(ROOT, "translate", "manual", "glossary.json")
HAN = re.compile(r"[㐀-鿿]")

FREE_TEXT_FIELDS = {
    "char.skills[].description", "char.blood_ranks.ranks[].text", "char.divinity.levels[].effect",
    "gear.items[].skill", "gear.items[].embed_recommendations[].effect", "gear.items[].set.bonuses[].text",
    "relics.items[].skills[]", "relics.items[].advanced_fixed_skill", "relics.items[].advanced_random_skills[]",
    "runes.items[].skills[]", "black_stones.items[].effects[].text", "factions.items[].thresholds[].text",
    "char.note", "char.blood_ranks.recommendation", "char.black_stones.note", "char.runes.note",
    "tiers.items[].note", "char.builds[].level_tier", "char.builds[].qualifier",
}


def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            if HAN.search(k):
                out.append((path + "{key}", k))
                walk(v, path + "{}", out)
            else:
                walk(v, path + "." + k, out)
    elif isinstance(o, list):
        for v in o:
            walk(v, path + "[]", out)
    elif isinstance(o, str):
        out.append((path, o))


def zh_strings():
    out = []
    for p in sorted(glob.glob(os.path.join(ZH, "characters", "*.json"))):
        with open(p, encoding="utf-8") as f:
            walk(json.load(f), "char", out)
    for name in ("gear", "relics", "runes", "black_stones", "factions", "tiers"):
        with open(os.path.join(ZH, name + ".json"), encoding="utf-8") as f:
            walk(json.load(f), name, out)
    return out


def strip_note(s):
    m = terms.NOTE_RE.match(s)
    return (m.group("body"), m.group("note")) if m else (s, None)


def collect(strings):
    """term -> (category, count)"""
    found: dict[str, Counter] = defaultdict(Counter)
    for path, s in strings:
        if not HAN.search(s):
            continue
        if path in terms.TERM_FIELDS:
            for t in s.split(terms.LIST_SEP):
                found[t.strip()][terms.TERM_FIELDS[path] or "other"] += 1
        elif path in terms.STAT_FIELDS:
            for part in s.split(terms.LIST_SEP):
                body, _ = strip_note(part.strip())
                st = terms.split_stat(body)
                if st:
                    found[st[1]]["stat"] += 1
        elif path.endswith("{key}") and path[:-5] in terms.SLOT_KEY_FIELDS:
            found[s]["slot"] += 1
        elif path == "char.skills[].cost":
            st = terms.split_stat(s)
            if st:
                found[st[1]]["resource"] += 1
    return found


# everyday words that are also status/stat labels in the game but are used in the wiki texts
# in their ordinary sense (e.g. 复活 'revive' vs. the stat label 'Revival Chance')
GENERIC_WORDS = {"复活", "召唤", "生命", "能量", "伤害", "守护", "辅助", "刺杀", "秘术", "前锋", "追猎", "致命",
                 "不死", "护体", "寒气", "寒冷", "事件", "精准", "命中", "庇护", "复仇", "清醒", "神通", "聚能",
                 "回春", "战意", "剑意", "警戒", "反弹"}


def in_text_candidates(gd, exclude: set[str]):
    """Status names (tpl_Buff) and stat names (tpl_HeroInfoTips, affix names) — not names of
    skills/factions/items (those are in names.json) and not GENERIC_WORDS."""
    cands = set()
    for table, fields in (("tpl_Buff", ("name",)), ("tpl_HeroInfoTips", ("name", "name_main"))):
        for r in gd.table(table):
            for f in fields:
                cands.add(r.get(f, ""))
    for r in gd.affixes.values():
        v = r.get("desc", "")
        if not v.startswith("技能"):
            cands.add(v)
            if v.endswith("增加"):
                cands.add(v[:-2])
    return {v for v in cands
            if 2 <= len(v) <= 8 and HAN.search(v) and not re.search(r"[（(\d+%测试废弃]", v)
            and v not in exclude and v not in GENERIC_WORDS
            and not v.endswith(("提升", "增加", "降低", "减少", "下降"))}


def name_set():
    p = os.path.join(ROOT, "data", "names.json")
    out = set()
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            n = json.load(f)
        for k, d in n.items():
            if k == "meta":
                continue
            for zh, e in d.items():
                out.add(zh)
                if e.get("game_name"):
                    out.add(e["game_name"])
    return out


def build():
    gd = gamedict.get()
    if gd is None:
        sys.exit("game files not found")
    strings = zh_strings()
    found = collect(strings)

    free = [s for p, s in strings if p in FREE_TEXT_FIELDS and s]
    blob = "\n".join(free)
    for t in in_text_candidates(gd, name_set()) | set(found):
        n = blob.count(t)
        if n and t not in found and gd.exact(t):
            found[t]["in_text"] += n

    manual = {}
    if os.path.exists(MANUAL):
        with open(MANUAL, encoding="utf-8") as f:
            manual = json.load(f)["terms"]
    # terms we added by hand (in-text words without a game entry, editorial words)
    for t, m in manual.items():
        if t not in found:
            n = blob.count(t)
            if n:
                found[t][m.get("category", "in_text")] += n

    glossary, missing = {}, []
    for t in sorted(found, key=lambda x: (-sum(found[x].values()), x)):
        cat = found[t].most_common(1)[0][0]
        ex = gd.exact(t)
        if ex:
            e = {"en": ex["en"], "source": "game_db", "text_id": ex["text_id"]}
            if ex["variants"]:
                e["variants"] = ex["variants"]
        elif t in manual:
            m = manual[t]
            e = {"en": m["en"], "source": "translated" if m["en"] else None}
            if not m["en"]:
                e["status"] = "unverified"
            for k in ("note", "possible_match"):
                if m.get(k):
                    e[k] = m[k]
        else:
            e = {"en": None, "source": None, "status": "missing"}
            missing.append((t, cat))
        if t in manual and ex and manual[t].get("override"):
            # the game's English for this exact Chinese is a different sense; documented in the manual file
            e = {"en": manual[t]["en"], "source": "translated", "note": manual[t]["note"],
                 "game_db_en": ex["en"], "text_id": ex["text_id"]}
        e["category"] = cat
        e["count"] = sum(found[t].values())
        glossary[t] = e

    counts = Counter(e["source"] or "missing" for e in glossary.values())
    out = {"meta": {"description": "game terms used in data/zh -> English",
                    "rule": "exact zhcn match in the game dictionary (source game_db); otherwise our "
                            "translation (source translated)",
                    "game_snapshot": gamedict.SNAPSHOT_DATE,
                    "generated_by": "translate/build_glossary.py",
                    "counts": dict(counts)},
           "terms": glossary}
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return out, missing


if __name__ == "__main__":
    o, missing = build()
    print(o["meta"]["counts"])
    for t, c in missing:
        print("missing", c, t)
