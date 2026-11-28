"""Step 3.7: data/en/REPORT.md — sources of the English, unverified names, number checks, examples.

    python translate/write_report.py      (after build_names, build_glossary, build_en)
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_numbers  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN = os.path.join(ROOT, "data", "en")
ZH = os.path.join(ROOT, "data", "zh")
OUT = os.path.join(EN, "REPORT.md")
EXAMPLES = ["飞焰铃舞", "千宵月守", "璨然银龙"]
CAT_TITLE = {"characters": "characters", "skills": "skills", "gear": "items (gear)", "relics": "relics",
             "runes": "runes", "black_stones": "黑石 (black stones)", "factions": "阵线 (factions)"}


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def pct(a, b):
    return "%.1f%%" % (100.0 * a / b) if b else "—"


def esc(s):
    return (s or "").replace("|", "\\|").replace("\n", " / ")


def records():
    for p in sorted(glob.glob(os.path.join(EN, "characters", "*.json"))):
        yield "character", jload(p)
    for name in ("gear", "relics", "runes", "black_stones", "factions", "tiers"):
        for it in jload(os.path.join(EN, name + ".json"))["items"]:
            yield name, it


def build():
    names = jload(os.path.join(ROOT, "data", "names.json"))
    gloss = jload(os.path.join(ROOT, "data", "glossary.json"))
    L = []
    w = L.append
    w("# Step 3 report — names, glossary, translation (data/zh → data/en)\n")
    w("Wiki data: BWIKI 依盖之书 <https://wiki.biligame.com/bookofyog/> (CC BY-NC-SA 4.0). "
      "Official English: game files dated %s and publisher announcements. "
      "Only strings that are used are kept (`data/names.json`, `data/glossary.json`, `data/en`)."
      % names["meta"]["game_snapshot"])
    w("")
    w("Regenerate: `python translate/build_names.py && python translate/build_glossary.py && "
      "python translate/build_en.py && python translate/check_numbers.py && python translate/write_report.py`.\n")

    # ---- names ----------------------------------------------------------------------
    w("## Names (`data/names.json`)\n")
    w("Names come from the game tables and dictionary when available. "
      "`translate/manual/names.json` supplies publisher spellings and translations for newer names.\n")
    w("| category | names | from the game | publisher | translated | empty (unverified) |")
    w("|---|---|---|---|---|---|")
    T = Counter()
    for cat, d in names.items():
        if cat == "meta":
            continue
        n = len(d)
        g = sum(1 for e in d.values() if e.get("en") and e.get("source") == "game_db")
        tr = sum(1 for e in d.values() if e.get("en") and e.get("source") == "translated")
        pub = sum(1 for e in d.values() if e.get("en") and e.get("source") == "publisher")
        missing = n - g - tr - pub
        T.update({"n": n, "g": g, "p": pub, "t": tr, "missing": missing})
        w("| %s | %d | %d (%s) | %d | %d | %d (%s) |" % (CAT_TITLE.get(cat, cat), n, g, pct(g, n), pub, tr,
                                                         missing, pct(missing, n)))
    w("| **all** | %d | %d (%s) | %d | %d | %d (%s) |\n" % (T["n"], T["g"], pct(T["g"], T["n"]), T["p"], T["t"],
                                                          T["missing"], pct(T["missing"], T["n"])))
    alias = [(zh, e["game_name"]) for zh, e in names["characters"].items() if e.get("game_name")]
    if alias:
        w("Aliases: " + ", ".join("%s = %s (game spelling)" % a for a in alias) + ".\n")

    w("### Unverified names\n")
    w("| category | name | why | possible match (unverified) | bare dictionary entry (not used) |")
    w("|---|---|---|---|---|")
    for cat, d in names.items():
        if cat == "meta":
            continue
        for zh, e in d.items():
            if e.get("en"):
                continue
            pm = e.get("possible_match")
            if isinstance(pm, list):
                pm = ", ".join(x["name"] for x in pm)
            elif isinstance(pm, dict):
                pm = pm.get("name")
            do = e.get("dictionary_only")
            w("| %s | %s | %s | %s | %s |" % (cat, zh, esc(e.get("note")), pm or "—",
                                             ("%s (%s)" % (do["en"], ",".join(map(str, do["text_ids"]))))
                                             if do else "—"))
    w("")

    # ---- glossary -------------------------------------------------------------------
    gc = Counter(e.get("source") or "unverified" for e in gloss["terms"].values())
    n = len(gloss["terms"])
    w("## Glossary (`data/glossary.json`)\n")
    w("%d terms: from the game dictionary (exact Chinese match) %d (%s), translated by us %d (%s), "
      "unverified (wiki typos / garbled values, `en: null`) %d.\n"
      % (n, gc["game_db"], pct(gc["game_db"], n), gc["translated"], pct(gc["translated"], n), gc["unverified"]))
    by_cat = defaultdict(Counter)
    for e in gloss["terms"].values():
        by_cat[e["category"]][e.get("source") or "unverified"] += 1
    w("| category | game_db | translated | unverified |")
    w("|---|---|---|---|")
    for cat, c in sorted(by_cat.items(), key=lambda kv: -sum(kv[1].values())):
        w("| %s | %d | %d | %d |" % (cat, c["game_db"], c["translated"], c["unverified"]))
    w("")
    unv = [(t, e) for t, e in gloss["terms"].items() if not e.get("en")]
    if unv:
        w("Unverified terms: " + "; ".join("%s (%s%s)" % (t, e.get("note", ""), ", possible match " +
                                                        e["possible_match"] if e.get("possible_match") else "")
                                          for t, e in unv) + ".\n")

    # ---- strings by source ----------------------------------------------------------
    src = Counter()
    missing = Counter()
    missing_rows = []
    for kind, r in records():
        i = r.get("i18n") or {}
        src.update(i.get("sources") or {})
        for m in i.get("missing") or []:
            missing[m["reason"].split(":")[0]] += 1
            missing_rows.append((i.get("name_zh"), m))
    total = sum(src.values()) + sum(missing.values())
    w("## Strings of data/en by source\n")
    w("| source | strings | share |")
    w("|---|---|---|")
    labels = {"game_db": "official English text of the game (values filled from the wiki, numbers checked)",
              "names": "names.json (official names)", "glossary": "glossary.json (terms, stat lines)",
              "derived": "mechanical (dates, scaling parts)", "translated": "our translation of the wiki text",
              "lore": "lore — kept in Chinese, not translated"}
    for k in ("game_db", "names", "glossary", "derived", "translated", "lore"):
        w("| %s | %d | %s |" % (labels[k], src[k], pct(src[k], total)))
    w("| empty (`null`, listed in `i18n.missing`) | %d | %s |\n" % (sum(missing.values()),
                                                                 pct(sum(missing.values()), total)))
    han_left = 0
    import re as _re
    skip = {"i18n", "item_ids", "unlinked", "placeholders_nulled", "parse_notes", "page_title", "name_zh",
            "character_zh", "lore", "affection", "skill_zh", "slot_zh", "quality_zh", "game", "used_in", "source"}

    def _walk(o, top_skip=()):
        n = 0
        if isinstance(o, dict):
            for k, v in o.items():
                if k not in skip and k not in top_skip:
                    n += _walk(v)
        elif isinstance(o, list):
            n += sum(_walk(v) for v in o)
        elif isinstance(o, str) and _re.search(r"[㐀-鿿]", o):
            n += 1
        return n
    for kind, r in records():
        # gear/relic `description` is flavour text (lore), kept in Chinese on purpose
        han_left += _walk(r, ("description",) if kind in ("gear", "relics") else ())
    w("English strings that still contain a Chinese name: %d.\n" % han_left)
    uo, uo_strings = [], set()
    for n_rec, (kind, r) in enumerate(records()):
        for u in (r.get("i18n") or {}).get("unofficial_names") or []:
            uo.append(u)
            uo_strings.add((n_rec, u["path"]))
    w("Unofficial names (step 4): names that have no official English and used to stay in Chinese inside "
      "English strings are translated by meaning in `translate/manual/unofficial_names.json` (people and "
      "places romanized, wiki typos translated as written) and listed per record in "
      "`i18n.unofficial_names`: %d replacements of %d distinct names in %d strings.\n"
      % (len(uo), len({u["zh"] for u in uo}), len(uo_strings)))
    if missing:
        w("Empty strings by reason: " + ", ".join("%s %d" % kv for kv in missing.most_common()) + ".\n")

    # ---- game-only gear -------------------------------------------------------------
    gear = jload(os.path.join(EN, "gear.json"))
    go = [g for g in gear["items"] if g.get("source") == "game_db"]
    links = 0
    for p in glob.glob(os.path.join(EN, "characters", "*.json")):
        for b in jload(p).get("builds") or []:
            links += sum(1 for v in (b.get("item_ids") or {}).values() if v and v.startswith("gear-game-"))
    w("## Items that exist only in the game\n")
    w("%d items named in wiki builds have no wiki page; they are in `data/en/gear.json` with "
      "`source: \"game_db\"` (id `gear-game-<game id>`), linked from %d build entries (`builds[].item_ids`). "
      "With slot: %d, with a fixed quality in the game table: %d, with a skill text: %d "
      "(skill English withheld because the game's English has other numbers than its Chinese: %d).\n"
      % (len(go), links, sum(1 for g in go if g.get("slot")), sum(1 for g in go if g.get("quality")),
         sum(1 for g in go if g.get("skill")),
         sum(1 for g in go if g.get("skill_zh") and not g.get("skill"))))
    w(gear.get("game_only_note", "") + "\n")

    # ---- numbers --------------------------------------------------------------------
    chk = check_numbers.check()
    w("## Number check (`translate/check_numbers.py`, also `tests/test_translate.py`)\n")
    w("String pairs compared: %d. Number/percent mismatches zh ↔ en: **%d**. "
      "(English `null` is not compared: %d.)\n" % (chk["pairs"], len(chk["errors"]), chk["missing"]))
    for e in chk["errors"][:50]:
        w("- `%s`: %s" % (e["path"], esc(json.dumps(e, ensure_ascii=False))))
    if chk["errors"]:
        w("")

    rej_p = os.path.join(ROOT, "translate", "work", "rejected_game_texts.json")
    if os.path.exists(rej_p):
        rej = jload(rej_p)["items"]
        w("### Wiki vs game: texts of the same skill/effect that differ\n")
        w("The game has a text for this very skill / blood rank / item / relic / faction, but it is not the "
          "wiki text with values filled in, so the wiki text was translated. Stricter than «numbers equal»: a "
          "different wording also counts (e.g. wiki 提升 *increase* vs game 下降 *decrease* with the same 10%). "
          "Punctuation and doubled characters are ignored.\n")
        c = Counter((x["kind"], x["reason"]) for x in rej)
        w("| kind | numbers differ | wording differs |")
        w("|---|---|---|")
        for k in sorted({k for k, _ in c}):
            w("| %s | %d | %d |" % (k, c[(k, "numbers differ")], c[(k, "wording differs")]))
        w("")
        nd = [x for x in rej if x["reason"] == "numbers differ"]
        w("Same wording, different numbers (%d) — numbers as written; the game's `{n}` values are filled per "
          "level and not shown:\n" % len(nd))
        w("| record | field | wiki numbers | game literal numbers |")
        w("|---|---|---|---|")
        seen = set()
        for x in nd:
            key = (x["record"], x["path"])
            if key in seen:
                continue
            seen.add(key)
            w("| %s | %s | %s | %s |" % (x["record"], x["path"], " ".join(x["wiki_numbers"]),
                                         " ".join(x["game_numbers"]) or "—"))
        w("")

    # ---- missing list (compact) -----------------------------------------------------
    if missing_rows:
        w("## Empty English strings\n")
        w("Per record in `i18n.missing`. Summary by field:\n")
        by_path = Counter()
        for rec, m in missing_rows:
            p = m["path"].split("[")[0].split(".")[0]
            by_path[(p, m["reason"].split(":")[0])] += 1
        w("| field | reason | count |")
        w("|---|---|---|")
        for (p, r), n_ in by_path.most_common():
            w("| %s | %s | %d |" % (p, r, n_))
        w("")

    # ---- examples -------------------------------------------------------------------
    w("## Examples for review\n")
    zh_by_name = {jload(p)["name"]: jload(p) for p in glob.glob(os.path.join(ZH, "characters", "*.json"))}
    en_by_id = {os.path.splitext(os.path.basename(p))[0]: jload(p) for p in glob.glob(os.path.join(EN, "characters", "*.json"))}
    for nm in EXAMPLES:
        z = zh_by_name.get(nm)
        if not z:
            continue
        e = en_by_id[z["id"]]
        ts = (e["i18n"].get("text_sources") or {})
        w("### %s → %s\n" % (nm, e["name"]))
        w("Real name: %s → %s. Element: %s → %s. Factions: %s.\n" % (
            z["profile"]["real_name"], e["profile"]["real_name"], z["element"], e["element"],
            ", ".join("%s → %s" % (a["name"], b["name"]) for a, b in
                      zip([z["factions"]["base"]] + (z["factions"]["others"] or []),
                          [e["factions"]["base"]] + (e["factions"]["others"] or [])) if a)))
        w("| skill | zh | en | source |")
        w("|---|---|---|---|")
        for i, (a, b) in enumerate(zip(z.get("skills") or [], e.get("skills") or [])):
            s = ts.get("skills[%d].description" % i, {})
            w("| %s → %s | %s | %s | %s |" % (a["name"], b["name"] or "*null*", esc(a["description"]),
                                             esc(b["description"]) if b["description"] else "*null*",
                                             (s.get("source", "") + (" #%s %s" % (s["text_id"], s.get("match", ""))
                                                                     if s.get("text_id") else ""))))
        w("")
        if z.get("blood_ranks"):
            w("| blood rank | zh | en | source |")
            w("|---|---|---|---|")
            for i, (a, b) in enumerate(zip(z["blood_ranks"]["ranks"], e["blood_ranks"]["ranks"])):
                s = ts.get("blood_ranks.ranks[%d]" % i, {})
                w("| %d | %s | %s | %s |" % (a["rank"], esc(a["text"]), esc(b["text"]) if b["text"] else "*null*",
                                            s.get("source", "") + (" #%s" % s["text_id"] if s.get("text_id") else "")))
            w("")
        for a, b in list(zip(z.get("builds") or [], e.get("builds") or []))[:2]:
            w("Build «%s» → «%s»: %s\n" % (a["level_tier"], b["level_tier"], "; ".join(
                "%s: %s → %s" % (ks, vz, ve if ve else "null") for (ks, vz), (ke, ve) in zip(a["slots"].items(), b["slots"].items())
                if vz)))
        if z.get("note"):
            w("Note: %s → %s\n" % (esc(z["note"]), esc(e["note"])))
        if z.get("affix_recommendations", {}).get("primary"):
            w("Affix recommendations: %s → %s\n" % ("、".join(z["affix_recommendations"]["primary"]),
                                                    "; ".join(x or "null" for x in e["affix_recommendations"]["primary"])))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    return OUT


if __name__ == "__main__":
    print(build())
