"""Step 2: data/raw -> data/zh (Chinese JSON, no translation).

    python parse_zh/build.py

Reads only data/raw. Writes data/zh/{characters/*.json, gear.json, relics.json,
runes.json, black_stones.json, factions.json, tiers.json, REPORT.md}.
"""
from __future__ import annotations

import collections
import difflib
import glob
import json
import os
import re
import shutil
import sys

import mwparserfromhell as mwp
from mwparserfromhell.nodes import Tag, Template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedb  # noqa: E402
import textutil as tu  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "zh")
LICENSE = "CC BY-NC-SA 4.0"
SOURCE = "BWIKI 依盖之书 https://wiki.biligame.com/bookofyog/"

SLOTS = ["头盔", "项链", "卡牌", "耳坠", "衣服", "戒指", "腰带", "圣物", "裤子", "徽章", "鞋子", "副手", "武器", "护手"]
SKILL_SLOTS = ["普攻", "必杀技", "战斗技", "辅助技1", "辅助技2", "辅助技3", "辅助技4",
               "通用辅助技1", "通用辅助技2", "通用辅助技3", "通用辅助技4"]
STONES = ["恐熊", "巫妖", "怒兽", "猎蛛", "蝮蛇", "诡眼", "幽鬼", "雷影狼", "石像鬼",
          "雪甲虫", "感电狐", "霜蹄", "冰凤", "诅咒灵", "闪鸣鸟", "金乌", "迅角兽", "炎龙"]
GRID_TEMPLATES = ["前锋战格", "守护战格", "秘术战格", "刺杀战格"]
DEEDS = ["事迹一", "事迹二", "事迹三", "事迹四", "事迹五", "事迹六"]


# ------------------------------------------------------------------ report
class Report:
    def __init__(self):
        self.unparsed: list[tuple[str, str]] = []          # (page, problem)
        self.ignored_comments: list[tuple[str, str]] = []
        self.unlinked_items: dict[str, list[str]] = collections.defaultdict(list)
        self.normalized_links: list[tuple[str, str]] = []
        self.slot_mismatch: list[str] = []
        self.unlinked_runes: dict[str, list[str]] = collections.defaultdict(list)
        self.unlinked_factions: dict[str, list[str]] = collections.defaultdict(list)
        self.unlinked_stones: dict[str, list[str]] = collections.defaultdict(list)
        self.relic_owner_missing: list[str] = []
        self.notes: list[str] = []
        self.char_empty: dict[str, dict] = {}
        self.link_count = {"before": {"linked": 0, "total": 0}, "after": {"linked": 0, "total": 0}}
        self.unlinked_before: set[str] = set()
        self.resolved: dict[str, dict] = {}        # name -> unlinked info (gear and runes)
        self.extra_pages: list[tuple[str, str]] = []   # (title, what it became)
        self.gamedb: dict | None = None
        self.rune_count = {"before": {"linked": 0, "total": 0}, "after": {"linked": 0, "total": 0}}

    def problem(self, page, msg):
        self.unparsed.append((page, msg))


R = Report()


# ------------------------------------------------------------------ loading
def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def raw_pages(group):
    return [load(p) for p in sorted(glob.glob(os.path.join(RAW, group, "*.json")))]


def smw_props(group, title):
    path = os.path.join(RAW, "smw", group, tu.safe_filename(title) + ".json")
    if not os.path.exists(path):
        return None, None
    d = load(path)
    props = {}
    for p in d["response"]["query"]["data"]:
        if p["property"].startswith("_"):
            continue
        items = [str(i["item"]) for i in p["dataitem"]]
        props[p["property"]] = items[0] if len(items) == 1 else items
    return props, d


def prov(page):
    return {"source_url": page["source_url"], "revid": page["revid"], "permalink": page.get("permalink")}


def params(t: Template) -> dict:
    return {str(p.name).strip(): p.value for p in t.params}


def templates(code, name):
    return [t for t in code.filter_templates(recursive=True) if str(t.name).strip() == name]


def arraydefine_values(value) -> list[str]:
    """{{#arraydefine:key|a,b}} -> ['a','b']; plain text -> [text]."""
    if value is None:
        return []
    code = mwp.parse(str(value))
    arr = [t for t in code.filter_templates(recursive=False) if str(t.name).strip().startswith("#arraydefine:")]
    if not arr:
        t = tu.clean(value)
        return [t] if t else []
    t = arr[0]
    # positional params; str(p) keeps a stray "a=b" intact if an item contains "="
    body = str(t.params[0]) if t.params else ""
    sep = str(t.params[1]).strip() if len(t.params) > 1 and str(t.params[1]).strip() else ","
    return [v.strip() for v in tu.clean(body).split(sep)] if tu.clean(body) else []


def to_number(s):
    if s is None:
        return None
    s = str(s).strip()
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return None


def split_semicolon(text):
    t = tu.clean_or_none(text)
    if t is None:
        return None
    return [p.strip() for p in re.split(r"[；]", t) if p.strip()] or None


# ------------------------------------------------------------------ gear / relics / runes
def parse_named_parts(text, pattern):
    """Split 'a：x；b：y' into parts; a part not matching `pattern` is glued to the previous one."""
    t = tu.clean_or_none(text)
    if t is None:
        return None, None
    out = []
    for part in [p for p in t.split("；") if p.strip()]:
        m = re.match(pattern, part.strip(), re.S)
        if m:
            out.append(m.groupdict())
        elif out:
            last_key = list(out[-1].keys())[-1]
            out[-1][last_key] += "；" + part
        else:
            return None, t
    return out, t


EXTRA_GROUP = "extra_items"   # pages found by scraper/resolve_missing.py (not in the category)
KIND_TEMPLATES = {"gear": ["装备图鉴"], "runes": ["主符文图鉴", "辅助符文图鉴"], "relics": ["遗物图鉴"]}


