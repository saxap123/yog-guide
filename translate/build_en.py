"""Step 3.4: data/zh -> data/en.

Every Chinese string of data/zh is replaced by English from exactly one of these sources
(recorded per record in `i18n`):

  names      data/names.json (characters, skills, gear, relics, runes, black stones, factions)
  glossary   data/glossary.json (stats, slots, qualities, statuses …), also inside stat strings
             like "17532魔力" -> "17532 Intelligence"
  game_db    official English text of the game, used only when the wiki text is the game text
             with its values filled in and all numbers agree (translate/textmatch.py).
             Skill descriptions: only the texts of that very skill (tpl_heroSkill effect_id /
             tpl_passive_skill desc_id); blood ranks: that hero's tpl_sc_heroBlood texts first;
             other effect texts (gear, relic, rune, black stone, faction, divinity): any
             dictionary text of the same shape.
  derived    mechanical rendering: dates, level labels, "500%法术强度的火焰伤害" scaling parts
  translated our translation of the wiki text (translate/manual/texts/*.json), terms per glossary
  lore       not translated (lore.story/deeds, affection, gear/relic flavour text): kept in Chinese

A string with no source is null in data/en and listed in i18n.missing (and in REPORT.md).
Strings still to translate are written to translate/work/todo.json (git-ignored: it quotes game texts).

Ninety-nine items named in builds exist only in the game: they are appended to
data/en/gear.json with source "game_db" (id gear-game-<game id>) and linked from the builds.
"""
from __future__ import annotations

import copy
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedict  # noqa: E402
import terms  # noqa: E402
import textmatch  # noqa: E402
import unofficial  # noqa: E402

ROOT = gamedict.ROOT
ZH = os.path.join(ROOT, "data", "zh")
EN = os.path.join(ROOT, "data", "en")
TM_DIR = os.path.join(ROOT, "translate", "manual", "texts")
TODO = os.path.join(ROOT, "translate", "work", "todo.json")
HAN = re.compile(r"[㐀-鿿]")

SLOT_TYPE = {"1": "武器", "2": "头盔", "3": "衣服", "4": "戒指", "5": "圣物", "6": "鞋子", "7": "腰带",
             "8": "护手", "9": "项链", "10": "副手", "11": "裤子", "12": "徽章", "13": "卡牌", "14": "耳坠"}
SCALING_RE = re.compile(r"^(?P<pct>[\d.%/()\-+~]+%)(?:的)?(?P<stat>物理&法术强度|法术&物理强度|物理与法术强度|"
                        r"法术与物理强度|法术强度|物理强度|攻击力|最大生命值|体质)(?:的)?(?P<eff>.*)$")


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jdump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def has_han(s):
    return isinstance(s, str) and bool(HAN.search(s))


