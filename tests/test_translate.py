"""Step 3 tests: data/en mirrors data/zh, numbers agree, names/glossary hold only used
strings with their sources, game files stay out of git.

    python translate/build_names.py && python translate/build_glossary.py && python translate/build_en.py
    python -m unittest discover -s tests -v

These tests read only data/zh, data/en, data/names.json and data/glossary.json (no game files).
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "translate"))
import check_numbers  # noqa: E402
from gamedict import numbers  # noqa: E402

ZH = os.path.join(ROOT, "data", "zh")
EN = os.path.join(ROOT, "data", "en")
HAN = re.compile(r"[㐀-鿿]")


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def zh_blob():
    """Every string and key of data/zh, for 'is this name/term used' checks."""
    parts = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                parts.append(k)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            parts.append(o)

    for p in glob.glob(os.path.join(ZH, "**", "*.json"), recursive=True):
        walk(load(p))
    return "\n".join(parts)


NAMES = load(os.path.join(ROOT, "data", "names.json"))
GLOSS = load(os.path.join(ROOT, "data", "glossary.json"))


class TestNumbers(unittest.TestCase):
    def test_numbers_helper(self):
        self.assertEqual(numbers("造成(10.00%-20.00%)伤害"), ["10", "20"])
        self.assertEqual(numbers("1,000 Rage, 0.5 sec"), ["1000", "0.5"])
        self.assertEqual(numbers("2026年09月21日"), numbers("2026-09-21"))

    def test_all_numbers_match(self):
        r = check_numbers.check()
        self.assertGreater(r["pairs"], 10000)
        self.assertEqual(r["errors"], [], "\n".join(json.dumps(e, ensure_ascii=False) for e in r["errors"][:20]))


class TestMirror(unittest.TestCase):
    def test_every_record_translated(self):
        zh_ids = {load(p)["id"] for p in glob.glob(os.path.join(ZH, "characters", "*.json"))}
        en_ids = {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(EN, "characters", "*.json"))}
        self.assertEqual(zh_ids, en_ids)
        for name in ("relics", "runes", "black_stones", "factions", "tiers"):
            self.assertEqual(load(os.path.join(ZH, name + ".json"))["count"],
                             load(os.path.join(EN, name + ".json"))["count"], name)

    def test_provenance_kept(self):
        for p in glob.glob(os.path.join(EN, "characters", "*.json")):
            c = load(p)
            for k in ("source_url", "revid", "permalink"):
                self.assertTrue(c.get(k), (p, k))
            self.assertIn("i18n", c)

    def test_names_from_names_json(self):
        chars = NAMES["characters"]
        for p in glob.glob(os.path.join(EN, "characters", "*.json")):
            c = load(p)
            zh = c["i18n"]["name_zh"]
            self.assertEqual(c["name"], chars[zh]["en"], zh)
            for s in c.get("skills") or []:
                if s.get("name_zh"):
                    self.assertEqual(s["name"], NAMES["skills"][s["name_zh"]]["en"], s["name_zh"])

    def test_missing_is_null_and_listed(self):
        for p in glob.glob(os.path.join(EN, "characters", "*.json")):
            c = load(p)
            for m in c["i18n"].get("missing") or []:
                self.assertTrue(m["zh"] and m["reason"], m)


class TestGameOnlyGear(unittest.TestCase):
    def test_99_items_linked(self):
        gear = load(os.path.join(EN, "gear.json"))
        go = {g["id"]: g for g in gear["items"] if g.get("source") == "game_db"}
        self.assertEqual(len(go), 99)
        for g in go.values():
            self.assertTrue(g["name_zh"] and g["game"]["game_id"] and g["used_in"], g["id"])
            self.assertIsNone(g.get("source_url"))
        linked = set()
        for p in glob.glob(os.path.join(EN, "characters", "*.json")):
            for b in load(p).get("builds") or []:
                linked |= {v for v in (b.get("item_ids") or {}).values() if v and v.startswith("gear-game-")}
        self.assertEqual(linked, set(go))


class TestNamesGlossary(unittest.TestCase):
    blob = None

    @classmethod
    def setUpClass(cls):
        cls.blob = zh_blob()

    def test_names_used_and_sourced(self):
        for cat, d in NAMES.items():
            if cat == "meta":
                continue
            for zh, e in d.items():
                self.assertIn(zh, self.blob, (cat, zh))
                if e.get("en"):
                    self.assertEqual(e["source"], "game_db", (cat, zh))
                    self.assertTrue(e.get("text_id"), (cat, zh))
                else:
                    self.assertEqual(e.get("status"), "unverified", (cat, zh))
        self.assertIsNone(NAMES["characters"]["司正天座"]["en"])
        self.assertEqual(NAMES["characters"]["璨然银龙"]["game_name"], "燦然银龙")

    def test_glossary_used_and_sourced(self):
        for zh, e in GLOSS["terms"].items():
            self.assertIn(zh, self.blob, zh)
            if e.get("en"):
                self.assertIn(e["source"], ("game_db", "translated"), zh)
            else:
                self.assertEqual(e.get("status"), "unverified", zh)

    def test_only_used_strings_not_the_dictionary(self):
        # the game dictionary has ~45k entries / 28 MB; the kept files must stay small
        size = sum(os.path.getsize(os.path.join(ROOT, "data", f)) for f in ("names.json", "glossary.json"))
        self.assertLess(size, 2_000_000)
        self.assertLess(sum(len(d) for k, d in NAMES.items() if k != "meta") + len(GLOSS["terms"]), 5000)


class TestGitIgnore(unittest.TestCase):
    @unittest.skipUnless(shutil.which("git") and os.path.isdir(os.path.join(ROOT, ".git")), "no git repository")
    def test_game_files_ignored(self):
        for p in ("data/raw/game_db/08.database/language/json/totalLanguageDicText.json",
                  "data/raw/game_db/08.database/template/tpl_sc_hero.xml",
                  "data/raw/GameDB/x", "translate/work/todo.json"):
            r = subprocess.run(["git", "check-ignore", "-q", p], cwd=ROOT)
            self.assertEqual(r.returncode, 0, p + " is not git-ignored")
        r = subprocess.run(["git", "ls-files", "data/raw/game_db", "data/raw/GameDB"], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "")


class TestUnofficialNames(unittest.TestCase):
    """Step 4: names left in Chinese inside English strings -> translate/manual/unofficial_names.json."""
    SKIP = {"i18n", "item_ids", "unlinked", "placeholders_nulled", "parse_notes", "page_title", "name_zh",
            "character_zh", "lore", "affection", "skill_zh", "slot_zh", "quality_zh", "game", "used_in", "source"}

    @staticmethod
    def records():
        for p in sorted(glob.glob(os.path.join(EN, "characters", "*.json"))):
            yield "character", load(p)
        for name in ("gear", "relics", "runes", "black_stones", "factions", "tiers"):
            for it in load(os.path.join(EN, name + ".json"))["items"]:
                yield name, it

    @staticmethod
    def get(rec, path):
        o = rec
        for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
            o = o[int(part[1:-1])] if part.startswith("[") else o[part]
        return o

    def test_no_chinese_left_and_marked(self):
        table = load(os.path.join(ROOT, "translate", "manual", "unofficial_names.json"))["names"]
        left, n = [], 0
        for kind, r in self.records():
            top = ("description",) if kind in ("gear", "relics") else ()

            def walk(o, path, is_top):
                if isinstance(o, dict):
                    for k, v in o.items():
                        if k not in self.SKIP and not (is_top and k in top):
                            walk(v, k if not path else path + "." + k, False)
                elif isinstance(o, list):
                    for i, v in enumerate(o):
                        walk(v, "%s[%d]" % (path, i), False)
                elif isinstance(o, str) and HAN.search(o):
                    left.append(path)
            walk(r, "", True)
            for u in (r.get("i18n") or {}).get("unofficial_names") or []:
                n += 1
                self.assertEqual(table[u["zh"]]["en"], u["en"])
                self.assertIn(u["en"], self.get(r, u["path"]), u)
        self.assertEqual(left, [])
        self.assertGreater(n, 0)

    def test_discrepancies_numbers_only(self):
        d = load(os.path.join(EN, "discrepancies.json"))
        self.assertEqual(d["count"], len(d["items"]))
        for x in d["items"]:
            self.assertEqual(set(x), {"record_zh", "kind", "path", "text_id", "wiki_numbers", "game_numbers"})


if __name__ == "__main__":
    unittest.main()