def pages_of(kind):
    """(page, group, in_category) for the category pages plus matching extra pages."""
    out = [(p, kind, True) for p in raw_pages(kind)]
    known = {p["pageid"] for p, _, _ in out}
    for p in raw_pages(EXTRA_GROUP):
        if p["pageid"] in known:
            continue
        if any(templates(mwp.parse(p["wikitext"]), t) for t in KIND_TEMPLATES[kind]):
            out.append((p, EXTRA_GROUP, False))
    return out


def classify_extra_pages():
    known = {p["pageid"]: k for k in KIND_TEMPLATES for p in raw_pages(k)}
    for p in raw_pages(EXTRA_GROUP):
        code = mwp.parse(p["wikitext"])
        kind = next((k for k, ts in KIND_TEMPLATES.items() if any(templates(code, t) for t in ts)), None)
        if p["pageid"] in known:
            what = f"already in Category ({known[p['pageid']]}); was unlinked only because of a 「，」 in the build"
        elif not p["wikitext"].strip():
            what = "empty page (no wikitext) — not linked"
        elif kind is None:
            what = "not an item page (no 装备图鉴/符文图鉴/遗物图鉴 template) — not linked"
        else:
            what = f"{kind} (outside the category snapshot of step 1)"
        R.extra_pages.append((p["title"], what, p.get("redirected_from")))


def build_gear():
    items = []
    for page, group, in_cat in pages_of("gear"):
        p, smw = smw_props(group, page["title"])
        if p is None:
            R.problem(page["title"], "gear: no SMW data")
            continue
        if smw["page_revid"] != page["revid"]:
            R.problem(page["title"], f"gear: SMW revid {smw['page_revid']} != page revid {page['revid']}")
        set_bonus, set_raw = parse_named_parts(p.get("套装技能"), r"^(?P<set>.+?)[(（](?P<pieces>\d+)[)）][：:](?P<text>.*)$")
        if set_bonus is not None:
            set_bonus = [{"pieces": int(b["pieces"]), "text": b["text"].strip(), "set": b["set"].strip()} for b in set_bonus]
        elif set_raw:
            R.problem(page["title"], "gear: 套装技能 not in 'name(n)：text' form, kept as raw text")
        embed, embed_raw = parse_named_parts(p.get("嵌入技能推荐"), r"^(?P<name>[^：:]+)[：:](?P<effect>.*)$")
        items.append({
            "id": f"gear-{page['pageid']}",
            "name": tu.clean(p.get("装备名称")) or page["title"],
            "page_title": page["title"],
            "slot": tu.clean_or_none(p.get("部位")),
            "quality": tu.clean_or_none(p.get("品质")),
            "max_level": to_number(tu.clean(p.get("最大等级"))),
            "main_stat": tu.clean_or_none(p.get("主属性")),
            "sub_stats": tu.split_list(p.get("副属性")),
            "prefixes": tu.split_list(p.get("前缀")),
            "suffixes": tu.split_list(p.get("后缀")),
            "exclusive": tu.split_list(p.get("专属")),
            "skill": tu.clean_or_none(p.get("装备技能")),
            "set": None if not tu.clean_or_none(p.get("套装")) else {
                "name": tu.clean(p.get("套装")),
                "bonuses": set_bonus,
                "raw": set_raw if set_bonus is None else None,
            },
            "extract_skill": tu.clean_or_none(p.get("萃取技能")),
            "embed_recommendations": [{"name": e["name"].strip(), "effect": e["effect"].strip()} for e in embed] if embed else None,
            "embed_recommendations_raw": embed_raw if (embed is None and embed_raw) else None,
            "obtain": tu.split_list(p.get("获取途径")),
            "description": tu.clean_or_none(p.get("介绍")),
            "in_category": in_cat,
            **prov(page),
            "smw_api_request": smw["api_request"],
        })
    return items


def build_relics(char_ids):
    items = []
    for page in raw_pages("relics"):
        p, smw = smw_props("relics", page["title"])
        if p is None:
            R.problem(page["title"], "relic: no SMW data")
            continue
        # 介绍 is a template parameter that the template does not #set -> only in wikitext
        desc = None
        for t in templates(mwp.parse(page["wikitext"]), "遗物图鉴"):
            pp = params(t)
            desc = tu.clean_or_none(pp.get("介绍"))
        owner = tu.clean_or_none(p.get("黑卫名称"))
        if owner and owner not in char_ids:
            R.relic_owner_missing.append(f"{page['title']} → {owner}")
        items.append({
            "id": f"relic-{page['pageid']}",
            "name": tu.clean(p.get("遗物名称")) or page["title"],
            "page_title": page["title"],
            "type": tu.clean_or_none(p.get("类型")),
            "quality": tu.clean_or_none(p.get("品质")),
            "max_level": to_number(tu.clean(p.get("最大等级"))),
            "character": None if not owner else {"name": owner, "id": char_ids.get(owner)},
            "exclusive": tu.split_list(p.get("专属")),
            "skills": split_semicolon(p.get("遗物技能")),
            "advanced_fixed_skill": tu.clean_or_none(p.get("进阶固有技能")),
            "advanced_random_skills": split_semicolon(p.get("进阶随机技能")),
            "prefixes": tu.split_list(p.get("前缀")),
            "suffixes": tu.split_list(p.get("后缀")),
            "obtain": tu.split_list(p.get("获取途径")),
            "description": desc,
            "description_source": "wikitext" if desc else None,
            **prov(page),
            "smw_api_request": smw["api_request"],
        })
    return items


def parse_edges(smw_value, wikitext_value):
    """边: colored slashes. SMW has hex colors, wikitext has {{颜色|name|///}}."""
    if not smw_value:
        return None
    hexes = re.findall(r'color:\s*(#[0-9a-fA-F]{3,6})">(/+)<', str(smw_value))
    names = []
    if wikitext_value is not None:
        for t in mwp.parse(str(wikitext_value)).filter_templates(recursive=False):
            if str(t.name).strip() == "颜色":
                names.append((str(t.get("1").value).strip(), len(str(t.get("2").value).strip()) if t.has("2") else 0))
    out = []
    for i, (hx, slashes) in enumerate(hexes):
        nm = names[i][0] if i < len(names) and names[i][1] == len(slashes) else None
        out.append({"color": hx.lower(), "color_name": nm, "count": len(slashes)})
    return out or None


