"""Step 3.5: every number and percentage of a Chinese string must reappear in its English string.

Compares data/zh with data/en field by field (and data/glossary.json zh -> en, and the
Chinese/English pair of every game-only item in data/en/gear.json). For each pair of
strings the multisets of Arabic numbers (gamedict.numbers: '10.00' == '10', '1,000' == '1000')
must be equal. An English value that is null is not a number error; it is counted as missing
(listed in i18n.missing / REPORT.md).

    python translate/check_numbers.py          # prints mismatches, exit code 1 if any
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gamedict import numbers  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZH = os.path.join(ROOT, "data", "zh")
EN = os.path.join(ROOT, "data", "en")
HAN = re.compile(r"[㐀-鿿]")

# keys that hold ids, links or provenance, not text; and keys that exist only in data/en
SKIP = {"id", "item_ids", "unlinked", "source_url", "permalink", "revid", "smw_api_request", "rev_timestamp",
        "template_source_url", "template_revid", "effects_source_url", "effects_revid", "fetched_at",
        "i18n", "name_zh", "character_zh", "language", "translation", "source", "license", "page_title",
        "placeholders_nulled", "parse_notes", "game_only_items", "game_only_note", "count"}


def _official_names():
    p = os.path.join(ROOT, "data", "names.json")
    out = {}
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            n = json.load(f)
        for cat, d in n.items():
            if cat != "meta":
                for zh, e in d.items():
                    if e.get("en"):
                        out.setdefault(zh, set()).add(e["en"])
    return out


OFFICIAL_NAMES = _official_names()


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def compare(zh, en, path, out):
    """Walk zh and en in parallel; dicts with Chinese keys (build slots) are paired by position."""
    if isinstance(zh, dict) and isinstance(en, dict):
        if any(HAN.search(k) for k in zh) and not any(HAN.search(k) for k in en if k not in SKIP):
            pairs = zip(zh.items(), en.items())
            for (kz, vz), (ke, ve) in pairs:
                compare(vz, ve, "%s.%s" % (path, kz), out)
            return
        for k, vz in zh.items():
            if k in SKIP:
                continue
            compare(vz, en.get(k), "%s.%s" % (path, k), out)
    elif isinstance(zh, list) and isinstance(en, list):
        if len(zh) != len(en):
            out["errors"].append({"path": path, "error": "list length %d vs %d" % (len(zh), len(en))})
            return
        for i, (a, b) in enumerate(zip(zh, en)):
            compare(a, b, "%s[%d]" % (path, i), out)
    elif isinstance(zh, str):
        if en is None:
            if numbers(zh) or HAN.search(zh):
                out["missing"] += 1
            return
        if not isinstance(en, str):
            out["errors"].append({"path": path, "zh": zh, "en": en, "error": "type"})
            return
        out["pairs"] += 1
        nz, ne = Counter(numbers(zh)), Counter(numbers(en))
        if en in OFFICIAL_NAMES.get(zh, ()):
            nz, ne = nz, ne & nz        # official name: English-only numbers allowed
        if nz != ne:
            out["errors"].append({"path": path, "zh": zh, "en": en,
                                  "only_zh": sorted((nz - ne).elements()), "only_en": sorted((ne - nz).elements())})
    elif zh is not None and en is None and isinstance(zh, (dict, list)):
        out["errors"].append({"path": path, "error": "structure missing in en"})


def check() -> dict:
    out = {"pairs": 0, "missing": 0, "errors": []}
    zh_chars = {jload(p)["id"]: p for p in glob.glob(os.path.join(ZH, "characters", "*.json"))}
    en_chars = {os.path.splitext(os.path.basename(p))[0]: p for p in glob.glob(os.path.join(EN, "characters", "*.json"))}
    for cid, p in sorted(zh_chars.items()):
        if cid not in en_chars:
            out["errors"].append({"path": cid, "error": "no data/en/characters/%s.json" % cid})
            continue
        compare(jload(p), jload(en_chars[cid]), cid, out)
    for name in ("gear", "relics", "runes", "black_stones", "factions", "tiers"):
        z, e = jload(os.path.join(ZH, name + ".json")), jload(os.path.join(EN, name + ".json"))
        en_items = {it["id"] if "id" in it else i: it for i, it in enumerate(e["items"])}
        for i, it in enumerate(z["items"]):
            key = it.get("id", i)
            if key not in en_items:
                out["errors"].append({"path": "%s/%s" % (name, key), "error": "missing in en"})
                continue
            compare(it, en_items[key], "%s/%s" % (name, key), out)
        if name == "gear":
            for it in e["items"]:
                if it.get("source") == "game_db":
                    for kz, ke in (("skill_zh", "skill"), ("name_zh", "name"), ("slot_zh", "slot"),
                                   ("quality_zh", "quality")):
                        if it.get(kz) is not None:
                            compare(it[kz], it.get(ke), "gear/%s.%s" % (it["id"], ke), out)
    g = jload(os.path.join(ROOT, "data", "glossary.json"))["terms"]
    for zh, e in g.items():
        if e.get("en"):
            compare(zh, e["en"], "glossary/%s" % zh, out)
    n = jload(os.path.join(ROOT, "data", "names.json"))
    for cat, d in n.items():
        if cat == "meta":
            continue
        for zh, e in d.items():
            # official names: every number of the Chinese name must be in the English one,
            # English-only numbers are allowed (e.g. 危机感知 -> "6th and 7th Sense")
            if e.get("en") and numbers(zh):
                miss = Counter(numbers(zh)) - Counter(numbers(e["en"]))
                out["pairs"] += 1
                if miss:
                    out["errors"].append({"path": "names/%s/%s" % (cat, zh), "zh": zh, "en": e["en"],
                                          "only_zh": sorted(miss.elements())})
    return out


if __name__ == "__main__":
    r = check()
    for e in r["errors"]:
        print(json.dumps(e, ensure_ascii=False))
    print("string pairs checked: %d, English missing (null): %d, number mismatches: %d"
          % (r["pairs"], r["missing"], len(r["errors"])))
    sys.exit(1 if r["errors"] else 0)
