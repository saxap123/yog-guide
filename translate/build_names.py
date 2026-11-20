"""Step 3.1: data/names.json — Chinese wiki names -> official English names from the game.

Every name is linked through the table row of the game (`name_id`, `title_id`) to the
dictionary, never by free string search:

    character  tpl_sc_hero.title   (title_id)   + profile.real_name = tpl_sc_hero.name (name_id)
    skill      tpl_heroSkill.name  (name_id), tpl_passive_skill.name (name_id)
    gear       tpl_sc_equipment.name (name_id)
    relic      tpl_sc_heirloom.name (name_id)
    rune       tpl_sc_rune.name (name_id)
    black stone tpl_sc_blackStone.name = 黑石·<wiki name> (name_id); English prefix 'Gem·' removed
    faction    tpl_sc_typeLevelTeam.name = <wiki name>阵线 or <wiki name> (name_id)

Not found -> en: null, status: "unverified". Only names used in data/zh are written.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gamedict  # noqa: E402

ROOT = gamedict.ROOT
ZH = os.path.join(ROOT, "data", "zh")
OUT = os.path.join(ROOT, "data", "names.json")

# wiki spelling -> game spelling (checked by hand in the game tables; never guessed).
ALIASES = {"characters": {"璨然银龙": "燦然银龙"}}

DOT_RE = re.compile(r"[·・•‧]")


def load(name):
    with open(os.path.join(ZH, name), encoding="utf-8") as f:
        return json.load(f)


def characters_zh():
    out = []
    for p in sorted(glob.glob(os.path.join(ZH, "characters", "*.json"))):
        with open(p, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


def dotnorm(s: str) -> str:
    return DOT_RE.sub("·", unicodedata.normalize("NFKC", s))


class Rows:
    """name -> rows of one table (exact name, then middle-dot/NFKC normalised)."""

    def __init__(self, rows, field="name"):
        self.exact, self.loose = {}, {}
        for r in rows:
            n = r.get(field, "")
            if n and n != "0":
                self.exact.setdefault(n, []).append(r)
                self.loose.setdefault(dotnorm(n), []).append(r)

    def get(self, name):
        if name in self.exact:
            return self.exact[name], "exact"
        if dotnorm(name) in self.loose:
            return self.loose[dotnorm(name)], "normalised"
        return [], None


def entry(gd, rows, how, table, field="name", game_name=None, strip=None):
    ids = sorted({r["id"] for r in rows}, key=lambda x: (len(x), x))
    tids = sorted({int(r[field + "_id"]) for r in rows if r.get(field + "_id", "0").isdigit()
                   and int(r[field + "_id"]) > 0})
    ens = []
    for t in tids:
        e = gd.en(t)
        if e and e not in ens:
            ens.append(e)
    if not ens:
        return {"en": None, "game_id": ids[0] if len(ids) == 1 else ids,
                "text_id": (tids[0] if len(tids) == 1 else tids) or None, "table": table, "source": None,
                "status": "unverified", "note": "in the game table but the dictionary has no English text"}
    en_full = ens[0]
    en = strip(en_full) if strip else en_full
    e = {"en": en, "game_id": ids[0] if len(ids) == 1 else ids, "text_id": tids[0] if len(tids) == 1 else tids,
         "table": table, "source": "game_db"}
    if strip and en != en_full:
        e["en_game"] = en_full
    if len(ens) > 1:
        e["en_variants"] = ens[1:]
    if game_name:
        e["game_name"] = game_name
    if how == "normalised":
        e["match"] = "normalised (NFKC / middle dot)"
    return e


def fallback(gd, zh, kind):
    """Name not in its own table: any other table row whose field is exactly zh (with an _id)."""
    for ref in gd.scan(zh):
        en = gd.en(ref["text_id"])
        if en:
            return {"en": en, "game_id": ref["game_id"], "text_id": ref["text_id"],
                    "table": ref["table"], "field": ref["field"], "source": "game_db",
                    "match": "not in the %s table; found as %s.%s" % (kind, ref["table"], ref["field"])}
    return None


def similar(zh, pool, n=2):
    import difflib
    return [{"name": m, "status": "unverified"} for m in difflib.get_close_matches(zh, list(pool), n=n, cutoff=0.6)]


def unverified(note, possible_match=None):
    e = {"en": None, "game_id": None, "source": None, "status": "unverified", "note": note}
    if possible_match:
        e["possible_match"] = possible_match
    return e


def hero_owner(skill_id: str, hero_ids: set[str]) -> str | None:
    for n in (3, 2, 4):
        if skill_id[:n] in hero_ids and len(skill_id) - n in (1, 2):
            return skill_id[:n]
    return None


def build():
    gd = gamedict.get()
    if gd is None:
        sys.exit("game files not found under data/raw/game_db/08.database")
    chars = characters_zh()
    gear = load("gear.json")["items"]
    relics = load("relics.json")["items"]
    runes = load("runes.json")["items"]
    stones = load("black_stones.json")["items"]
    factions = load("factions.json")["items"]

    names = {"characters": {}, "skills": {}, "gear": {}, "relics": {}, "runes": {}, "black_stones": {},
             "factions": {}}

    # ---- characters (+ real name) ------------------------------------------------------
    heroes = Rows(gd.heroes, "title")
    hero_of = {}
    for c in chars:
        zh = c["name"]
        game_name = ALIASES["characters"].get(zh)
        rows, how = heroes.get(game_name or zh)
        e = entry(gd, rows, how, "tpl_sc_hero", "title", game_name=game_name) if rows else None
        if e is None:
            e = unverified("not in tpl_sc_hero (game files dated %s; wiki release %s)"
                           % (gamedict.SNAPSHOT_DATE, c["profile"].get("release_date")))
        else:
            row = rows[0]
            hero_of[zh] = row
            rn = gd.field_text(row, "name")
            e["real_name"] = {"zh_game": rn["zh"], "en": rn["en"], "text_id": rn["text_id"]}
            wiki_rn = c["profile"].get("real_name")
            if wiki_rn and rn["zh"] and wiki_rn != rn["zh"]:
                e["real_name"]["zh_wiki"] = wiki_rn
                e["real_name"]["note"] = "wiki real name differs from the game's"
        names["characters"][zh] = e

    # ---- skills ------------------------------------------------------------------------
    hero_ids = {r["id"] for r in gd.heroes}
    skills_by_name = Rows(list(gd.hero_skills.values()))
    passive_by_name = Rows(list(gd.passive_skills.values()))
    for c in chars:
        hero = hero_of.get(c["name"])
        for s in c.get("skills") or []:
            zh = s.get("name")
            if not zh:
                continue
            rows, how = skills_by_name.get(zh)
            table = "tpl_heroSkill"
            if not rows:
                rows, how = passive_by_name.get(zh)
                table = "tpl_passive_skill"
            if hero and rows:
                own = [r for r in rows if hero_owner(r["id"], hero_ids) == hero["id"]]
                general = [r for r in rows if hero_owner(r["id"], hero_ids) is None]
                pick = own or general or rows
            else:
                pick = rows
            e = entry(gd, pick, how, table) if pick else fallback(gd, zh, "skill")
            prev = names["skills"].get(zh)
            if e is None:
                if prev is None:
                    own_names = [r["name"] for r in gd.hero_skills.values()
                                 if hero and hero_owner(r["id"], hero_ids) == hero["id"]]
                    names["skills"][zh] = unverified("no skill of this name in tpl_heroSkill / tpl_passive_skill",
                                                     possible_match=similar(zh, own_names) or None)
                    names["skills"][zh]["characters"] = []
                names["skills"][zh]["characters"].append(c["name"])
                continue
            if prev is None or prev.get("en") is None:
                e["characters"] = (prev or {}).get("characters", [])
                names["skills"][zh] = e
                prev = e
            prev["characters"].append(c["name"])
            if e["en"] != prev["en"]:
                prev.setdefault("en_by_character", {})[c["name"]] = e["en"]

    # ---- gear (wiki pages + every name used in builds) ---------------------------------
    eq = Rows(gd.table("tpl_sc_equipment"))
    gear_names = {g["name"] for g in gear}
    build_names = {}
    for c in chars:
        for b in c.get("builds") or []:
            for n in (b.get("item_ids") or {}):
                build_names.setdefault(n, b.get("unlinked", {}) or {})
            if b.get("signature_weapon"):
                build_names.setdefault(b["signature_weapon"], {})
            for slot, n in (b.get("extracts") or {}).items():
                build_names.setdefault(n, {})
    embed_names = {x["name"] for g in gear for x in (g.get("embed_recommendations") or []) if x.get("name")}
    for zh in sorted(gear_names | set(build_names) | embed_names):
        rows, how = eq.get(zh)
        e = entry(gd, rows, how, "tpl_sc_equipment") if rows else fallback(gd, zh, "equipment")
        if e is None:
            un = build_names.get(zh, {}).get(zh) or {}
            pm = un.get("possible_match") or similar(zh, eq.exact) or None
            e = unverified({"not_an_item": "not an item name (wiki text)",
                            "typo_candidate": "probably a typo on the wiki; not corrected"}.get(
                un.get("reason"), "not in tpl_sc_equipment"),
                possible_match=pm)
        e["in_wiki_gear"] = zh in gear_names
        names["gear"][zh] = e

    # ---- relics ------------------------------------------------------------------------
    hl = Rows(gd.table("tpl_sc_heirloom"))
    for zh in sorted({r["name"] for r in relics} | {x["name"] for c in chars for x in (c.get("relics") or [])}):
        rows, how = hl.get(zh)
        names["relics"][zh] = (entry(gd, rows, how, "tpl_sc_heirloom") if rows else fallback(gd, zh, "heirloom")) \
            or unverified("not in tpl_sc_heirloom", possible_match=similar(zh, hl.exact) or None)

    # ---- runes -------------------------------------------------------------------------
    rn = Rows(gd.table("tpl_sc_rune"))
    rune_names, rune_pm = {r["name"] for r in runes}, {}
    for c in chars:
        rr = c.get("runes") or {}
        for part in ("main", "support"):
            for x in rr.get(part) or []:
                for o in (x.get("options") or [x]):
                    rune_names.add(o["name"])
                    if o.get("unlinked") and o["unlinked"].get("possible_match"):
                        rune_pm[o["name"]] = o["unlinked"]["possible_match"]
    for zh in sorted(rune_names):
        rows, how = rn.get(zh)
        e = entry(gd, rows, how, "tpl_sc_rune") if rows else None
        names["runes"][zh] = e or unverified("probably a typo on the wiki; not corrected" if zh in rune_pm
                                              else "not in tpl_sc_rune", possible_match=rune_pm.get(zh))

    # ---- black stones ------------------------------------------------------------------
    bs = Rows(gd.table("tpl_sc_blackStone"))
    strip = lambda s: re.sub(r"^Gem\s*·\s*", "", s)  # noqa: E731
    for zh in sorted({s["name"] for s in stones} |
                     {x["name"] for c in chars for x in ((c.get("black_stones") or {}).get("stones") or [])}):
        rows, how = bs.get("黑石·" + zh)
        e = entry(gd, rows, how, "tpl_sc_blackStone", game_name="黑石·" + zh, strip=strip) if rows else None
        names["black_stones"][zh] = e or unverified("no 黑石·%s in tpl_sc_blackStone" % zh)

    # ---- factions ----------------------------------------------------------------------
    tl = Rows(gd.table("tpl_sc_typeLevelTeam"))
    fac_names = {f["name"] for f in factions}
    for c in chars:
        fa = c.get("factions") or {}
        for x in [fa.get("base")] + (fa.get("others") or []):
            if x:
                fac_names.add(x["name"])
    for zh in sorted(fac_names):
        rows, how = tl.get(zh + "阵线")
        gname = zh + "阵线"
        if not rows:
            rows, how = tl.get(zh)
            gname = None
        e = entry(gd, rows, how, "tpl_sc_typeLevelTeam", game_name=gname) if rows else None
        names["factions"][zh] = e or unverified("not in tpl_sc_typeLevelTeam")

    # ---- hints for unverified names: a bare dictionary entry with no table row ---------
    for k, d in names.items():
        for zh, e in d.items():
            if e.get("en") is None:
                ex = gd.exact(zh)
                if ex:
                    e["dictionary_only"] = {"en": ex["en"], "text_ids": ex["text_ids"],
                                            "note": "same Chinese text in the dictionary but no table row "
                                                    "links to it; not used"}

    # ---- summary -----------------------------------------------------------------------
    counts = {}
    for k, d in names.items():
        found = sum(1 for e in d.values() if e.get("en"))
        counts[k] = {"total": len(d), "game_db": found, "unverified": len(d) - found}
    out = {
        "meta": {
            "description": "Chinese wiki names -> official English names from the game dictionary",
            "game_snapshot": gamedict.SNAPSHOT_DATE,
            "wiki": "BWIKI 依盖之书 https://wiki.biligame.com/bookofyog/ (CC BY-NC-SA 4.0)",
            "rule": "linked through the table row (name_id/title_id) -> totalLanguageDicText.json; "
                    "not found -> en null, status unverified",
            "generated_by": "translate/build_names.py",
            "counts": counts,
        },
        **names,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return out


if __name__ == "__main__":
    o = build()
    print(json.dumps(o["meta"]["counts"], ensure_ascii=False))
    for k in ("characters", "skills", "gear", "relics", "runes", "black_stones", "factions"):
        for zh, e in o[k].items():
            if not e.get("en"):
                print("unverified", k, zh, e.get("note"))
