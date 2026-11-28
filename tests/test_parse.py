"""Step 2 tests: schema validation of every output JSON, link integrity,
cross-checks against SMW, and manual checks of three character pages.

    python parse_zh/build.py
    python -m unittest discover -s tests -v
"""
import filecmp
import glob
import json
import os
import sys
import tempfile
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "parse_zh"))
import build  # noqa: E402
import textutil as tu  # noqa: E402

ZH = os.path.join(ROOT, "data", "zh")
RAW = os.path.join(ROOT, "data", "raw")
SCHEMA = os.path.join(ROOT, "schema")


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _registry():
    reg = Registry()
    for p in glob.glob(os.path.join(SCHEMA, "*.schema.json")):
        s = load(p)
        res = Resource.from_contents(s)
        reg = reg.with_resource(s["$id"], res)
    return reg


REG = _registry()


def validator(name):
    s = load(os.path.join(SCHEMA, name + ".schema.json"))
    Draft202012Validator.check_schema(s)
    return Draft202012Validator(s, registry=REG)


def errors(v, obj):
    return [f"{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in v.iter_errors(obj)]


def char(title):
    return load(os.path.join(ZH, "characters", tu.safe_filename(title) + ".json"))


def raw_char(title):
    return load(os.path.join(RAW, "characters", tu.safe_filename(title) + ".json"))


def skill(c, slot):
    return next(s for s in c["skills"] if s["slot"] == slot)


COLLECTIONS = {
    "gear.json": "gear_item",
    "relics.json": "relic",
    "runes.json": "rune",
    "black_stones.json": "black_stone",
    "factions.json": "faction",
    "tiers.json": "tiers",
}


def setUpModule():
    if not os.path.exists(os.path.join(ZH, "tiers.json")):
        build.main(quiet=True)


# ------------------------------------------------------------------ schemas
class TestSchemas(unittest.TestCase):
    def test_characters_validate(self):
        v = validator("character")
        files = glob.glob(os.path.join(ZH, "characters", "*.json"))
        self.assertEqual(len(files), len(glob.glob(os.path.join(RAW, "characters", "*.json"))))
        for f in files:
            with self.subTest(file=os.path.basename(f)):
                self.assertEqual(errors(v, load(f)), [])

    def test_collections_validate(self):
        coll = Draft202012Validator({"$ref": "https://yog-guide.local/schema/common.schema.json#/$defs/collection"}, registry=REG)
        for fname, schema in COLLECTIONS.items():
            data = load(os.path.join(ZH, fname))
            self.assertEqual(errors(coll, data), [], fname)
            self.assertEqual(data["count"], len(data["items"]), fname)
            v = validator(schema)
            for i, item in enumerate(data["items"]):
                with self.subTest(file=fname, item=item.get("name") or item.get("character")):
                    self.assertEqual(errors(v, item), [])

    def test_schema_rejects_bad_record(self):
        v = validator("character")
        c = char("千宵月守")
        del c["revid"]
        self.assertTrue(errors(v, c))
        c = char("千宵月守")
        c["builds"][0]["slots"]["帽子"] = "x"
        self.assertTrue(errors(v, c))


# ------------------------------------------------------------------ integrity
class TestIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids = {}
        for fname in COLLECTIONS:
            if fname == "tiers.json":
                continue
            for it in load(os.path.join(ZH, fname))["items"]:
                cls.ids[it["id"]] = it
        cls.chars = [load(f) for f in glob.glob(os.path.join(ZH, "characters", "*.json"))]
        for c in cls.chars:
            cls.ids[c["id"]] = c

    def test_ids_unique(self):
        seen = []
        for fname in COLLECTIONS:
            if fname != "tiers.json":
                seen += [it["id"] for it in load(os.path.join(ZH, fname))["items"]]
        seen += [c["id"] for c in self.chars]
        self.assertEqual(len(seen), len(set(seen)))

    def test_links_resolve(self):
        for c in self.chars:
            refs = []
            for b in c["builds"] or []:
                refs += [(n, i, "gear") for n, i in b["item_ids"].items() if i]
                names = [x for x in b["slots"].values() if x]
                names += [x for v in (b["alternatives"] or {}).values() for x in v]
                names += list((b["extracts"] or {}).values()) + ([b["signature_weapon"]] if b["signature_weapon"] else [])
                self.assertEqual(set(names), set(b["item_ids"]), c["page_title"])
            for key in ("main", "support"):
                for r in ((c["runes"] or {}).get(key) or []):
                    if r["id"]:
                        refs.append((r["name"], r["id"], "rune"))
            for f in ([c["factions"]["base"]] if c["factions"]["base"] else []) + (c["factions"]["others"] or []):
                if f["id"]:
                    refs.append((f["name"], f["id"], "faction"))
            for s in ((c["black_stones"] or {}).get("stones") or []):
                refs.append((s["name"], s["id"], "black_stone"))
            for r in c["relics"] or []:
                refs.append((r["name"], r["id"], "relic"))
            for name, i, kind in refs:
                with self.subTest(character=c["page_title"], name=name):
                    self.assertIn(i, self.ids)
                    self.assertTrue(i.startswith(kind + "-"))
                    self.assertIn(name, (self.ids[i]["name"], self.ids[i].get("page_title")))

    def test_relic_owner_back_link(self):
        for r in load(os.path.join(ZH, "relics.json"))["items"]:
            if r["character"] and r["character"]["id"]:
                c = self.ids[r["character"]["id"]]
                if c["relics"] is not None:
                    self.assertIn(r["id"], [x["id"] for x in c["relics"]])

    def test_tiers_cover_every_character_once_per_mode(self):
        tiers = load(os.path.join(ZH, "tiers.json"))["items"]
        names = {c["page_title"] for c in self.chars}
        for mode in ("PVE", "PVP"):
            got = [t["character"] for t in tiers if t["mode"] == mode]
            self.assertEqual(sorted(got), sorted(names))

    def test_tiers_match_raw_links(self):
        """Every character linked from a tier page is ranked, every other one is not_ranked."""
        tiers = load(os.path.join(ZH, "tiers.json"))["items"]
        for t in tiers:
            page = load(os.path.join(RAW, "pages", f"{t['mode']}节奏榜.json"))
            linked = f"link={t['character']}]]" in page["wikitext"]
            self.assertEqual(t["tier"] != "not_ranked", linked, (t["mode"], t["character"]))
            self.assertEqual((t["revid"], t["as_of"]), (page["revid"], page["rev_timestamp"][:10]))

    def test_wikitext_matches_smw(self):
        """Fields parsed from wikitext equal the values SMW stored for the same page."""
        for c in self.chars:
            p, _ = build.smw_props("characters", c["page_title"])
            with self.subTest(character=c["page_title"]):
                self.assertEqual(c["element"], tu.clean_or_none(p.get("属性")))
                self.assertEqual(c["rarity"], tu.clean_or_none(p.get("稀有度")))
                base = c["factions"]["base"]["name"] if c["factions"]["base"] else None
                self.assertEqual(base, tu.clean_or_none(p.get("基础阵线")))
                if c["skills"]:
                    self.assertEqual(skill(c, "必杀技")["description"], tu.clean(p.get("必杀技")))

    def test_black_stones_and_factions_complete(self):
        stones = load(os.path.join(ZH, "black_stones.json"))["items"]
        self.assertEqual(len(stones), 18)
        self.assertEqual({s["name"] for s in stones}, set(build.STONES))
        for s in stones:
            self.assertEqual([e["pieces"] for e in s["effects"]], [2, 4, 8], s["name"])
            self.assertTrue(all(e["text"] for e in s["effects"]), s["name"])
        fac = {f["name"]: f for f in load(os.path.join(ZH, "factions.json"))["items"]}
        self.assertEqual(len(fac), len(load(os.path.join(RAW, "categories", "阵线.json"))["members"]))
        self.assertEqual(fac["共鸣"]["thresholds"], [{"levels": [2, 3], "label": "(2/3)",
                         "text": "共鸣阵线达到2/3级时，共鸣阵线的黑卫所有球的上限增加1/2个。"}])

    def test_no_placeholder_text_left(self):
        def walk(v):
            if isinstance(v, dict):
                for x in v.values():
                    yield from walk(x)
            elif isinstance(v, list):
                for x in v:
                    yield from walk(x)
            elif isinstance(v, str):
                yield v
        for c in self.chars:
            for s in walk({k: c[k] for k in ("profile", "lore", "affection", "portraits")}):
                self.assertFalse(tu.is_placeholder(s), (c["page_title"], s))

    def test_outputs_up_to_date(self):
        """Re-running the parser reproduces the stored wiki data and available game matches."""
        def wiki_fields(record):
            if isinstance(record, list):
                return [wiki_fields(item) for item in record]
            if isinstance(record, dict):
                if {"reason", "game_id", "possible_match", "game", "wiki_lookup"} == record.keys():
                    return {"wiki_lookup": record["wiki_lookup"]}
                return {k: wiki_fields(v) for k, v in record.items()}
            return record

        with tempfile.TemporaryDirectory() as tmp:
            build.main(out=tmp, quiet=True)
            for rel in [os.path.relpath(p, tmp) for p in glob.glob(os.path.join(tmp, "**", "*.json"), recursive=True)]:
                with self.subTest(file=rel):
                    parsed, stored = os.path.join(tmp, rel), os.path.join(ZH, rel)
                    if HAS_DB:
                        self.assertTrue(filecmp.cmp(parsed, stored, shallow=False))
                    else:
                        self.assertEqual(wiki_fields(load(parsed)), wiki_fields(load(stored)))


# ------------------------------------------------------------------ text helpers
class TestTextUtil(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(tu.clean("全伤害类型减免{{颜色|红|（PVE要95%）}}、体质"), "全伤害类型减免（PVE要95%）、体质")
        self.assertEqual(tu.clean("配合[[迷迭妖精]]、[[雪月公主|雪月]]"), "配合迷迭妖精、雪月")
        self.assertEqual(tu.clean('<span class="xhp-icon">[[file:圣血晶石.png¦22px]]<span>×640</span></span>'), "×640")
        self.assertEqual(tu.clean("<p>a</p><p>b</p>"), "a\nb")
        self.assertIsNone(tu.clean("  "))
        self.assertIsNone(tu.clean_or_none("暂无"))

    def test_placeholders(self):
        for s in ("立绘1", "事迹6", "角色故事", "2级好感度问题", "10级好感度答案", "10级好感度答案1"):
            self.assertTrue(tu.is_placeholder(s), s)
        for s in ("纱夜", "事迹", "获得专属武器：云梦纤笔"):
            self.assertFalse(tu.is_placeholder(s), s)

    def test_scaling(self):
        sc = tu.extract_scaling("发射箭矢对单个敌人造成500%法术强度的火焰伤害(本技能不会受攻速影响)")
        self.assertEqual([(x["values"], x["stat"], x["effect"]) for x in sc], [([500.0], "法术强度", "火焰伤害")])
        sc = tu.extract_scaling("并分别附加1500%/5000%/5000%物理强度的神圣伤害")
        self.assertEqual(sc[0]["values"], [1500.0, 5000.0, 5000.0])
        sc = tu.extract_scaling("造成408+(50%-60%)*物理&法术强度的闪电伤害")
        self.assertEqual((sc[0]["values"], sc[0]["stat"]), ([50.0, 60.0], "物理&法术强度"))
        self.assertEqual(tu.extract_scaling("造成600%闪电伤害"), [])


# ------------------------------------------------------------------ manual checks against the pages
class TestManual千宵月守(unittest.TestCase):
    """https://wiki.biligame.com/bookofyog/千宵月守 rev 9138"""

    @classmethod
    def setUpClass(cls):
        cls.c = char("千宵月守")

    def test_header(self):
        c = self.c
        self.assertEqual(c["revid"], raw_char("千宵月守")["revid"])
        self.assertEqual(c["revid"], 9138)
        self.assertEqual((c["element"], c["rarity"]), ("黑暗", "SP"))
        self.assertEqual(c["factions"]["base"]["name"], "秘术")
        self.assertEqual([f["name"] for f in c["factions"]["others"]], ["智慧", "魔导", "超导", "流星", "暴怒", "咒蚀", "雷暴", "共鸣"])
        self.assertEqual(c["affix_recommendations"]["primary"][0], "全伤害类型减免（PVE要95%）")
        self.assertEqual(c["affix_recommendations"]["secondary"][-1], "怒气")
        self.assertIsNone(c["note"])
        self.assertEqual(c["profile"]["real_name"], "纱夜")

    def test_builds(self):
        b = self.c["builds"]
        self.assertEqual([x["level_tier"] for x in b], ["450/700级", "1000级"])
        self.assertEqual(b[0]["slots"]["头盔"], "月辉·烁金荧紫")
        self.assertEqual(b[0]["slots"]["项链"], "魔眼吊坠")
        self.assertEqual(b[0]["alternatives"]["项链"], ["海晶项链"])
        self.assertEqual(b[0]["slots"]["武器"], "宵暗刃舞")
        self.assertIsNone(b[0]["signature_weapon"])
        self.assertEqual(b[1]["slots"]["卡牌"], "任意太古装备")
        self.assertIsNone(b[1]["item_ids"]["任意太古装备"])
        self.assertEqual(b[1]["extracts"], {"裤子": "元素大师之裤"})
        self.assertEqual(b[1]["signature_weapon"], "宵暗刃舞")
        self.assertEqual(b[1]["alternatives"]["武器"], ["混沌利刃"])
        self.assertTrue(b[1]["item_ids"]["宵暗刃舞"].startswith("gear-"))

    def test_skills(self):
        s = self.c["skills"]
        self.assertEqual([x["name"] for x in s], ["黑焰冲袭", "暗渊咒杀", "邪影追猎", "今宵月圆", "月祝之舞", "叹月无瑕",
                                                  "洞悉", "玻璃大炮", "体质增强", "元素充能", "星辰之躯"])
        self.assertEqual(skill(self.c, "战斗技")["cooldown_s"], 1.5)
        self.assertEqual(skill(self.c, "战斗技")["cost"], "15源力")
        self.assertEqual(skill(self.c, "必杀技")["cost"], "1000怒气")
        self.assertEqual([(x["values"], x["stat"]) for x in skill(self.c, "普攻")["scaling"]], [([2500.0], "法术强度")])
        self.assertEqual(skill(self.c, "必杀技")["scaling"][0]["values"], [5000.0])
        self.assertEqual(skill(self.c, "战斗技")["scaling"][0]["values"], [3500.0])

    def test_runes_stones_ranks_divinity(self):
        c = self.c
        self.assertEqual([r["name"] for r in c["runes"]["main"]], ["逐日者", "残月", "雷霆咆哮", "魔哮", "戏火者", "毒牙", "万象余烬"])
        self.assertTrue(all(r["id"] for r in c["runes"]["main"]))
        self.assertEqual([r["name"] for r in c["runes"]["support"]], ["火咒"])
        self.assertEqual(c["runes"]["note"], "异界后万象换怒法")
        self.assertEqual({s["name"]: s["count"] for s in c["black_stones"]["stones"]}, {"巫妖": 4, "诡眼": 2, "雪甲虫": 4, "迅角兽": 8})
        self.assertEqual(c["blood_ranks"]["ranks"][5]["text"], "千宵月守造成的所有伤害+10%。")
        self.assertIsNone(c["blood_ranks"]["recommendation"])
        d = c["divinity"]
        self.assertEqual(d["levels"][0], {"index": 1, "name": "伏夜", "level_range": "Lv1-Lv2",
                                          "cost": [{"item": "圣血晶石", "amount": 640, "raw": "×640"},
                                                   {"item": "黑潮勋章", "amount": 20, "raw": "×20"}],
                                          "effect": "感知+15"})
        self.assertEqual(d["levels"][9]["name"], "冥神")
        self.assertEqual(d["total_cost"], [{"item": "圣血晶石", "amount": 18000, "raw": "×18000"},
                                           {"item": "黑潮勋章", "amount": 410, "raw": "×410"}])

    def test_placeholders_and_tiers(self):
        c = self.c
        self.assertIsNone(c["portraits"])
        self.assertEqual(c["lore"], {"story": None, "deeds": None})
        self.assertIsNone(c["affection"])
        self.assertIn("立绘1", c["placeholders_nulled"])
        tiers = {t["mode"]: t for t in load(os.path.join(ZH, "tiers.json"))["items"] if t["character"] == "千宵月守"}
        self.assertEqual((tiers["PVE"]["tier"], tiers["PVE"]["note"]), ("T0", "无氪金手1+0\n氪金手3+19"))
        self.assertEqual((tiers["PVP"]["tier"], tiers["PVP"]["note"]), ("T1", "进攻强大"))


class TestManual飞焰铃舞(unittest.TestCase):
    """https://wiki.biligame.com/bookofyog/飞焰铃舞 rev 9205 — a new page with mostly empty sections."""

    @classmethod
    def setUpClass(cls):
        cls.c = char("飞焰铃舞")

    def test_header(self):
        c = self.c
        self.assertEqual(c["revid"], 9205)
        self.assertEqual((c["element"], c["rarity"], c["factions"]["base"]["name"]), ("火焰", "SP", "辅助"))
        self.assertEqual(len(c["factions"]["others"]), 8)
        self.assertEqual(c["affix_recommendations"]["primary"], ["全伤害类型减免（PVE要95%）", "体质", "最大生命值", "怒气", "怒气恢复"])
        self.assertIsNone(c["note"])
        self.assertEqual(c["profile"]["release_date"], "2026年09月21日")

    def test_build_only_weapon(self):
        b = self.c["builds"]
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0]["level_tier"], "蹲")
        self.assertEqual({k: v for k, v in b[0]["slots"].items() if v}, {"武器": "飞星如焰"})
        self.assertIsNone(b[0]["alternatives"])
        self.assertFalse(b[0]["empty"])

    def test_skills(self):
        c = self.c
        self.assertEqual(skill(c, "普攻")["name"], "飞焰流矢")
        self.assertEqual([(x["values"], x["stat"], x["effect"]) for x in skill(c, "普攻")["scaling"]], [([500.0], "法术强度", "火焰伤害")])
        self.assertEqual(skill(c, "必杀技")["scaling"][0]["values"], [10000.0])
        self.assertEqual(skill(c, "战斗技")["scaling"][0]["values"], [5000.0])
        self.assertEqual(skill(c, "战斗技")["cooldown_s"], 12)
        self.assertEqual(skill(c, "战斗技")["cost"], "40源力")
        self.assertEqual(skill(c, "通用辅助技3")["description"], "法术强度提升6%")
        self.assertEqual(skill(c, "通用辅助技3")["scaling"], [])

    def test_empty_sections(self):
        c = self.c
        self.assertIsNone(c["runes"])                       # 主符文/辅助符文/备注 all empty
        self.assertEqual(c["black_stones"]["stones"], [{"name": "迅角兽", "id": c["black_stones"]["stones"][0]["id"], "count": 4, "raw": None}])
        self.assertIsNone(c["blood_ranks"]["recommendation"])
        self.assertEqual(c["blood_ranks"]["ranks"][0]["text"], "【赤瞳】提供的暴击几率+10%。")
        self.assertIsNone(c["divinity"])
        self.assertIsNone(c["lore"]["story"])
        self.assertIsNone(c["portraits"])
        tiers = [t for t in load(os.path.join(ZH, "tiers.json"))["items"] if t["character"] == "飞焰铃舞"]
        self.assertEqual({t["mode"]: t["tier"] for t in tiers}, {"PVE": "not_ranked", "PVP": "not_ranked"})