class Translator:
    def __init__(self):
        self.gd = gamedict.get()
        if self.gd is None:
            sys.exit("game files not found under data/raw/game_db/08.database")
        self.si = textmatch.ShapeIndex(self.gd)
        self.names = jload(os.path.join(ROOT, "data", "names.json"))
        self.gloss = jload(os.path.join(ROOT, "data", "glossary.json"))["terms"]
        self.tm = {}
        for p in sorted(glob.glob(os.path.join(TM_DIR, "*.json"))):
            for k, v in jload(p)["texts"].items():
                self.tm[k] = v
        self.todo: dict[str, dict] = {}
        self.used_tm: set[str] = set()
        self.used_names: dict[str, set] = defaultdict(set)
        self.used_terms: set[str] = set()
        self.rec = None  # i18n of the record being built
        self.rejected: list[dict] = []  # game text of the same skill/effect exists but was not used
        self.hero_ids = {r["id"] for r in self.gd.heroes}

    # ---- bookkeeping -------------------------------------------------------------------
    def start(self, name_zh):
        self.rec = {"name_zh": name_zh, "sources": Counter(), "text_sources": {}, "missing": [],
                    "untranslated_lore": []}
        return self.rec

    def finish(self):
        r = self.rec
        r["sources"] = dict(sorted(r["sources"].items()))
        for k in ("text_sources", "missing", "untranslated_lore"):
            if not r[k]:
                r[k] = None
        self.rec = None
        return r

    def _src(self, path, src, detail=None, long=False):
        self.rec["sources"][src] += 1
        if long:
            self.rec["text_sources"][path] = {"source": src, **(detail or {})}

    def _miss(self, path, zh, reason):
        self.rec["missing"].append({"path": path, "zh": zh, "reason": reason})

    def _need(self, zh, kind, path, ref=None):
        t = self.todo.setdefault(zh, {"kind": kind, "where": [], "game_en_reference": None})
        if len(t["where"]) < 5:
            t["where"].append("%s: %s" % (self.rec["name_zh"], path))
        if ref and not t["game_en_reference"]:
            t["game_en_reference"] = ref

    # ---- names -------------------------------------------------------------------------
    def name(self, cat, zh, path):
        if not zh:
            return zh
        e = self.names[cat].get(zh)
        if e is None:
            self._miss(path, zh, "not in names.json/%s" % cat)
            return None
        self.used_names[cat].add(zh)
        if e.get("en"):
            self._src(path, "names")
            return e["en"]
        self._miss(path, zh, "names.json/%s: %s" % (cat, e.get("note") or "unverified"))
        return None

    # ---- glossary ----------------------------------------------------------------------
    def term(self, zh, path, quiet=False):
        if not has_han(zh):
            return zh
        e = self.gloss.get(zh)
        if e is not None:
            self.used_terms.add(zh)
            if e.get("en"):
                self._src(path, "glossary")
                return e["en"]
            if not quiet:
                self._miss(path, zh, "glossary: %s" % (e.get("note") or "no English"))
            return None
        return self.text(zh, "term", path)

    def stat(self, zh, path):
        """'17532魔力' / '43%暴击伤害减免' / '%法术强度' / 'a、b、c' / '全伤害类型减免（PVE要95%）'."""
        if not has_han(zh):
            return zh
        out = []
        for part in zh.split(terms.LIST_SEP):
            part = part.strip()
            m = terms.NOTE_RE.match(part)
            body, note = (m.group("body"), m.group("note")) if m else (part, None)
            st = terms.split_stat(body)
            g = self.gloss.get(st[1]) if st else None
            if not g or not g.get("en"):
                return self.text(zh, "stat", path)
            self.used_terms.add(st[1])
            num = st[0]
            en = ("%s %%" % g["en"]) if num == "%" else ("%s %s" % (num, g["en"])).strip()
            if note:
                note_en = self.text(note, "editorial", path + " (note)")
                if note_en is None:
                    return None
                en += " (%s)" % note_en
            out.append(en)
        self._src(path, "glossary")
        return ", ".join(out)

    # ---- free texts --------------------------------------------------------------------
    def text(self, zh, kind, path, own_ids=(), allow_global=True, long=False):
        if not has_han(zh):
            return zh
        ref = None
        for tid in own_ids:
            if not tid:
                continue
            r = textmatch.fill_any(zh, self.gd.zh(tid), self.gd.en(tid))
            if r:
                self._src(path, "game_db", {"text_id": tid, "match": "loose" if r["loose"] else "exact"}, long)
                return r["en"]
            if not ref and self.gd.en(tid):
                ref = {"text_id": tid, "zh": self.gd.zh(tid), "en": self.gd.en(tid)}
        if ref:
            same_wording = textmatch.NUMERIC_RUN.sub("#", textmatch.loose(zh)) == \
                textmatch.NUMERIC_RUN.sub("#", textmatch.loose(ref["zh"]))
            self.rejected.append({"record": self.rec["name_zh"], "path": path, "kind": kind,
                                  "text_id": ref["text_id"],
                                  "reason": "numbers differ" if same_wording else "wording differs",
                                  "wiki": zh, "game": ref["zh"],
                                  "wiki_numbers": gamedict.numbers(zh),
                                  "game_numbers": gamedict.numbers(textmatch.PH_RE.sub("{}", ref["zh"]))})
        if allow_global:
            ex = self.gd.exact(zh)
            if ex and Counter(gamedict.numbers(zh)) == Counter(gamedict.numbers(ex["en"])):
                self._src(path, "game_db", {"text_id": ex["text_id"], "match": "exact"}, long)
                return ex["en"]
            r = self.si.match(zh)
            if r:
                self._src(path, "game_db", {"text_id": r["text_id"], "match": "loose" if r["loose"] else "exact"},
                          long)
                return r["en"]
        if zh in self.tm:
            self.used_tm.add(zh)
            v = self.tm[zh]
            if v is None:
                self._miss(path, zh, "not translatable (see translate/manual/texts)")
                return None
            self._src(path, "translated", None, long)
            return v
        self._need(zh, kind, path, ref)
        self._miss(path, zh, "not translated yet")
        return None

    def lore(self, value, path):
        if value is not None:
            self.rec["untranslated_lore"].append(path)
            self.rec["sources"]["lore"] += 1
        return value

    # ---- derived -----------------------------------------------------------------------
    def date(self, zh, path):
        if not zh:
            return zh
        m = re.fullmatch(r"(\d{4})年(\d{1,2})月(\d{1,2})日", zh)
        if m:
            self._src(path, "derived")
            return "%s-%02d-%02d" % (m.group(1), int(m.group(2)), int(m.group(3)))
        m = re.fullmatch(r"(\d{1,2})月(\d{1,2})日", zh)
        if m and 1 <= int(m.group(1)) <= 12:
            self._src(path, "derived")
            return "--%02d-%02d" % (int(m.group(1)), int(m.group(2)))   # ISO 8601 month-day
        return self.text(zh, "profile", path)

    def scaling_text(self, zh, path):
        m = SCALING_RE.match(zh or "")
        if m:
            stat = self.gloss.get(m.group("stat"), {}).get("en")
            eff = m.group("eff")
            eff_en = self.gloss.get(eff, {}).get("en") if eff else None
            if stat and (not eff or eff_en):
                self.used_terms.update(x for x in (m.group("stat"), eff) if x)
                self._src(path, "derived")
                return ("%s equal to %s of %s" % (eff_en, m.group("pct"), stat)) if eff else \
                    ("%s of %s" % (m.group("pct"), stat))
        return self.text(zh, "skill_fragment", path)

    def cost(self, zh, path):
        if not has_han(zh):
            return zh
        st = terms.split_stat(zh)
        if st and self.gloss.get(st[1], {}).get("en"):
            self.used_terms.add(st[1])
            self._src(path, "glossary")
            return ("%s %s" % (st[0], self.gloss[st[1]]["en"])).strip()
        return self.term(zh, path)


