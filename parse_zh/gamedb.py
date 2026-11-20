"""Read-only lookups in the unpacked game database (data/raw/game_db/08.database).

The folder is local reference material: it is git-ignored, never modified and
never copied into data/zh — only ids and table names are recorded.

    template/*.xml            game tables, Chinese text, e.g. tpl_sc_equipment.xml
                              <root><equip><id>…</id><name>…</name><name_id>…</name_id>…
    language/json/totalLanguageDicText.json
                              [{id, zhcn, en, zhtw, ja, ko, es, …}] — <field>_id in a table
                              points to an id here
"""
from __future__ import annotations

import difflib
import json
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATE_DIRS = [os.path.join(ROOT, "data", "raw", d, "08.database") for d in ("game_db", "GameDB")]

# tables whose rows are things a build can name; used for exact lookups first and
# for "similar name" hints
ITEM_TABLES = {
    "tpl_sc_equipment.xml": "equip",
    "tpl_sc_rune.xml": "rune",
    "tpl_sc_heirloom.xml": "heirloom",
    "tpl_sc_blackStone.xml": "blackStoneDesignDrawing",
}


def find_db() -> str | None:
    for d in CANDIDATE_DIRS:
        if os.path.isdir(os.path.join(d, "template")):
            return d
    return None


class GameDB:
    def __init__(self, path: str):
        self.path = path
        self.template = os.path.join(path, "template")
        with open(os.path.join(path, "language", "json", "totalLanguageDicText.json"), encoding="utf-8") as f:
            self.dic = json.load(f)
        self.zh_to_dict: dict[str, list[int]] = {}
        for e in self.dic:
            if e.get("zhcn"):
                self.zh_to_dict.setdefault(e["zhcn"], []).append(e["id"])
        self.items: dict[str, list[dict]] = {}   # name -> rows of ITEM_TABLES
        for fname, tag in ITEM_TABLES.items():
            for row in ET.parse(os.path.join(self.template, fname)).getroot():
                if row.tag != tag:
                    continue
                name = (row.findtext("name") or "").strip()
                if name:
                    self.items.setdefault(name, []).append(self._ref(fname, row, "name"))
        self._files = sorted(
            os.path.join(dp, f) for dp, _, fs in os.walk(self.template) for f in fs if f.endswith(".xml"))

    @staticmethod
    def _ref(fname, row, field):
        nid = row.findtext(field + "_id")
        return {
            "table": os.path.splitext(fname)[0],
            "row": row.tag,
            "game_id": (row.findtext("id") or "").strip() or None,
            "field": field,
            "text_id": int(nid) if nid and nid.strip().isdigit() and int(nid) > 0 else None,
            "type": (row.findtext("type") or "").strip() or None,
        }

    def lookup(self, name: str) -> dict:
        """Exact Chinese-name matches: item tables, then any template field, then the text dictionary."""
        refs = list(self.items.get(name, []))
        if not refs:
            needle = f">{name}<".encode("utf-8")
            for path in self._files:
                with open(path, "rb") as f:
                    if needle not in f.read():
                        continue
                fname = os.path.relpath(path, self.template).replace(os.sep, "/")
                for row in ET.parse(path).getroot():
                    for child in row:
                        if (child.text or "").strip() == name:
                            refs.append(self._ref(fname, row, child.tag))
        return {"refs": refs, "text_ids": self.zh_to_dict.get(name, [])}

    def similar_item_names(self, name: str, n: int = 3, cutoff: float = 0.6) -> list[str]:
        return difflib.get_close_matches(name, list(self.items), n=n, cutoff=cutoff)

    def summary(self) -> dict:
        return {"path": os.path.relpath(self.path, ROOT).replace(os.sep, "/"),
                "dictionary_entries": len(self.dic),
                "item_names": len(self.items)}


_DB: GameDB | None = None


def get() -> GameDB | None:
    global _DB
    if _DB is None:
        p = find_db()
        if p:
            _DB = GameDB(p)
    return _DB