class TestManual炽焰降生(unittest.TestCase):
    """https://wiki.biligame.com/bookofyog/炽焰降生 rev 8928"""

    @classmethod
    def setUpClass(cls):
        cls.c = char("炽焰降生")

    def test_header(self):
        c = self.c
        self.assertEqual(c["revid"], 8928)
        self.assertEqual((c["element"], c["rarity"], c["factions"]["base"]["name"]), ("火焰", "SP", "秘术"))
        self.assertEqual(c["profile"]["real_name"], "伊莉德")
        self.assertEqual(c["battle_grid"], [{"template": "秘术战格", "recommended": None}])

    def test_builds(self):
        b = self.c["builds"]
        self.assertEqual([x["level_tier"] for x in b], ["450级", "旅途800级", "帆船800级"])
        self.assertIsNone(b[0]["slots"]["卡牌"])
        self.assertIsNone(b[0]["slots"]["耳坠"])
        self.assertEqual(b[0]["slots"]["武器"], "燎原焰影")
        self.assertEqual(b[0]["alternatives"]["护手"], ["祭礼手套"])
        self.assertIsNone(b[1]["slots"]["鞋子"])
        self.assertEqual(b[1]["slots"]["头盔"], "祈火灵盔")
        self.assertEqual(b[1]["alternatives"]["头盔"], ["静默之盔"])
        self.assertEqual(b[2]["slots"]["裤子"], "魔源裤腿")
        self.assertEqual(b[2]["alternatives"]["裤子"], ["元素圣灵裤"])
        self.assertEqual(b[2]["slots"]["鞋子"], "宗室礼靴")

    def test_skills(self):
        c = self.c
        self.assertEqual(skill(c, "普攻")["cooldown_s"], 1.5)
        self.assertEqual(skill(c, "战斗技")["cooldown_s"], 6)
        self.assertEqual([x["values"][0] for x in skill(c, "普攻")["scaling"]], [2500.0, 5000.0])
        self.assertEqual([x["values"][0] for x in skill(c, "战斗技")["scaling"]], [7500.0, 12000.0])
        self.assertEqual(skill(c, "辅助技3")["scaling"][0]["values"], [4000.0])

    def test_runes_stones_tiers(self):
        c = self.c
        self.assertIsNone(c["runes"]["main"])
        self.assertEqual([r["name"] for r in c["runes"]["support"]], ["火咒"])
        self.assertIn("主符文 is empty", " ".join(c["parse_notes"]))
        self.assertEqual({s["name"]: s["count"] for s in c["black_stones"]["stones"]}, {"巫妖": 4, "诡眼": 2, "迅角兽": 4, "炎龙": 8})
        self.assertEqual(c["blood_ranks"]["ranks"][1]["text"], "【血火真龙】变身的持续时间增加100%")
        tiers = {t["mode"]: t for t in load(os.path.join(ZH, "tiers.json"))["items"] if t["character"] == "炽焰降生"}
        self.assertEqual((tiers["PVE"]["tier"], tiers["PVE"]["note"]), ("T3", "火系AOE\n战技流\n异界火小怪击杀凑合用"))
        self.assertEqual((tiers["PVP"]["tier"], tiers["PVP"]["note"]), ("T3", "火系aoe\n高血阶有生存空间"))
        self.assertEqual(tiers["PVE"]["as_of"], "2026-11-09")