# =========================================================================================
# game-only gear
# =========================================================================================

def fmt_range(lo, hi, percent):
    """Value range as the wiki writes item skills: '(10.00%-20.00%)' for percents."""
    try:
        a, b = float(lo), float(hi)
    except ValueError:
        return None
    if percent:
        return "(%.2f%%-%.2f%%)" % (a * 100, b * 100) if a != b else "%.2f%%" % (a * 100)
    return "(%s-%s)" % (lo, hi) if a != b else lo


def gear_skill_affixes(gd, row):
    out = []
    grp = gd.affix_groups.get(row.get("affixs_skill", "0"))
    if not grp:
        return out
    # "a|b" = alternatives, "a-b" = affix a plus affix b (e.g. base skill + 铸魂 upgrade)
    ids = [x for part in grp.get("affixs", "").split("|") for x in part.split("-")]
    for aid in ids:
        a = gd.affixes.get(aid)
        if a and int(a.get("skillDes_id") or 0) not in (0, 7300):
            out.append(a)
    return out


def render_affix(gd, a, lang):
    tid = int(a["skillDes_id"])
    tpl = gd.zh(tid) if lang == "zh" else gd.en(tid)
    if not tpl:
        return None
    pct = a.get("showPersent") == "1"
    val = fmt_range(a.get("min_1", "0"), a.get("max_1", "0"), pct)
    if "{0}" in tpl and val is None:
        return None
    if pct and val and "{0}%" in tpl:      # the template writes the % sign itself
        val = val.replace("%", "")
    return tpl.replace("{0}", val or "")


def quality_names(gd):
    out = {}
    for r in gd.table("tpl_sc_quality"):
        n = r.get("name", "")
        if n.startswith("强化-"):
            out[r["quality"]] = n[3:]
    return out


def game_only_gear(T: Translator, chars_zh, wiki_gear_names):
    gd = T.gd
    eq_rows = defaultdict(list)
    for r in gd.table("tpl_sc_equipment"):
        eq_rows[r["name"]].append(r)
    qn = quality_names(gd)
    used = defaultdict(list)
    linked = set()   # names step 2 already linked to a wiki gear page
    for c in chars_zh:
        for b in c.get("builds") or []:
            for slot, n in (b.get("slots") or {}).items():
                names_ = [n] + ((b.get("alternatives") or {}).get(slot) or [])
                for x in names_:
                    if x:
                        used[x].append("%s / %s / %s" % (c["name"], b["level_tier"], slot))
            for slot, x in (b.get("extracts") or {}).items():
                used[x].append("%s / %s / %s (extract)" % (c["name"], b["level_tier"], slot))
            if b.get("signature_weapon"):
                used[b["signature_weapon"]].append("%s / %s / signature weapon" % (c["name"], b["level_tier"]))
            for n, gid in (b.get("item_ids") or {}).items():
                if gid:
                    linked.add(n)
    items = []
    for zh in sorted(used):
        if zh in wiki_gear_names or zh in linked:
            continue
        ne = T.names["gear"].get(zh) or {}
        if not ne.get("en") or ne.get("table") != "tpl_sc_equipment":
            continue
        rows = eq_rows.get(zh) or []
        if not rows:
            continue
        T.start(zh)
        T.used_names["gear"].add(zh)
        row = rows[0]
        ids = [r["id"] for r in rows]
        slot_zh = SLOT_TYPE.get(row.get("type"))
        q = row.get("quality", "0")
        qzh = qn.get(q)
        affs = gear_skill_affixes(gd, row)
        skill_zh = "\n".join(filter(None, (render_affix(gd, a, "zh") for a in affs))) or None
        skill_en = "\n".join(filter(None, (render_affix(gd, a, "en") for a in affs))) or None
        skill_note = None
        if skill_zh and skill_en and Counter(gamedict.numbers(skill_zh)) != Counter(gamedict.numbers(skill_en)):
            skill_note = ("the game's English skill text has other numbers than its Chinese text; not used "
                          "(English: %s)" % skill_en)
            skill_en = None
        it = {
            "id": "gear-game-%s" % row["id"],
            "name": ne["en"],
            "name_zh": zh,
            "page_title": None,
            "slot": T.term(slot_zh, "slot") if slot_zh else None,
            "slot_zh": slot_zh,
            "quality": T.term(qzh, "quality") if qzh else None,
            "quality_zh": qzh,
            "max_level": int(row["maxLevel"]) if row.get("maxLevel", "0").isdigit() and int(row["maxLevel"]) else None,
            "skill": skill_en,
            "skill_zh": skill_zh,
            "game": {
                "table": "tpl_sc_equipment",
                "game_id": ids[0] if len(ids) == 1 else ids,
                "name_text_id": ne.get("text_id"),
                "type": row.get("type"),
                "quality": q,
                "equipmentGrade": row.get("equipmentGrade"),
                "skill_affixes": [{"affix_id": a["id"], "affix_name": a.get("name"), "text_id": int(a["skillDes_id"]), "min": a.get("min_1"),
                                   "max": a.get("max_1"), "percent": a.get("showPersent") == "1"} for a in affs]
                or None,
                "snapshot": gamedict.SNAPSHOT_DATE,
            },
            "used_in": used[zh],
            "source": "game_db",
            "notes": [n for n in (
                None if qzh else "quality not fixed in tpl_sc_equipment (quality=%s); the item can drop "
                                 "in the grades listed in game.equipmentGrade" % q,
                None if affs else "no skill affix in tpl_sc_equipment.affixs_skill",
                skill_note,
                "skill values rendered from affix min_1/max_1 in the wiki's '(a%-b%)' format" if affs else None,
                "stats (basic/prefix/suffix affixes) are random rolls in the game tables and are not listed",
            ) if n],
        }
        it["i18n"] = T.finish()
        items.append(it)
    return items