def build_runes():
    items = []
    for page, group, in_cat in pages_of("runes"):
        p, smw = smw_props(group, page["title"])
        if p is None:
            R.problem(page["title"], "rune: no SMW data")
            continue
        wt_edges = None
        for name in ("主符文图鉴", "辅助符文图鉴"):
            for t in templates(mwp.parse(page["wikitext"]), name):
                wt_edges = params(t).get("边")
        items.append({
            "id": f"rune-{page['pageid']}",
            "name": tu.clean(p.get("符文名称")) or page["title"],
            "page_title": page["title"],
            "type": tu.clean_or_none(p.get("类型")),
            "max_level": to_number(tu.clean(p.get("最大等级"))),
            "attribute": tu.clean_or_none(p.get("属性")),
            "exclusive": tu.split_list(p.get("专属")),
            "exclusive_attribute": tu.clean_or_none(p.get("专属属性")),
            "prefixes": tu.split_list(p.get("前缀")),
            "suffixes": tu.split_list(p.get("后缀")),
            "skills": split_semicolon(p.get("符文技能")),
            "edges": parse_edges(p.get("边"), wt_edges),
            "obtain": tu.split_list(p.get("获取途径")),
            "in_category": in_cat,
            **prov(page),
            "smw_api_request": smw["api_request"],
        })
    return items


# ------------------------------------------------------------------ tabbed overview pages (黑石, 阵线)
def _has_class(tag: Tag, cls: str) -> bool:
    if not tag.has("class"):
        return False
    return cls in str(tag.get("class").value).split()


def tab_blocks(wikitext):
    """Return [(label_wikicode, content_wikicode)] for every resp-tabs group, in page order.

    The overview pages have unbalanced <div>s, so the tab structure is cut at the
    literal `resp-tabs` / `resp-tab-content` markers; each piece is then parsed
    with mwparserfromhell (the <span>s inside are balanced).
    """
    out = []
    for grp in re.split(r'<div class="resp-tabs"', wikitext)[1:]:
        head, *chunks = re.split(r'<div class="resp-tab-content"', grp)
        head_code = mwp.parse(head)
        labels = head_code.filter_tags(recursive=True, matches=lambda n: n.tag == "span" and _has_class(n, "tab-panel"))
        if len(labels) != len(chunks):
            out.append((None, (len(labels), len(chunks))))
            continue
        out.extend(zip([lb.contents for lb in labels], [mwp.parse(c) for c in chunks]))
    return out


def num_text_pairs(code):
    nums = code.filter_tags(recursive=True, matches=lambda n: n.tag == "span" and _has_class(n, "box-hs-num"))
    texts = code.filter_tags(recursive=True, matches=lambda n: n.tag == "span" and _has_class(n, "box-hs-text"))
    return [(tu.clean(a.contents), tu.clean(b.contents)) for a, b in zip(nums, texts)], (len(nums), len(texts))


def build_black_stones():
    page = load(os.path.join(RAW, "black_stones", "黑石.json"))
    tpl = load(os.path.join(RAW, "black_stones", "模板_推荐黑石.json"))
    from_page = {}
    for label, content in tab_blocks(page["wikitext"]):
        if label is None:
            R.problem("黑石", f"tab labels/contents count mismatch {content}")
            continue
        name = tu.clean(label)
        pairs, counts = num_text_pairs(content)
        if counts[0] != counts[1]:
            R.problem("黑石", f"{name}: {counts[0]} piece labels vs {counts[1]} texts")
        eff = []
        for num, text in pairs:
            m = re.search(r"(\d+)\s*套装", num or "")
            if not m:
                R.problem("黑石", f"{name}: cannot read piece count from {num!r}")
                continue
            eff.append({"pieces": int(m.group(1)), "text": text})
        from_page[name] = eff

    # 模板:推荐黑石: {{#if: {{{X|}}}| ... {{#ifexpr: {{{X}}} >= 2|<span ..num>(2 套装)</span><span ..text>T</span>}} ...}}
    from_tpl = collections.defaultdict(dict)
    # mwparserfromhell does not treat "{{#ifexpr: … >= 2|…}}" as a template (">" is not allowed
    # in template names), so the #ifexpr calls are located with a regex and only their bodies
    # are parsed.
    for m in re.finditer(r"\{\{#ifexpr:\s*\{\{\{([^}|]+)\}\}\}\s*(>=|=)\s*(\d+)\s*\|(.*?)\}\}", tpl["wikitext"], re.S):
        stone, pieces, body = m.group(1).strip(), int(m.group(3)), m.group(4)
        texts = mwp.parse(body).filter_tags(recursive=True, matches=lambda n: n.tag == "span" and _has_class(n, "box-hs-text"))
        from_tpl[stone][pieces] = tu.clean(texts[0].contents) if texts else None

    stones = []
    names = list(from_page.keys())
    for extra in STONES:
        if extra not in from_page:
            R.problem("黑石", f"stone {extra} (parameter of 模板:推荐黑石) has no tab on page 黑石")
            names.append(extra)
    for i, name in enumerate(names, 1):
        page_eff = from_page.get(name)
        tpl_eff = from_tpl.get(name, {})
        effects = []
        if page_eff:
            for e in page_eff:
                tt = tpl_eff.get(e["pieces"])
                effects.append({"pieces": e["pieces"], "text": e["text"],
                                "text_template": tt,
                                "same_in_template": tt == e["text"]})
                if tt != e["text"]:
                    R.notes.append(f"黑石 {name} ({e['pieces']}): page «{e['text']}» vs 模板:推荐黑石 «{tt}»")
        elif tpl_eff:
            effects = [{"pieces": k, "text": None, "text_template": v, "same_in_template": False} for k, v in sorted(tpl_eff.items())]
        stones.append({
            "id": f"black_stone-{i:02d}",
            "name": name,
            "effects": effects or None,
            **prov(page),
            "template_source_url": tpl["source_url"],
            "template_revid": tpl["revid"],
        })
    if len(stones) != 18:
        R.problem("黑石", f"expected 18 stones, found {len(stones)}")
    return stones


