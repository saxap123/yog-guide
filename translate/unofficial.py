"""Unofficial English for the names left in Chinese inside English strings (step 4).

translate/manual/unofficial_names.json maps a Chinese name (a maximal run of Han characters, as
it appears in an English string of data/en) to our translation by meaning. apply() replaces every
such run in a data/en record and lists each replacement in i18n.unofficial_names
({path, zh, en}) so that the site can mark it "unofficial name" and show the Chinese.

Fields that are ids / provenance / lore are skipped (the same set as the REPORT count).
A Chinese run without an entry is left as it is and returned by apply() as unknown.
"""
from __future__ import annotations

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "translate", "manual", "unofficial_names.json")
HAN_RUN = re.compile(r"[㐀-鿿]+")
SKIP = {"i18n", "item_ids", "unlinked", "placeholders_nulled", "parse_notes", "page_title", "name_zh",
        "character_zh", "lore", "affection", "skill_zh", "slot_zh", "quality_zh", "game", "used_in", "source"}

_names = None


def names() -> dict:
    global _names
    if _names is None:
        with open(PATH, encoding="utf-8") as f:
            _names = json.load(f)["names"]
    return _names


def _join(path, key):
    return key if not path else "%s.%s" % (path, key)


def apply(rec: dict, top_skip=()) -> list[str]:
    """Replace Chinese runs in place; returns Chinese runs that have no entry."""
    tbl = names()
    used, unknown = [], []

    def fix(s, path):
        def rep(m):
            zh = m.group(0)
            e = tbl.get(zh)
            if not e:
                unknown.append(zh)
                return zh
            used.append({"path": path, "zh": zh, "en": e["en"]})
            return e["en"]
        return HAN_RUN.sub(rep, s)

    def walk(o, path, top):
        if isinstance(o, dict):
            for k in list(o):
                if k in SKIP or (top and k in top_skip):
                    continue
                o[k] = walk(o[k], _join(path, k), False)
            return o
        if isinstance(o, list):
            return [walk(v, "%s[%d]" % (path, i), False) for i, v in enumerate(o)]
        if isinstance(o, str) and HAN_RUN.search(o):
            return fix(o, path)
        return o

    walk(rec, "", True)
    if used:
        rec.setdefault("i18n", {})["unofficial_names"] = used
    return unknown