def check_range_format(T: Translator, gear_zh):
    """How often the '(a%-b%)' rendering of the game affix equals the wiki's own skill text."""
    gd = T.gd
    rows = defaultdict(list)
    for r in gd.table("tpl_sc_equipment"):
        rows[r["name"]].append(r)
    same = total = 0
    for g in gear_zh:
        if not g.get("skill") or not rows.get(g["name"]):
            continue
        affs = gear_skill_affixes(gd, rows[g["name"]][0])
        if not affs:
            continue
        total += 1
        z = "\n".join(filter(None, (render_affix(gd, a, "zh") for a in affs)))
        if textmatch.norm(z) == textmatch.norm(g["skill"]):
            same += 1
    return same, total


# =========================================================================================
# records
# =========================================================================================

def hero_row(T, zh):
    e = T.names["characters"].get(zh) or {}
    gid = e.get("game_id")
    for r in T.gd.heroes:
        if r["id"] == gid:
            return r
    return None


def skill_text_ids(T, hero, skill_name):
    """Dictionary ids of the texts of this very skill (own hero first, then general skills)."""
    ids = []
    rows = [r for r in T.gd.hero_skills.values() if r.get("name") == skill_name]
    prow = [r for r in T.gd.passive_skills.values() if r.get("name") == skill_name]

    def owner(i):
        for n in (3, 2, 4):
            if i[:n] in T.hero_ids and len(i) - n in (1, 2):
                return i[:n]
        return None

    for group in (rows, prow):
        if hero:
            own = [r for r in group if owner(r["id"]) == hero["id"]]
            gen = [r for r in group if owner(r["id"]) is None]
            group = own or gen
        for r in group:
            for f in ("effect_id", "desc_id"):
                v = r.get(f, "0")
                if v.isdigit() and int(v) > 0:
                    ids.append(int(v))
    return list(dict.fromkeys(ids))