def build_factions():
    overview = load(os.path.join(RAW, "pages", "阵线.json"))
    effects = {}
    for label, content in tab_blocks(overview["wikitext"]):
        if label is None:
            R.problem("阵线", f"tab labels/contents count mismatch {content}")
            continue
        icon = [t for t in label.filter_templates(recursive=True) if str(t.name).strip() == "阵线图标"]
        name = str(icon[0].get("1").value).strip() if icon else tu.clean(label)
        pairs, counts = num_text_pairs(content)
        if counts[0] != counts[1]:
            R.problem("阵线", f"{name}: {counts[0]} threshold labels vs {counts[1]} texts")
        lst = []
        for num, text in pairs:
            lv = re.findall(r"\d+", num or "")
            if not lv:
                R.problem("阵线", f"{name}: cannot read thresholds from {num!r}")
            lst.append({"levels": [int(x) for x in lv], "label": num, "text": text})
        effects[name] = lst

    items = []
    seen = set()
    for page in raw_pages("factions"):
        p, smw = smw_props("factions", page["title"])
        name = tu.clean((p or {}).get("名称")) or page["title"]
        seen.add(name)
        stub = {}
        for t in templates(mwp.parse(page["wikitext"]), "阵线"):
            stub = {k: tu.clean_or_none(v) for k, v in params(t).items()}
        eff = effects.get(name)
        if eff is None:
            R.unlinked_factions["(no effects on page 阵线)"].append(name)
        items.append({
            "id": f"faction-{page['pageid']}",
            "name": name,
            "type": tu.clean_or_none((p or {}).get("类型")),
            "count": stub.get("数量"),
            "effect_on_page": stub.get("效果"),
            "thresholds": eff,
            **prov(page),
            "effects_source_url": overview["source_url"] if eff is not None else None,
            "effects_revid": overview["revid"] if eff is not None else None,
        })
    for name in effects:
        if name not in seen:
            R.problem("阵线", f"faction {name} has effects on page 阵线 but no page in Category:阵线")
    return items


# ------------------------------------------------------------------ characters
class Linker:
    def __init__(self, records, kind):
        self.kind = kind
        self.exact = {}
        self.norm = collections.defaultdict(set)
        for r in records:
            for n in {r["name"], r.get("page_title") or r["name"]}:
                self.exact.setdefault(n, r["id"])
                self.norm[tu.normalize_name(n)].add(r["id"])
        self.by_id = {r["id"]: r for r in records}

    def find(self, name):
        if name in self.exact:
            return self.exact[name], "exact"
        cands = self.norm.get(tu.normalize_name(name), set())
        if len(cands) == 1:
            return next(iter(cands)), "normalized"
        return None, ("ambiguous" if cands else "missing")


class Resolver:
    """Why a name stayed unlinked: wiki lookup (missing_lookup.json), game DB, similar names.

    reason: not_an_item | game_only (no wiki page, exists in the game DB) |
            typo_candidate (similar existing name, unverified) | nowhere
    """

    def __init__(self, lookup, gamedb, records_by_kind, char_titles=()):
        self.char_titles = set(char_titles)
        self.lookup = lookup or {}
        self.db = gamedb
        self.records = records_by_kind      # kind -> list of records with name/id

    def _similar(self, name, kind):
        names = {r["name"]: r["id"] for r in self.records[kind]}
        cutoff = 0.5 if len(name) <= 2 else 0.6
        hits = [x for x in difflib.get_close_matches(name, list(names), n=3, cutoff=cutoff) if abs(len(x) - len(name)) <= 1]
        return [(h, names[h]) for h in hits]

    def info(self, name, kind):
        if name in R.resolved:
            return {k: v for k, v in R.resolved[name].items() if k != "kind"}
        wl = self.lookup.get(name)
        wiki = None
        if wl is not None:
            q = wl.get("query") or {}
            wiki = {"title_found": bool(q.get("found")), "page": q.get("title"),
                    "search_hits": [h["title"] for h in (wl.get("search") or [])][:5]}
        game = None
        if self.db is not None:
            g = self.db.lookup(name)
            if g["refs"] or g["text_ids"]:
                game = {"refs": g["refs"] or None, "text_ids": g["text_ids"] or None}
        possible = None
        if name.startswith("任意"):
            reason = "not_an_item"
        elif game and game["refs"]:
            reason = "game_only"
        else:
            cands = self._similar(name, kind)
            src = "similar name in " + ("gear.json" if kind == "gear" else "runes.json")
            if not cands and self.db is not None:
                cands = [(h, None) for h in self.db.similar_item_names(name, n=1)]
                src = "similar name in game DB"
            if not cands and wiki:
                cands = [(h, None) for h in wiki["search_hits"]
                         if h not in self.char_titles and difflib.SequenceMatcher(None, name, h).ratio() >= 0.6][:1]
                src = "wiki search hit"
            if cands:
                possible = {"name": cands[0][0], "id": cands[0][1], "source": src, "status": "unverified"}
                reason = "typo_candidate"
            else:
                reason = "nowhere"
        game_id = None
        if game and game["refs"]:
            game_id = next((r["game_id"] for r in game["refs"] if r["table"] in ("tpl_sc_equipment", "tpl_sc_rune")),
                           game["refs"][0]["game_id"])
        rec = {"reason": reason, "game_id": game_id, "possible_match": possible, "game": game, "wiki_lookup": wiki}
        R.resolved[name] = {**rec, "kind": kind}
        return rec


