"""Read-only access to the unpacked game files (data/raw/game_db/08.database).

The folder is git-ignored local reference material. Nothing here writes to it, and
nothing from it is copied wholesale into the repository: step 3 keeps only the
strings it actually uses (data/names.json, data/glossary.json, data/en).

    template/<table>.xml                       <root><ROW><field>…</field><field_id>N</field_id>…
    language/json/totalLanguageDicText.json    [{id, zhcn, en, …}]  (N above -> id here)
"""
from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from functools import cached_property

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = [os.path.join(ROOT, "data", "raw", d, "08.database") for d in ("game_db", "GameDB")]
SNAPSHOT_DATE = "2026-09-22"


RICH_TAG = re.compile(r"</?(?:size|color|b|i|u|material|quad)(?:=[^>]*)?>", re.I)


def find_db() -> str | None:
    for d in CANDIDATES:
        if os.path.isfile(os.path.join(d, "language", "json", "totalLanguageDicText.json")):
            return d
    return None


def _int(s) -> int | None:
    s = (s or "").strip()
    return int(s) if s.isdigit() and int(s) > 0 else None


class GameDict:
    def __init__(self, path: str):
        self.path = path
        with open(os.path.join(path, "language", "json", "totalLanguageDicText.json"), encoding="utf-8") as f:
            raw = json.load(f)
        self.text: dict[int, dict] = {e["id"]: e for e in raw}
        self.by_zh: dict[str, list[int]] = {}
        for e in raw:
            z = (e.get("zhcn") or "").strip()
            if z:
                self.by_zh.setdefault(z, []).append(e["id"])
        self._tables: dict[str, list[dict]] = {}

    # ---- dictionary -------------------------------------------------------------
    def zh(self, tid: int | None) -> str | None:
        e = self.text.get(tid) if tid else None
        return (e.get("zhcn") or "").strip() or None if e else None

    def en(self, tid: int | None) -> str | None:
        """English text; Unity rich-text tags (<size=14>, <color=#..>, </b> …) removed."""
        e = self.text.get(tid) if tid else None
        if not e or not (e.get("en") or "").strip():
            return None
        return RICH_TAG.sub("", e["en"]).strip() or None

    def exact(self, zh: str) -> dict | None:
        """Dictionary entries whose zhcn is exactly `zh` -> chosen en (most frequent) + variants."""
        ids = [i for i in self.by_zh.get(zh.strip(), []) if self.en(i)]
        if not ids:
            return None
        counts = Counter(self.en(i) for i in ids)
        best = max(counts, key=lambda s: (counts[s], -min(i for i in ids if self.en(i) == s)))
        return {"en": best, "text_id": min(i for i in ids if self.en(i) == best),
                "text_ids": sorted(ids), "variants": sorted(set(counts) - {best}) or None}

    # ---- tables -----------------------------------------------------------------
    def table(self, name: str) -> list[dict]:
        """Rows of template/<name>.xml as dicts of stripped strings (first level children only)."""
        if name not in self._tables:
            rows = []
            for row in ET.parse(os.path.join(self.path, "template", name + ".xml")).getroot():
                rows.append({c.tag: (c.text or "").strip() for c in row})
            self._tables[name] = rows
        return self._tables[name]

    def field_text(self, row: dict, field: str) -> dict:
        tid = _int(row.get(field + "_id"))
        return {"text_id": tid, "zh": self.zh(tid), "en": self.en(tid)}

    @cached_property
    def _template_files(self) -> list[str]:
        t = os.path.join(self.path, "template")
        return sorted(os.path.join(dp, f) for dp, _, fs in os.walk(t) for f in fs if f.endswith(".xml"))

    def scan(self, value: str) -> list[dict]:
        """Rows of any table with a field exactly `value` that has a sibling `<field>_id`."""
        needle = f">{value}<".encode("utf-8")
        refs = []
        for path in self._template_files:
            with open(path, "rb") as f:
                if needle not in f.read():
                    continue
            table = os.path.splitext(os.path.relpath(path, os.path.join(self.path, "template")))[0]
            for row in ET.parse(path).getroot():
                kids = {c.tag: (c.text or "").strip() for c in row}
                for tag, txt in kids.items():
                    if txt == value and _int(kids.get(tag + "_id")):
                        refs.append({"table": table.replace(os.sep, "/"), "row": row.tag,
                                     "game_id": kids.get("id") or None, "field": tag,
                                     "text_id": _int(kids.get(tag + "_id"))})
        return refs

    @cached_property
    def heroes(self) -> list[dict]:
        return self.table("tpl_sc_hero")

    @cached_property
    def hero_skills(self) -> dict[str, dict]:
        return {r["id"]: r for r in self.table("tpl_heroSkill")}

    @cached_property
    def passive_skills(self) -> dict[str, dict]:
        return {r["id"]: r for r in self.table("tpl_passive_skill")}

    @cached_property
    def affixes(self) -> dict[str, dict]:
        return {r["id"]: r for r in self.table("tpl_sc_equipment_affix")}

    @cached_property
    def affix_groups(self) -> dict[str, dict]:
        return {r["id"]: r for r in self.table("tpl_sc_equipment_affix_type")}


_DB: GameDict | None = None


def get() -> GameDict | None:
    global _DB
    if _DB is None:
        p = find_db()
        if p:
            _DB = GameDict(p)
    return _DB


# ---- text helpers shared by the build and the checks --------------------------------

NUM_RE = re.compile(r"\d+(?:\.\d+)?")
THOUSANDS_RE = re.compile(r"(?<=\d),(?=\d{3}(?!\d))")
FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９．％", "0123456789.%")


def numbers(s: str | None) -> list[str]:
    """Arabic numbers of a string as normalised decimals ('10.00' -> '10', '1,000' -> '1000')."""
    if not s:
        return []
    s = THOUSANDS_RE.sub("", s.translate(FULLWIDTH_DIGITS))
    out = []
    for n in NUM_RE.findall(s):
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.append(re.sub(r"^0+(?=\d)", "", n))
    return out