def build_character(T: Translator, c, gear_game_ids):
    T.start(c["name"])
    e = copy.deepcopy(c)
    hero = hero_row(T, c["name"])
    ne = T.names["characters"].get(c["name"]) or {}
    e["name"] = T.name("characters", c["name"], "name")

    p, pz = e["profile"], c["profile"]
    rn = ne.get("real_name") or {}
    if pz.get("real_name"):
        if rn.get("en") and rn.get("zh_game") == pz["real_name"]:
            T._src("profile.real_name", "names")
            p["real_name"] = rn["en"]
        else:
            p["real_name"] = T.text(pz["real_name"], "profile", "profile.real_name")
    p["gender"] = T.term(pz.get("gender"), "profile.gender")
    p["race"] = T.term(pz.get("race"), "profile.race")
    p["birthday"] = T.date(pz.get("birthday"), "profile.birthday")
    p["birthplace"] = T.text(pz.get("birthplace"), "profile", "profile.birthplace")
    p["height_weight"] = T.text(pz.get("height_weight"), "profile", "profile.height_weight")
    for k in ("specialties", "likes", "dislikes"):
        if pz.get(k):
            p[k] = [T.text(x, "profile", "profile.%s[%d]" % (k, i)) for i, x in enumerate(pz[k])]
    p["release_date"] = T.date(pz.get("release_date"), "profile.release_date")

    e["element"] = T.term(c.get("element"), "element")
    fa = e["factions"]
    if fa.get("base"):
        fa["base"]["name"] = T.name("factions", c["factions"]["base"]["name"], "factions.base")
    for i, x in enumerate(fa.get("others") or []):
        x["name"] = T.name("factions", c["factions"]["others"][i]["name"], "factions.others[%d]" % i)

    for k in ("primary", "secondary"):
        v = c["affix_recommendations"].get(k)
        if v:
            e["affix_recommendations"][k] = [T.stat(x, "affix_recommendations.%s[%d]" % (k, i))
                                             for i, x in enumerate(v)]
    e["note"] = T.text(c.get("note"), "editorial", "note", long=True)

    for i, s in enumerate(e.get("skills") or []):
        sz = c["skills"][i]
        base = "skills[%d]" % i
        s["slot"] = T.term(sz["slot"], base + ".slot")
        s["category"] = T.term(sz["category"], base + ".category")
        s["name"] = T.name("skills", sz["name"], base + ".name") if sz.get("name") else None
        s["name_zh"] = sz.get("name")
        s["cooldown_raw"] = T.text(sz.get("cooldown_raw"), "skill_fragment", base + ".cooldown_raw")
        s["cost"] = T.cost(sz.get("cost"), base + ".cost")
        ids = skill_text_ids(T, hero, sz["name"]) if sz.get("name") else []
        s["description"] = T.text(sz.get("description"), "skill", base + ".description", own_ids=ids,
                                  allow_global=False, long=True)
        for j, x in enumerate(s.get("scaling") or []):
            xz = sz["scaling"][j]
            x["stat"] = T.term(xz["stat"], base + ".scaling[%d].stat" % j)
            x["effect"] = T.term(xz["effect"], base + ".scaling[%d].effect" % j) if xz.get("effect") else None
            x["text"] = T.scaling_text(xz["text"], base + ".scaling[%d].text" % j)

    for i, b in enumerate(e.get("builds") or []):
        bz = c["builds"][i]
        base = "builds[%d]" % i
        b["level_tier"] = T.text(bz.get("level_tier"), "label", base + ".level_tier")
        b["qualifier"] = T.text(bz.get("qualifier"), "label", base + ".qualifier")

        def item(n, path):
            return T.name("gear", n, path) if n else None

        if bz.get("slots"):
            b["slots"] = {T.term(k, base + ".slots{key}"): item(v, base + ".slots.%s" % k)
                          for k, v in bz["slots"].items()}
        if bz.get("alternatives"):
            b["alternatives"] = {T.term(k, base + ".alternatives{key}"):
                                 [item(x, base + ".alternatives.%s[%d]" % (k, j)) for j, x in enumerate(v)]
                                 for k, v in bz["alternatives"].items()}
        if bz.get("extracts"):
            b["extracts"] = {T.term(k, base + ".extracts{key}"): item(v, base + ".extracts.%s" % k)
                             for k, v in bz["extracts"].items()}
        b["signature_weapon"] = item(bz.get("signature_weapon"), base + ".signature_weapon")
        ids = {}
        for n, gid in (bz.get("item_ids") or {}).items():
            ids[n] = gid or gear_game_ids.get(n)
        b["item_ids"] = ids or bz.get("item_ids")

    if c.get("runes"):
        r = e["runes"]
        for part in ("main", "support"):
            for i, x in enumerate(r.get(part) or []):
                xz = c["runes"][part][i]
                x["name"] = T.name("runes", xz["name"], "runes.%s[%d]" % (part, i)) \
                    if xz["name"] in T.names["runes"] else T.text(xz["name"], "label", "runes.%s[%d]" % (part, i))
                for j, o in enumerate(x.get("options") or []):
                    o["name"] = T.name("runes", xz["options"][j]["name"], "runes.%s[%d].options[%d]" % (part, i, j))
        r["note"] = T.text(c["runes"].get("note"), "editorial", "runes.note", long=True)

    if c.get("black_stones"):
        bs = e["black_stones"]
        for i, x in enumerate(bs.get("stones") or []):
            x["name"] = T.name("black_stones", c["black_stones"]["stones"][i]["name"], "black_stones.stones[%d]" % i)
            if has_han(x.get("raw")):
                x["raw"] = T.text(c["black_stones"]["stones"][i]["raw"], "editorial", "black_stones.stones[%d].raw" % i)
        bs["note"] = T.text(c["black_stones"].get("note"), "editorial", "black_stones.note", long=True)

    if c.get("blood_ranks"):
        br = e["blood_ranks"]
        blood = None
        if hero:
            for row in T.gd.table("tpl_sc_heroBlood"):
                if row.get("id") == hero["id"]:
                    blood = row
        own = [int(x) for x in (blood or {}).get("skill_desc_id", "").split("|") if x.isdigit()]
        for i, x in enumerate(br.get("ranks") or []):
            xz = c["blood_ranks"]["ranks"][i]
            k = xz["rank"] - 1
            x["text"] = T.text(xz["text"], "blood_rank", "blood_ranks.ranks[%d]" % i,
                               own_ids=own[k:k + 1] + [t for t in own if t not in own[k:k + 1]], long=True)
        br["recommendation"] = T.text(c["blood_ranks"].get("recommendation"), "editorial",
                                      "blood_ranks.recommendation", long=True)

    if c.get("divinity"):
        dv = e["divinity"]
        for i, x in enumerate(dv.get("levels") or []):
            xz = c["divinity"]["levels"][i]
            x["name"] = T.text(xz.get("name"), "divinity_name", "divinity.levels[%d].name" % i)
            for j, co in enumerate(x.get("cost") or []):
                co["item"] = T.term(xz["cost"][j]["item"], "divinity.levels[%d].cost[%d]" % (i, j))
            x["effect"] = T.text(xz.get("effect"), "divinity", "divinity.levels[%d].effect" % i, long=True)
        for j, co in enumerate(dv.get("total_cost") or []):
            co["item"] = T.term(c["divinity"]["total_cost"][j]["item"], "divinity.total_cost[%d]" % j)

    for i, x in enumerate(e.get("relics") or []):
        x["name"] = T.name("relics", c["relics"][i]["name"], "relics[%d]" % i)
    for i, x in enumerate(e.get("battle_grid") or []):
        x["template"] = T.term(c["battle_grid"][i]["template"], "battle_grid[%d]" % i)
        if has_han(x.get("recommended")):
            x["recommended"] = T.text(c["battle_grid"][i]["recommended"], "editorial", "battle_grid[%d].rec" % i)

    e["lore"] = T.lore(c.get("lore"), "lore") if c.get("lore") else c.get("lore")
    e["affection"] = T.lore(c.get("affection"), "affection") if c.get("affection") else None
    e["i18n"] = T.finish()
    return e