# ------------------------------------------------------------------ step 2 follow-up: lookup, tier_kind, reasons
HAS_DB = __import__("gamedb").find_db() is not None


class TestTierKind(unittest.TestCase):
    def test_labels(self):
        b = char("千宵月守")["builds"]
        self.assertEqual([(x["level_tier"], x["tier_kind"], x["level"], x["levels"]) for x in b],
                         [("450/700级", "level", 450, [450, 700]), ("1000级", "level", 1000, [1000])])
        b = char("炽焰降生")["builds"]
        self.assertEqual([(x["level"], x["qualifier"]) for x in b], [(450, None), (800, "旅途"), (800, "帆船")])
        b = char("飞焰铃舞")["builds"][0]
        self.assertEqual((b["level_tier"], b["tier_kind"], b["level"]), ("蹲", "special", None))
        self.assertTrue(b["tier_note"])
        b = char("百花旅者")["builds"][0]
        self.assertEqual((b["level_tier"], b["tier_kind"]), ("血包", "special"))
        self.assertEqual([x["tier_kind"] for x in char("爱恋花见")["builds"]], ["special", "special"])
        # a placeholder label that mentions 450 is still special
        b = char("唤霜海灵")["builds"][0]
        self.assertEqual((b["tier_kind"], b["level"]), ("special", None))

    def test_label_unchanged(self):
        for f in glob.glob(os.path.join(ZH, "characters", "*.json")):
            c = load(f)
            labels = build.tab_labels_before_builds(raw_char(c["page_title"])["wikitext"])
            if c["builds"]:
                self.assertEqual([b["level_tier"] for b in c["builds"]], labels, c["page_title"])
                for b in c["builds"]:
                    self.assertIn(b["tier_kind"], ("level", "special"))
                    self.assertEqual(b["level"] is None, b["tier_kind"] == "special")