def parse_skills(code, title):
    tl = templates(code, "黑卫技能")
    if not tl:
        return None
    if len(tl) > 1:
        R.problem(title, f"{len(tl)} 黑卫技能 calls, using the first")
    pp = params(tl[0])
    names = arraydefine_values(pp.get("技能名称"))
    cds = arraydefine_values(pp.get("技能冷却时间"))
    costs = arraydefine_values(pp.get("技能消耗"))
    if names and len(names) != len(SKILL_SLOTS):
        R.problem(title, f"黑卫技能: {len(names)} skill names for {len(SKILL_SLOTS)} slots")
    out = []
    for i, slot in enumerate(SKILL_SLOTS):
        desc = tu.clean(pp.get(slot))
        cd = cds[i] if i < len(cds) else None
        out.append({
            "slot": slot,
            "category": re.sub(r"\d+$", "", slot),
            "name": (names[i] or None) if i < len(names) else None,
            "cooldown_s": to_number(cd),
            "cooldown_raw": cd if (cd is not None and to_number(cd) is None) else None,
            "cost": (costs[i] or None) if i < len(costs) else None,
            "description": desc,
            "scaling": tu.extract_scaling(desc),
        })
    return out


def tab_labels_before_builds(wikitext):
    code = mwp.parse(wikitext)
    spans = code.filter_tags(recursive=True, matches=lambda n: n.tag == "span" and _has_class(n, "tab-panel"))
    return [tu.clean(s.contents) for s in spans]


# Short English explanations of tab labels that are not level tiers. These are
# readings of the wiki's own wording, not game data; unknown labels get null.
SPECIAL_TIER_NOTES = {
    "蹲": "placeholder ('waiting'): build not filled in yet",
    "蹲一个450配装，欢迎下方评论区留言": "placeholder: editors ask for a 450 build in the comments",
    "血包": "'blood pack' build (healing / HP support role)",
    "＜3血阶": "for blood rank below 3",
    "≥3血阶": "for blood rank 3 or higher",
    "大招无敌流": "playstyle: ultimate + invincibility",
    "帆船辅助": "support build for 帆船 (sailing mode)",
}


def classify_tier(label):
    """tier_kind 'level' when the tab label names a level (450/700/800/1000), else 'special'."""
    if label is None:
        return {"tier_kind": None, "level": None, "levels": None, "qualifier": None, "tier_note": None}
    nums = [int(x) for x in re.findall(r"\d{3,4}", label)]
    if nums and not label.startswith("蹲"):
        rest = re.sub(r"\d{3,4}(?:/\d{3,4})*\s*级?", "", label).strip() or None
        return {"tier_kind": "level", "level": nums[0], "levels": nums, "qualifier": rest, "tier_note": None}
    note = SPECIAL_TIER_NOTES.get(label)
    if note is None:
        R.notes.append(f"tab label «{label}» has no explanation in SPECIAL_TIER_NOTES (tier_note = null)")
    return {"tier_kind": "special", "level": None, "levels": None, "qualifier": None, "tier_note": note}


def parse_builds(code, page, gear_link, gear_by_id, base_link, resolver):
    title = page["title"]
    calls = templates(code, "黑卫配装")
    if not calls:
        return None
    labels = tab_labels_before_builds(page["wikitext"])
    if len(labels) != len(calls):
        R.problem(title, f"{len(calls)} 黑卫配装 calls but {len(labels)} tab labels — level_tier set to null")
        labels = [None] * len(calls)
    builds = []
    for bi, (t, label) in enumerate(zip(calls, labels)):
        pp = params(t)
        owner = tu.clean(pp.get("黑卫名称"))
        if owner and owner != title:
            R.problem(title, f"黑卫配装 #{bi + 1}: 黑卫名称={owner} differs from page title")
        slots, alts, extracts, links = {}, {}, {}, {}
        raw_names = []          # names exactly as written (no 「，」 split): the step-2 "before" state
        for s in SLOTS:
            vals = []
            for v in arraydefine_values(pp.get(s)):
                if v:
                    raw_names.append(v)
                parts = [p.strip() for p in v.split("，") if p.strip()]
                if len(parts) > 1:
                    R.notes.append(f"{title} build «{label}» {s}: «{v}» split on the full-width comma into {parts}")
                vals += parts
            slots[s] = vals[0] if vals else None
            if len(vals) > 1:
                alts[s] = vals[1:]
            if len(vals) > 2:
                R.notes.append(f"{title} build «{label}» {s}: {len(vals)} items, the wiki template shows only the first two")
            ex = tu.clean(pp.get(s + "萃取"))
            if ex:
                extracts[s] = ex
                raw_names.append(ex)
        sig = tu.clean(pp.get("专武"))
        if sig:
            raw_names.append(sig)
        for n in raw_names:
            R.link_count["before"]["total"] += 1
            if base_link.find(n)[0]:
                R.link_count["before"]["linked"] += 1
            else:
                R.unlinked_before.add(n)
        named = [(s, n) for s in SLOTS for n in ([slots[s]] if slots[s] else []) + alts.get(s, [])]
        named += [(s + "萃取", n) for s, n in extracts.items()]
        if sig:
            named.append(("专武", sig))
        unlinked = {}
        for s, n in named:
            gid, how = gear_link.find(n)
            links[n] = gid
            R.link_count["after"]["total"] += 1
            where = f"{title} / «{label}» / {s}"
            if gid is None:
                R.unlinked_items[n].append(where + (" (ambiguous)" if how == "ambiguous" else ""))
                unlinked[n] = resolver.info(n, "gear")
            else:
                R.link_count["after"]["linked"] += 1
                if how == "normalized":
                    R.normalized_links.append((n, gear_by_id[gid]["name"]))
                gslot = gear_by_id[gid]["slot"]
                base_slot = s.replace("萃取", "")
                if s != "专武" and gslot and gslot != base_slot:
                    R.slot_mismatch.append(f"{where}: {n} has 部位={gslot}")
        builds.append({
            "level_tier": label,
            **classify_tier(label),
            "slots": slots,
            "alternatives": alts or None,
            "extracts": extracts or None,
            "signature_weapon": sig,
            "item_ids": links,
            "unlinked": unlinked or None,
            "empty":all(v is None for v in slots.values()) and not extracts and not sig,
        })
    return builds