def build_gear(T, g, eq_rows):
    T.start(g["name"])
    e = copy.deepcopy(g)
    e["name"] = T.name("gear", g["name"], "name")
    e["slot"] = T.term(g.get("slot"), "slot")
    e["quality"] = T.term(g.get("quality"), "quality")
    for k in ("main_stat",):
        if g.get(k):
            e[k] = T.stat(g[k], k)
    for k in ("sub_stats", "prefixes", "suffixes", "exclusive"):
        if g.get(k):
            e[k] = [T.stat(x, "%s[%d]" % (k, i)) for i, x in enumerate(g[k])]
    own = []
    rows = eq_rows.get(g["name"]) or []
    if rows:
        own = [int(a["skillDes_id"]) for a in gear_skill_affixes(T.gd, rows[0])]
    e["skill"] = T.text(g.get("skill"), "gear_skill", "skill", own_ids=own, long=True)
    if g.get("set"):
        s = e["set"]
        s["name"] = T.text(g["set"]["name"], "set_name", "set.name")
        for i, b in enumerate(s.get("bonuses") or []):
            bz = g["set"]["bonuses"][i]
            b["text"] = T.text(bz["text"], "set_bonus", "set.bonuses[%d]" % i, long=True)
            b["set"] = T.text(bz["set"], "set_name", "set.bonuses[%d].set" % i)
        if has_han(s.get("raw")):
            s["raw"] = T.text(g["set"]["raw"], "set_bonus", "set.raw", long=True)
    e["extract_skill"] = T.term(g.get("extract_skill"), "extract_skill")
    for i, x in enumerate(e.get("embed_recommendations") or []):
        xz = g["embed_recommendations"][i]
        x["name"] = T.name("gear", xz["name"], "embed_recommendations[%d].name" % i)
        x["effect"] = T.text(xz["effect"], "gear_skill", "embed_recommendations[%d].effect" % i, long=True)
    e["embed_recommendations_raw"] = T.term(g.get("embed_recommendations_raw"), "embed_recommendations_raw")
    if g.get("obtain"):
        e["obtain"] = [T.term(x, "obtain[%d]" % i) for i, x in enumerate(g["obtain"])]
    e["description"] = T.lore(g.get("description"), "description")
    e["source"] = "wiki"
    e["i18n"] = T.finish()
    return e


