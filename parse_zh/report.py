"""Writes data/zh/REPORT.md for step 2."""
from __future__ import annotations

import collections


def _esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def write(path, R, chars, gear, relics, runes, stones, factions, tiers, empty_fields, unknown_templates=None):
    L = []
    a = L.append
    a("# Step 2 report — data/raw → data/zh (Chinese, not translated)\n")
    a("Source: BWIKI 依盖之书 <https://wiki.biligame.com/bookofyog/>, CC BY-NC-SA 4.0. "
      "Every record carries `source_url`, `revid` and `permalink` of the page it was read from.\n")
    a("Regenerate: `python parse_zh/build.py`; check: `python -m unittest discover -s tests -v`.\n")

    a("## Output\n")
    a("| file | records | built from |")
    a("|---|---|---|")
    a(f"| characters/*.json | {len(chars)} | wikitext of Category:黑卫 pages (mwparserfromhell) |")
    a(f"| gear.json | {len(gear)} | SMW `browsebysubject` of Category:装备 |")
    a(f"| relics.json | {len(relics)} | SMW of Category:遗物 (+ `介绍` from wikitext, the template does not store it) |")
    a(f"| runes.json | {len(runes)} | SMW of Category:符文 (+ colour names of `边` from wikitext) |")
    a(f"| black_stones.json | {len(stones)} | tabs of page 黑石 + texts of 模板:推荐黑石 |")
    a(f"| factions.json | {len(factions)} | Category:阵线 pages (name/type) + tabs of page 阵线 (thresholds) |")
    a(f"| tiers.json | {len(tiers)} | PVE节奏榜, PVP节奏榜 (every character × 2 modes) |")
    a("")

    a("## Conventions\n")
    a("- Missing data is `null`; nothing is filled in from elsewhere.")
    a("- Wiki placeholder text (`立绘1`, `事迹1`, `角色故事`, `2级好感度问题`, `10级好感度答案1` …) → `null`; "
      "the replaced fields are listed per character in `placeholders_nulled`.")
    a("- The values `无` (none) and `暂无` (not yet) → `null`.")
    a("- Markup is removed: `{{颜色|红|x}}` → `x`, links → their text, `<br>`/`<p>` → newline, file links dropped.")
    a("- Lists written with `、` become arrays; skill lists written with `；` become arrays.")
    a("- `builds[].slots[slot]` = first item of the slot (shown in the centre of the wiki table); "
      "the following ones are in `alternatives[slot]` (the wiki shows the second one beside it). "
      "`item_ids` maps every item name of the build to a `gear.json` id or `null`.")
    a("- `builds[].level_tier` is the tab label exactly as written on the page (it is not always a level, e.g. `蹲`, `血包`).")
    a("- `skills[].scaling` lists only «percent + stat» pairs literally present in the text "
      "(stats: 法术强度, 物理强度, 物理&法术强度, 攻击力, 最大生命值, 体质).")
    a("- Templates inside `<!-- -->` comments are not rendered by the wiki and are ignored (listed below).")
    a("- Tier `as_of` = date of the tier page revision.")
    a("")

    # ---------------------------------------------------- empty fields
    a("## Characters → empty fields\n")
    a("`null` sections/fields per character. `placeholders` = fields whose only content was wiki placeholder text.\n")
    a("| character | rarity | empty | placeholders → null |")
    a("|---|---|---|---|")
    cnt = collections.Counter()
    for c in sorted(chars, key=lambda c: c["page_title"]):
        ef = empty_fields(c)
        cnt.update(ef)
        a(f"| {c['page_title']} | {c.get('rarity') or ''} | {', '.join(ef) or '—'} | {', '.join(c.get('placeholders_nulled') or []) or '—'} |")
    a("")
    a("Totals (characters with the field empty): " + ", ".join(f"{k} {v}" for k, v in cnt.most_common()) + "\n")

    empty_builds = [(c["page_title"], b["level_tier"]) for c in chars for b in (c.get("builds") or []) if b["empty"]]
    partial = []
    for c in chars:
        for b in c.get("builds") or []:
            if not b["empty"]:
                miss = [s for s, v in b["slots"].items() if v is None]
                if miss:
                    partial.append(f"{c['page_title']} «{b['level_tier']}»: {', '.join(miss)}")
    a("### Builds with no items at all\n")
    a("\n".join(f"- {t} «{lt}»" for t, lt in empty_builds) or "- none")
    a("")
    a("### Builds with empty slots\n")
    a("\n".join(f"- {p}" for p in partial) or "- none")
    a("")

    notes = [(c["page_title"], n) for c in chars for n in (c.get("parse_notes") or [])]
    if notes:
        a("### Per-character notes\n")
        for t, n in notes:
            a(f"- {t}: {n}")
        a("")

    # ---------------------------------------------------- links
    REASON = {
        "game_only": "no wiki page; exists in the game DB",
        "typo_candidate": "probably a typo — candidate below (unverified)",
        "not_an_item": "not an item name",
        "nowhere": "found nowhere (wiki, game DB)",
    }
    a("## Links of build items and recommended runes\n")
    a("Lookup order for a name not in the category downloads: wiki `action=query&titles=…&redirects` "
      "(50 per request) → wiki `list=search` → game DB (`template/*.xml`, `language/json`) by exact Chinese name → "
      "similar existing names (difflib, only as `possible_match`, status `unverified`, never linked). "
      "A full-width comma `，` inside a slot value is treated as a separator of variants. "
      "Raw answers: `data/raw/missing_lookup.json` (written by `scraper/resolve_missing.py`).\n")
    lc, rc = R.link_count, R.rune_count
    a("| | before (category pages only) | after (+ pages found by lookup) |")
    a("|---|---|---|")
    a(f"| build item names linked | {lc['before']['linked']} / {lc['before']['total']} | {lc['after']['linked']} / {lc['after']['total']} |")
    a(f"| distinct unlinked build item names | {len(R.unlinked_before)} | {len(R.unlinked_items)} |")
    in_game = sum(1 for i in R.resolved.values() if i["kind"] == "gear" and i["game_id"])
    a(f"| …of the unlinked build item names: found in the game DB (game_id recorded) | — | {in_game} |")
    a(f"| recommended rune names linked | {rc['before']['linked']} / {rc['before']['total']} | {rc['after']['linked']} / {rc['after']['total']} |")
    a("")
    a("«before» = step 2: names exactly as written on the pages, only the category pages of step 1. "
      "«after» = names split on `，` + pages found by the lookup. Totals differ because a split name counts twice.\n")
    if R.extra_pages:
        a("### Wiki pages found by the lookup and downloaded (`data/raw/extra_items`)\n")
        a("| page | used as | requested as |")
        a("|---|---|---|")
        for t, k, frm in sorted(R.extra_pages, key=lambda x: x[0]):
            a(f"| {_esc(t)} | {_esc(k)} | {_esc(frm or t)} |")
        a("")
    a("### Still unlinked, with reasons\n")
    if R.resolved:
        a("| name | kind | reason | possible match (unverified) | game DB ids | wiki search hits | used in |")
        a("|---|---|---|---|---|---|---|")
        where = {**{n: w for n, w in R.unlinked_runes.items()}, **{n: w for n, w in R.unlinked_items.items()}}
        for n, info in sorted(R.resolved.items(), key=lambda kv: (kv[1]["reason"], kv[0])):
            pm = info["possible_match"]
            pm_s = f"{pm['name']} ({pm['id'] or 'no id'}; {pm['source']})" if pm else "—"
            g = info["game"]
            g_s = "; ".join(f"{r['table']}#{r['game_id']}" + (f" text {r['text_id']}" if r['text_id'] else "")
                            for r in (g["refs"] or [])) if g else "—"
            if g and not g["refs"] and g["text_ids"]:
                g_s = "text " + ", ".join(map(str, g["text_ids"]))
            wl = info["wiki_lookup"]
            w_s = ", ".join(wl["search_hits"][:3]) if wl and wl["search_hits"] else "—"
            used = where.get(n, [])
            used_s = "; ".join(used[:4]) + (f" (+{len(used) - 4})" if len(used) > 4 else "")
            reason = REASON[info["reason"]]
            if info["reason"] == "game_only" and info["wiki_lookup"] and info["wiki_lookup"]["title_found"]:
                reason = "wiki page exists but is empty; exists in the game DB"
            a(f"| {_esc(n)} | {info['kind']} | {reason} | {_esc(pm_s)} | {_esc(g_s or '—')} | {_esc(w_s)} | {_esc(used_s)} |")
        a("")
        cnt = collections.Counter(i["reason"] for i in R.resolved.values())
        a("Totals: " + ", ".join(f"{REASON[k]}: {v}" for k, v in cnt.most_common()) + "\n")
    else:
        a("- none\n")
    if R.gamedb:
        a(f"Game DB used: `{R.gamedb['path']}` ({R.gamedb['dictionary_entries']} text entries, "
          f"{R.gamedb['item_names']} item names in equipment/rune/heirloom/blackStone tables). "
          "Only ids are written to data/zh; see `docs/GAMEDB.md`.\n")

    # ---------------------------------------------------- tiers of builds
    kinds = collections.Counter(b.get("tier_kind") for c in chars for b in (c.get("builds") or []))
    specials = collections.Counter((b["level_tier"], b.get("tier_note")) for c in chars for b in (c.get("builds") or [])
                                   if b.get("tier_kind") == "special")
    a("## Build tab labels (`tier_kind`)\n")
    a(f"- level: {kinds.get('level', 0)}, special: {kinds.get('special', 0)}")
    for (lab, note), n in sorted(specials.items()):
        a(f"- special «{lab}» ×{n}: {note or 'no explanation (null)'}")
    a("")
    if R.normalized_links:
        a("Linked only after normalisation:\n")
        for n, g in sorted(set(R.normalized_links)):
            a(f"- {n} → {g}")
        a("")
    if R.slot_mismatch:
        a("Linked item whose `部位` differs from the build slot:\n")
        for s in sorted(set(R.slot_mismatch)):
            a(f"- {s}")
        a("")

    a("## Other unresolved links\n")
    fac = {k: v for k, v in R.unlinked_factions.items() if not k.startswith("(")}
    a("- Character factions not in factions.json: " + ("; ".join(f"{n} ({', '.join(w)})" for n, w in sorted(fac.items())) or "none"))
    a("- Factions without threshold effects on page 阵线 (`thresholds: null`): " +
      (", ".join(sorted(R.unlinked_factions.get("(no effects on page 阵线)", []))) or "none"))
    a("- Black stones in character pages not in black_stones.json: " + ("; ".join(sorted(R.unlinked_stones)) or "none"))
    a("- Relics whose `黑卫名称` is not a downloaded character: " + ("; ".join(R.relic_owner_missing) or "none"))
    a("")

    # ---------------------------------------------------- problems
    a("## Pages / parts that did not parse cleanly\n")
    if R.unparsed:
        a("| page | problem |")
        a("|---|---|")
        for p, m in R.unparsed:
            a(f"| {_esc(p)} | {_esc(m)} |")
    else:
        a("- none")
    a("")
    a("### Unknown templates left as raw text inside values\n")
    a("\n".join(f"- {k} ×{v}" for k, v in sorted((unknown_templates or {}).items())) or "- none")
    a("")
    a("### Templates ignored because they are commented out\n")
    a("\n".join(f"- {p}: {n}" for p, n in R.ignored_comments) or "- none")
    a("")

    if R.notes:
        a("## Source discrepancies and remarks\n")
        for n in R.notes:
            a(f"- {n}")
        a("")

    ranked = collections.Counter((t["mode"], t["tier"] == "not_ranked") for t in tiers)
    a("## Tier lists\n")
    for mode in ("PVE", "PVP"):
        a(f"- {mode}: ranked {ranked[(mode, False)]}, not_ranked {ranked[(mode, True)]}")
    a("")

    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