def parse_character(page, gear_link, gear_by_id, rune_link, faction_link, stone_ids, relics_by_owner,
                    base_gear_link, base_rune_link, resolver):
    title = page["title"]
    code = mwp.parse(page["wikitext"])
    placeholders = []
    notes = []

    for cm in code.filter_comments():
        if "{{" in str(cm):
            names = re.findall(r"\{\{\s*([^|}\n]+)", str(cm))
            R.ignored_comments.append((title, ", ".join(n.strip() for n in names)))

    def field(pp, key, label=None):
        v, ph = tu.real_or_none(pp.get(key))
        if ph:
            placeholders.append(label or key)
        if v in tu.NONE_VALUES:
            return None
        return v

    # ---- 黑卫
    hw = templates(code, "黑卫")
    if not hw:
        R.problem(title, "no 黑卫 template")
        pp = {}
    else:
        pp = params(hw[0])

    def flist(key):
        v = field(pp, key)
        return [x.strip() for x in v.split("、") if x.strip()] if v else None

    base_f = field(pp, "基础阵线")
    other_f = flist("其他阵线")

    def flink(n):
        fid, _ = faction_link.find(n)
        if fid is None:
            R.unlinked_factions[n].append(title)
        return {"name": n, "id": fid}

    rec = {
        "id": f"char-{page['pageid']}",
        "name": field(pp, "称号") or title,
        "page_title": title,
        "in_category_黑卫": page.get("in_category_黑卫", True),
        "profile": {
            "real_name": field(pp, "姓名"),
            "gender": field(pp, "性别"),
            "race": field(pp, "种族"),
            "birthday": field(pp, "生日"),
            "birthplace": field(pp, "出生地"),
            "height_weight": field(pp, "具体身高/体重"),
            "specialties": flist("特长"),
            "likes": flist("喜爱的东西"),
            "dislikes": flist("讨厌的东西"),
            "release_date": field(pp, "上线日期"),
        },
        "element": field(pp, "属性"),
        "rarity": field(pp, "稀有度"),
        "factions": {
            "base": flink(base_f) if base_f else None,
            "others": [flink(n) for n in other_f] if other_f else None,
        },
        "affix_recommendations": {"primary": flist("配装-词条推荐1"), "secondary": flist("配装-词条推荐2")},
        "note": field(pp, "备注"),
    }
    if rec["name"] != title:
        R.problem(title, f"黑卫.称号={rec['name']} differs from page title")

    # ---- skills / builds
    rec["skills"] = parse_skills(code, title)
    rec["builds"] = parse_builds(code, page, gear_link, gear_by_id, base_gear_link, resolver)

    # ---- runes
    rt = templates(code, "推荐符文")
    if rt:
        rp = params(rt[0])

        def rl(key):
            v = tu.split_list(rp.get(key))
            if not v:
                return None
            out = []
            def count(name, rid):
                R.rune_count["after"]["total"] += 1
                R.rune_count["after"]["linked"] += bool(rid)

            for n in v:
                # before = step 2: the name as written ("断钢/逐日" is one unlinked entry)
                R.rune_count["before"]["total"] += 1
                R.rune_count["before"]["linked"] += bool(base_rune_link.find(n)[0])
                rid, _ = rune_link.find(n)
                entry = {"name": n, "id": rid, "options": None, "unlinked": None}
                if rid is None and "/" in n:
                    # "断钢/逐日": either rune; kept as written, options linked separately
                    opts = [{"name": o.strip(), "id": rune_link.find(o.strip())[0], "unlinked": None}
                            for o in n.split("/") if o.strip()]
                    entry["options"] = opts
                    for o in opts:
                        count(o["name"], o["id"])
                        if o["id"] is None:
                            o["unlinked"] = resolver.info(o["name"], "runes")
                            R.unlinked_runes[o["name"]].append(f"{title} / {key} (option of «{n}»)")
                else:
                    count(n, rid)
                    if rid is None:
                        entry["unlinked"] = resolver.info(n, "runes")
                        R.unlinked_runes[n].append(f"{title} / {key}")
                out.append(entry)
            return out
        rec["runes"] = {"main": rl("主符文"), "support": rl("辅助符文"), "note": tu.clean_or_none(rp.get("备注"))}
        if rec["runes"]["main"] is None and rec["runes"]["support"]:
            notes.append("推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set")
        if all(v is None for v in rec["runes"].values()):
            rec["runes"] = None
    else:
        rec["runes"] = None

    # ---- black stones
    bt = templates(code, "推荐黑石")
    if bt:
        bp = params(bt[0])
        stones = []
        for s in STONES:
            v = tu.clean(bp.get(s))
            if not v:
                continue
            n = to_number(v)
            if not isinstance(n, int):
                R.problem(title, f"推荐黑石 {s}={v!r} is not an integer")
            stones.append({"name": s, "id": stone_ids.get(s), "count": n if isinstance(n, int) else None, "raw": None if isinstance(n, int) else v})
            if stone_ids.get(s) is None:
                R.unlinked_stones[s].append(title)
        unknown = [k for k in bp if k not in STONES and k != "备注"]
        if unknown:
            R.problem(title, f"推荐黑石 unknown parameters {unknown}")
        rec["black_stones"] = {"stones": stones or None, "note": tu.clean_or_none(bp.get("备注"))}
        if rec["black_stones"]["stones"] is None and rec["black_stones"]["note"] is None:
            rec["black_stones"] = None
    else:
        rec["black_stones"] = None

    # ---- blood ranks
    xt = templates(code, "黑卫血阶")
    if xt:
        xp = params(xt[0])
        ranks = [{"rank": i, "text": tu.clean(xp.get(f"血阶{i}"))} for i in range(1, 7)]
        rec["blood_ranks"] = {"ranks": ranks, "recommendation": tu.clean_or_none(xp.get("血阶推荐及理由"))}
        if all(r["text"] is None for r in ranks) and rec["blood_ranks"]["recommendation"] is None:
            rec["blood_ranks"] = None
    else:
        rec["blood_ranks"] = None

    # ---- divinity (神格)
    st = templates(code, "黑卫神格")
    if st:
        sp = params(st[0])

        def costs(v):
            if v is None:
                return None
            out = []
            for t in mwp.parse(str(v)).filter_templates(recursive=False):
                if str(t.name).strip() == "消耗品icon":
                    amt = str(t.get("2").value).strip() if t.has("2") else ""
                    out.append({"item": str(t.get("1").value).strip(), "amount": to_number(amt.lstrip("×x")), "raw": amt})
            return out or None
        levels = []
        for i in range(1, 11):
            ev = sp.get(f"效果{i}")
            lv = None
            if ev is not None:
                lt = [t for t in mwp.parse(str(ev)).filter_templates(recursive=False) if str(t.name).strip() == "等级Tab"]
                if lt:
                    lv = str(lt[0].get("1").value).strip()
                    ev = str(ev).replace(str(lt[0]), "", 1)
            levels.append({"index": i, "name": tu.clean(sp.get(f"名称{i}")), "level_range": lv,
                           "cost": costs(sp.get(f"消耗{i}")), "effect": tu.clean(ev)})
        rec["divinity"] = {"levels": levels, "total_cost": costs(sp.get("合计"))}
    else:
        rec["divinity"] = None

    # ---- relics (模板:黑卫遗物 = #ask [[分类:遗物]][[黑卫名称::X]])
    if templates(code, "黑卫遗物"):
        rel = relics_by_owner.get(title, [])
        rec["relics"] = [{"name": r["name"], "id": r["id"]} for r in rel] or None
        if not rel:
            notes.append("黑卫遗物 is on the page but no relic in Category:遗物 has 黑卫名称 = this character")
    else:
        rel = relics_by_owner.get(title, [])
        rec["relics"] = None
        if rel:
            notes.append(f"relics {[r['name'] for r in rel]} name this character but the page has no 黑卫遗物 block")

    # ---- battle grid (战格)
    grids = []
    for g in GRID_TEMPLATES:
        for t in templates(code, g):
            gp = params(t)
            grids.append({"template": g, "recommended": tu.clean(gp.get("推荐"))})
    rec["battle_grid"] = grids or None

    # ---- portraits, lore, affection
    lt = templates(code, "黑卫立绘")
    if lt:
        lp = params(lt[0])
        ports = [field(lp, f"立绘{i}") for i in range(1, 5)]
        rec["portraits"] = [p for p in ports if p] or None
    else:
        rec["portraits"] = None

    bg = templates(code, "黑卫背景故事")
    if bg:
        bp = params(bg[0])
        deeds = [field(bp, d) for d in DEEDS]
        rec["lore"] = {"story": field(bp, "角色故事"), "deeds": deeds if any(deeds) else None}
    else:
        rec["lore"] = None

    af = templates(code, "黑卫羁绊好感度")
    if af:
        ap = params(af[0])
        aff = []
        for lv in (2, 5, 10):
            q = field(ap, f"{lv}Q")
            answers = [field(ap, k) for k in (f"{lv}A", f"{lv}A1", f"{lv}A2") if k in ap]
            answers = [a for a in answers if a]
            if q or answers:
                aff.append({"level": lv, "question": q, "answers": answers or None})
        rec["affection"] = aff or None
    else:
        rec["affection"] = None

    for name in ("黑卫", "黑卫技能", "黑卫配装", "推荐符文", "推荐黑石", "黑卫血阶", "黑卫遗物"):
        if not templates(code, name):
            notes.append(f"no {name} template on the page")

    rec["placeholders_nulled"] = placeholders or None
    rec["parse_notes"] = notes or None
    rec.update(prov(page))
    rec["rev_timestamp"] = page.get("rev_timestamp")
    return rec