def build_relic(T, r):
    T.start(r["name"])
    e = copy.deepcopy(r)
    e["name"] = T.name("relics", r["name"], "name")
    e["type"] = T.term(r.get("type"), "type")
    e["quality"] = T.term(r.get("quality"), "quality")
    if r.get("character"):
        e["character"]["name"] = T.name("characters", r["character"]["name"], "character")
    for k in ("exclusive", "prefixes", "suffixes"):
        if r.get(k):
            e[k] = [T.stat(x, "%s[%d]" % (k, i)) for i, x in enumerate(r[k])]
    own = []
    for row in T.gd.table("tpl_sc_heirloom"):
        if row.get("name") == r["name"]:
            own = [int(row[f]) for f in ("skillDes1_id", "skillDes2_id") if row.get(f, "0").isdigit()
                   and int(row[f]) > 0]
    if r.get("skills"):
        e["skills"] = [T.text(x, "relic_skill", "skills[%d]" % i, own_ids=own, long=True)
                       for i, x in enumerate(r["skills"])]
    e["advanced_fixed_skill"] = T.text(r.get("advanced_fixed_skill"), "relic_skill", "advanced_fixed_skill", long=True)
    if r.get("advanced_random_skills"):
        e["advanced_random_skills"] = [T.text(x, "relic_skill", "advanced_random_skills[%d]" % i, long=True)
                                       for i, x in enumerate(r["advanced_random_skills"])]
    if r.get("obtain"):
        e["obtain"] = [T.term(x, "obtain[%d]" % i) for i, x in enumerate(r["obtain"])]
    e["description"] = T.lore(r.get("description"), "description")
    e["i18n"] = T.finish()
    return e


def build_rune(T, r):
    T.start(r["name"])
    e = copy.deepcopy(r)
    e["name"] = T.name("runes", r["name"], "name")
    e["type"] = T.term(r.get("type"), "type")
    for k in ("attribute", "exclusive_attribute"):
        if r.get(k):
            e[k] = T.stat(r[k], k)
    for k in ("exclusive", "prefixes", "suffixes"):
        if r.get(k):
            e[k] = [T.stat(x, "%s[%d]" % (k, i)) for i, x in enumerate(r[k])]
    if r.get("skills"):
        e["skills"] = [T.text(x, "rune_skill", "skills[%d]" % i, long=True) for i, x in enumerate(r["skills"])]
    for i, x in enumerate(e.get("edges") or []):
        x["color_name"] = T.term(r["edges"][i]["color_name"], "edges[%d]" % i)
    if r.get("obtain"):
        e["obtain"] = [T.term(x, "obtain[%d]" % i) for i, x in enumerate(r["obtain"])]
    e["i18n"] = T.finish()
    return e


def build_stone(T, s):
    T.start(s["name"])
    e = copy.deepcopy(s)
    e["name"] = T.name("black_stones", s["name"], "name")
    for i, x in enumerate(e.get("effects") or []):
        xz = s["effects"][i]
        x["text"] = T.text(xz["text"], "black_stone", "effects[%d].text" % i, long=True)
        x["text_template"] = T.text(xz["text_template"], "black_stone", "effects[%d].text_template" % i, long=True)
    e["i18n"] = T.finish()
    return e


def build_faction(T, f):
    T.start(f["name"])
    e = copy.deepcopy(f)
    e["name"] = T.name("factions", f["name"], "name")
    e["type"] = T.term(f.get("type"), "type")
    e["effect_on_page"] = T.text(f.get("effect_on_page"), "faction", "effect_on_page", long=True)
    own = []
    gname = (T.names["factions"].get(f["name"]) or {}).get("game_name") or f["name"]
    for row in T.gd.table("tpl_sc_typeLevelTeam"):
        if row.get("name") in (gname, f["name"]):
            own = [int(row[k]) for k in ("lowSkillDes_id", "middleSkillDes_id", "highSkillDes_id", "superSkillDes_id")
                   if row.get(k, "0").isdigit() and int(row[k]) > 0]
    for i, x in enumerate(e.get("thresholds") or []):
        x["text"] = T.text(f["thresholds"][i]["text"], "faction", "thresholds[%d]" % i, own_ids=own, long=True)
    e["i18n"] = T.finish()
    return e


def build_tier(T, t):
    T.start(t["character"])
    e = copy.deepcopy(t)
    e["character"] = T.name("characters", t["character"], "character")
    e["character_zh"] = t["character"]
    e["note"] = T.text(t.get("note"), "editorial", "note", long=True)
    e["i18n"] = T.finish()
    return e


def collection(zh_coll, items, extra=None):
    out = {k: v for k, v in zh_coll.items() if k != "items"}
    out["language"] = "en"
    out["translation"] = "see data/names.json, data/glossary.json, translate/README.md"
    if extra:
        out.update(extra)
    out["count"] = len(items)
    out["items"] = items
    return out