class TestUnlinked(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chars = [load(f) for f in glob.glob(os.path.join(ZH, "characters", "*.json"))]
        cls.gear_ids = {g["id"] for g in load(os.path.join(ZH, "gear.json"))["items"]}

    def test_every_null_link_has_a_reason(self):
        for c in self.chars:
            for b in c["builds"] or []:
                nulls = {n for n, i in b["item_ids"].items() if i is None}
                self.assertEqual(nulls, set(b["unlinked"] or {}), (c["page_title"], b["level_tier"]))
            for key in ("main", "support"):
                for r in ((c["runes"] or {}).get(key) or []):
                    if r["options"]:
                        for o in r["options"]:
                            self.assertEqual(o["id"] is None, o["unlinked"] is not None)
                    else:
                        self.assertEqual(r["id"] is None, r["unlinked"] is not None)

    def test_possible_match_is_never_linked(self):
        for c in self.chars:
            for b in c["builds"] or []:
                for n, info in (b["unlinked"] or {}).items():
                    self.assertIsNone(b["item_ids"][n])
                    if info["possible_match"]:
                        self.assertEqual(info["possible_match"]["status"], "unverified")
                        self.assertEqual(info["reason"], "typo_candidate")

    def test_full_width_comma_split(self):
        b = next(x for x in char("夜行暹罗")["builds"] if x["level_tier"] == "帆船800级")
        self.assertEqual((b["slots"]["头盔"], b["alternatives"]["头盔"]), ("祭仪羽冠", ["界卫魔面"]))
        self.assertEqual((b["slots"]["徽章"], b["alternatives"]["徽章"]), ("霆霓猩红血印", ["狩猎徽章"]))
        for n in ("祭仪羽冠", "界卫魔面", "霆霓猩红血印", "狩猎徽章"):
            self.assertIn(b["item_ids"][n], self.gear_ids)

    def test_reasons(self):
        b = char("千宵月守")["builds"][1]
        self.assertEqual(b["unlinked"]["任意太古装备"]["reason"], "not_an_item")
        b = next(x for x in char("绯红荆棘")["builds"] if x["level_tier"] == "帆船800级")
        pm = b["unlinked"]["宗室礼鞋"]["possible_match"]
        self.assertEqual((pm["name"], pm["status"]), ("宗室礼靴", "unverified"))
        self.assertIn(pm["id"], self.gear_ids)
        self.assertIn("宗室礼鞋", [b["slots"]["鞋子"]] + (b["alternatives"] or {}).get("鞋子", []))  # typo kept as written
        opts = next(r for r in char("战争之蹄")["runes"]["main"] if r["options"])["options"]
        zr = next(o for o in opts if o["name"] == "逐日")
        self.assertEqual((zr["id"], zr["unlinked"]["possible_match"]["name"]), (None, "逐日者"))
        tj = next(r for r in char("战争之蹄")["runes"]["support"] if r["name"] == "铁荆")
        self.assertEqual(tj["unlinked"]["possible_match"]["name"], "铁棘")

    @unittest.skipUnless(HAS_DB, "game DB not present")
    def test_game_ids(self):
        b = char("千宵月守")["builds"][0]
        info = b["unlinked"]["魔弦耳环"]
        self.assertEqual((info["reason"], info["game_id"]), ("game_only", "90306"))
        self.assertIn(63588, info["game"]["text_ids"])
        b = char("飞焰铃舞")["builds"][0]
        self.assertEqual(b["unlinked"]["飞星如焰"]["game_id"], "90389")
        b = next(x for x in char("炙光之舞")["builds"])
        self.assertEqual(b["unlinked"]["扩散魔链"]["wiki_lookup"]["title_found"], True)   # empty wiki page

    def test_lookup_file(self):
        d = load(os.path.join(RAW, "missing_lookup.json"))
        self.assertIn("names", d)
        for n, r in d["names"].items():
            q = r["query"]
            self.assertIsNotNone(q, n)
            self.assertEqual(r["search"] is None, q["found"], n)       # search only when not found
        for f in glob.glob(os.path.join(RAW, "extra_items", "*.json")):
            p = load(f)
            self.assertTrue(p["source_url"].startswith("https://wiki.biligame.com/bookofyog/"))
            self.assertIsInstance(p["revid"], int)
            self.assertTrue(os.path.exists(os.path.join(RAW, "smw", "extra_items", os.path.basename(f))))

    def test_report_counts(self):
        with open(os.path.join(ZH, "REPORT.md"), encoding="utf-8") as f:
            rep = f.read()
        self.assertRegex(rep, r"\| build item names linked \| \d+ / \d+ \| \d+ / \d+ \|")
        self.assertIn("### Still unlinked, with reasons", rep)
        unl = {n for c in self.chars for b in (c["builds"] or []) for n, i in b["item_ids"].items() if i is None}
        for n in unl:
            self.assertIn(f"| {n} | gear |", rep)


class TestGameDBUntouched(unittest.TestCase):
    @unittest.skipUnless(HAS_DB, "game DB not present")
    def test_build_does_not_write_game_db(self):
        db = __import__("gamedb").find_db()

        def snapshot():
            return {os.path.join(dp, f): os.stat(os.path.join(dp, f)).st_mtime_ns
                    for dp, _, fs in os.walk(db) for f in fs}
        before = snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            build.main(out=tmp, quiet=True)
        self.assertEqual(before, snapshot())

    def test_gitignore(self):
        with open(os.path.join(ROOT, ".gitignore"), encoding="utf-8") as f:
            lines = f.read().split()
        self.assertIn("data/raw/GameDB/", lines)
        self.assertIn("data/raw/game_db/", lines)


if __name__ == "__main__":
    unittest.main()