# ------------------------------------------------------------------ tiers
def build_tiers(chars):
    out = []
    ranked = {}
    sections = {}
    for mode in ("PVE", "PVP"):
        page = load(os.path.join(RAW, "pages", f"{mode}节奏榜.json"))
        as_of = (page.get("rev_timestamp") or "")[:10] or None
        code = mwp.parse(page["wikitext"])
        tables = [t for t in code.filter_tags(recursive=False) if t.tag == "table"]
        if len(tables) != 1:
            R.problem(f"{mode}节奏榜", f"{len(tables)} tables found")
            continue
        rows = [r for r in tables[0].contents.filter_tags(recursive=False) if r.tag == "tr"]
        section_note = None
        for r in rows:
            tags = r.contents.filter_tags(recursive=False)
            cells = [c for c in tags if c.tag == "td"]
            if not cells:
                continue
            tier = tu.clean(cells[0].contents)
            if not tier and len(cells) == 1:
                heading = next((c for c in tags if c.tag == "th"), None)
                if heading:
                    section_note = tu.clean(heading.contents)
                    continue
            if not tier or not re.fullmatch(r"T\d+(?:\.\d+)?", tier):
                R.problem(f"{mode}节奏榜", f"row without tier label: {tier!r}")
                continue
            if section_note:
                sections.setdefault(mode, {})[tier] = section_note
                section_note = None
            for c in cells[1:]:
                links = [lk for lk in c.contents.filter_wikilinks(recursive=True)]
                target = None
                for lk in links:
                    m = re.search(r"\|\s*link=([^|\]]+)", str(lk))
                    if m:
                        target = m.group(1).strip()
                if target is None:
                    text = tu.clean(c.contents)
                    if text and text != "保留":
                        R.problem(f"{mode}节奏榜", f"{tier}: cell without character link: {text!r}")
                    continue
                ps = c.contents.filter_tags(recursive=True, matches=lambda n: n.tag == "p")
                note = tu.clean(ps[0].contents) if ps else None
                key = (target, mode)
                if key in ranked:
                    R.problem(f"{mode}节奏榜", f"{target} listed twice ({ranked[key]['tier']} and {tier})")
                    continue
                ranked[key] = {"tier": tier, "note": note, "as_of": as_of, **prov(page)}
                if target not in chars:
                    R.problem(f"{mode}节奏榜", f"{target} is not a downloaded character")
    for mode in ("PVE", "PVP"):
        page = load(os.path.join(RAW, "pages", f"{mode}节奏榜.json"))
        as_of = (page.get("rev_timestamp") or "")[:10] or None
        ranked_names = [name for name, list_mode in ranked if list_mode == mode and name in chars]
        unranked_names = sorted(name for name in chars if (name, mode) not in ranked)
        for name in ranked_names + unranked_names:
            r = ranked.get((name, mode))
            out.append({
                "character": name,
                "character_id": chars[name],
                "mode": mode,
                "tier": r["tier"] if r else "not_ranked",
                "note": r["note"] if r else None,
                "as_of": as_of,
                **prov(page),
            })
    return out, sections