def build():
    T = Translator()
    chars = [jload(p) for p in sorted(glob.glob(os.path.join(ZH, "characters", "*.json")))]
    gear_zh = jload(os.path.join(ZH, "gear.json"))
    eq_rows = defaultdict(list)
    for r in T.gd.table("tpl_sc_equipment"):
        eq_rows[r["name"]].append(r)

    # game-only gear first: builds link to it
    wiki_names = {g["name"] for g in gear_zh["items"]}
    game_gear = game_only_gear(T, chars, wiki_names)
    gear_game_ids = {g["name_zh"]: g["id"] for g in game_gear}

    out_chars = [build_character(T, c, gear_game_ids) for c in chars]
    gear_items = [build_gear(T, g, eq_rows) for g in gear_zh["items"]] + game_gear
    rel = jload(os.path.join(ZH, "relics.json"))
    run = jload(os.path.join(ZH, "runes.json"))
    sto = jload(os.path.join(ZH, "black_stones.json"))
    fac = jload(os.path.join(ZH, "factions.json"))
    tie = jload(os.path.join(ZH, "tiers.json"))
    rel_items = [build_relic(T, r) for r in rel["items"]]
    run_items = [build_rune(T, r) for r in run["items"]]
    sto_items = [build_stone(T, s) for s in sto["items"]]
    fac_items = [build_faction(T, f) for f in fac["items"]]
    tie_items = [build_tier(T, t) for t in tie["items"]]

    # step 4: names still in Chinese -> unofficial English (translate/manual/unofficial_names.json)
    unknown = Counter()
    for recs, top_skip in ((out_chars, ()), (gear_items, ("description",)), (rel_items, ("description",)),
                           (run_items, ()), (sto_items, ()), (fac_items, ()), (tie_items, ())):
        for rec in recs:
            unknown.update(unofficial.apply(rec, top_skip))
    if unknown:
        print("names left in Chinese (add them to translate/manual/unofficial_names.json):", dict(unknown))

    # write
    for old in glob.glob(os.path.join(EN, "characters", "*.json")):
        os.remove(old)
    for c, cz in zip(out_chars, chars):
        jdump(c, os.path.join(EN, "characters", "%s.json" % cz["id"]))
    same, total = check_range_format(T, gear_zh["items"])
    jdump(collection(gear_zh, gear_items, {
        "game_only_items": len(game_gear),
        "game_only_note": "items with source game_db are named in wiki builds but have no wiki page; "
                          "data from the game files dated %s (no source_url/revid). Their skill value "
                          "ranges use the wiki format, which equals the wiki text for %d of %d wiki items "
                          "checked (the others differ in wording, typos or fixed values on the wiki)."
                          % (gamedict.SNAPSHOT_DATE, same, total)}),
        os.path.join(EN, "gear.json"))
    jdump(collection(rel, rel_items), os.path.join(EN, "relics.json"))
    jdump(collection(run, run_items), os.path.join(EN, "runes.json"))
    jdump(collection(sto, sto_items), os.path.join(EN, "black_stones.json"))
    jdump(collection(fac, fac_items), os.path.join(EN, "factions.json"))
    jdump(collection(tie, tie_items), os.path.join(EN, "tiers.json"))

    jdump({"about": "texts of the very same skill/effect exist in the game but differ from the wiki "
                    "(numbers or wording), so the wiki text was translated instead",
           "count": len(T.rejected), "items": T.rejected}, os.path.join(ROOT, "translate", "work", "rejected_game_texts.json"))
    # numbers only (no game text): same wording, different numbers -> shown as a warning on the site
    nd, seen = [], set()
    for x in T.rejected:
        if x["reason"] == "numbers differ" and (x["record"], x["path"]) not in seen:
            seen.add((x["record"], x["path"]))
            nd.append({"record_zh": x["record"], "kind": x["kind"], "path": x["path"], "text_id": x["text_id"],
                       "wiki_numbers": x["wiki_numbers"], "game_numbers": x["game_numbers"]})
    jdump({"about": "texts whose game version (game files dated %s) has the same wording as the wiki but other "
                    "numbers; the wiki text is used. game_numbers are the literal numbers of the game text; its "
                    "per-level {n} values are not included. Numbers only, no game text." % gamedict.SNAPSHOT_DATE,
           "count": len(nd), "items": nd}, os.path.join(EN, "discrepancies.json"))
    jdump({"about": "Chinese strings that still need a translation (kind, where, official English of "
                    "the same skill as a reference when its numbers differ from the wiki)",
           "count": len(T.todo), "chars": sum(len(k) for k in T.todo),
           "texts": dict(sorted(T.todo.items(), key=lambda kv: (kv[1]["kind"], kv[0])))}, TODO)
    return T, out_chars, gear_items, (same, total)


if __name__ == "__main__":
    T, chars, gear, rng = build()
    tot = Counter()
    for p in glob.glob(os.path.join(EN, "**", "*.json"), recursive=True):
        d = jload(p)
        recs = d["items"] if "items" in d else [d]
        for r in recs:
            tot.update((r.get("i18n") or {}).get("sources") or {})
    print("sources", dict(tot))
    print("todo strings", len(T.todo), "chars", sum(len(k) for k in T.todo))
    print("todo by kind", Counter(v["kind"] for v in T.todo.values()))
    print("game-only gear", sum(1 for g in gear if g.get("source") == "game_db"), "range format check", rng)