# ------------------------------------------------------------------ main
def wrap(items, kind):
    return {"kind": kind, "license": LICENSE, "source": SOURCE, "count": len(items), "items": items}


def dump(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def empty_fields(rec):
    paths = []

    def walk(prefix, v):
        if v is None:
            paths.append(prefix)
        elif isinstance(v, dict) and prefix in ("profile", "factions", "affix_recommendations", "lore"):
            for k, x in v.items():
                walk(f"{prefix}.{k}", x)
    for k in ("profile", "element", "rarity", "factions", "affix_recommendations", "note", "skills", "builds",
              "runes", "black_stones", "blood_ranks", "divinity", "relics", "battle_grid", "portraits", "lore", "affection"):
        walk(k, rec.get(k))
    return paths


def main(out=OUT, quiet=False):
    R.__init__()
    tu.UNKNOWN_TEMPLATES.clear()
    if os.path.isdir(os.path.join(out, "characters")):
        shutil.rmtree(os.path.join(out, "characters"))
    char_pages = raw_pages("characters")
    char_ids = {p["title"]: f"char-{p['pageid']}" for p in char_pages}

    gear = build_gear()
    relics = build_relics(char_ids)
    runes = build_runes()
    stones = build_black_stones()
    factions = build_factions()

    classify_extra_pages()
    gear_link = Linker(gear, "gear")
    gear_by_id = {g["id"]: g for g in gear}
    rune_link = Linker(runes, "rune")
    # "before" = only the category pages of step 1 (for the report's before/after counts)
    base_gear_link = Linker([g for g in gear if g["in_category"]], "gear")
    base_rune_link = Linker([r for r in runes if r["in_category"]], "rune")
    lookup_path = os.path.join(RAW, "missing_lookup.json")
    lookup = load(lookup_path)["names"] if os.path.exists(lookup_path) else None
    if lookup is None:
        R.notes.append("data/raw/missing_lookup.json not found — run scraper/resolve_missing.py; wiki lookup info is null")
    db = gamedb.get()
    R.gamedb = db.summary() if db else None
    if db is None:
        R.notes.append("game DB (data/raw/game_db/08.database) not found — game ids are null")
    resolver = Resolver(lookup, db, {"gear": gear, "runes": runes}, char_ids)
    faction_link = Linker(factions, "faction")
    stone_ids = {s["name"]: s["id"] for s in stones}
    relics_by_owner = collections.defaultdict(list)
    for r in relics:
        if r["character"]:
            relics_by_owner[r["character"]["name"]].append(r)

    chars = []
    for page in char_pages:
        try:
            rec = parse_character(page, gear_link, gear_by_id, rune_link, faction_link, stone_ids, relics_by_owner,
                                  base_gear_link, base_rune_link, resolver)
        except Exception as e:  # keep going, report the page
            R.problem(page["title"], f"exception: {type(e).__name__}: {e}")
            continue
        chars.append(rec)
        dump(rec, os.path.join(out, "characters", tu.safe_filename(page["title"]) + ".json"))

    tiers, sections = build_tiers(char_ids)
    dump(wrap(gear, "gear_item"), os.path.join(out, "gear.json"))
    dump(wrap(relics, "relic"), os.path.join(out, "relics.json"))
    dump(wrap(runes, "rune"), os.path.join(out, "runes.json"))
    dump(wrap(stones, "black_stone"), os.path.join(out, "black_stones.json"))
    dump(wrap(factions, "faction"), os.path.join(out, "factions.json"))
    dump({**wrap(tiers, "tier_entry"), "sections": sections}, os.path.join(out, "tiers.json"))

    import report  # noqa: E402
    report.write(os.path.join(out, "REPORT.md"), R, chars, gear, relics, runes, stones, factions, tiers, empty_fields,
                 dict(tu.UNKNOWN_TEMPLATES))
    if quiet:
        return
    print(f"characters {len(chars)}, gear {len(gear)}, relics {len(relics)}, runes {len(runes)}, "
          f"black stones {len(stones)}, factions {len(factions)}, tier entries {len(tiers)}")
    print(f"problems {len(R.unparsed)}, unlinked build items {len(R.unlinked_items)}")
    if tu.UNKNOWN_TEMPLATES:
        print("unknown templates kept as text:", tu.UNKNOWN_TEMPLATES)


if __name__ == "__main__":
    main()
