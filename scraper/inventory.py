"""Inventory of what the downloaded raw data contains (no parsing of values).

Scans character wikitext for direct template calls {{Name|param=...}} and
lists template names and parameter names. Values are NOT interpreted;
they are only shown truncated as examples.

Writes data/raw/inventory.json and data/raw/REPORT.md.
Usage:  python scraper/inventory.py
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SAMPLES = ["飞焰铃舞", "千宵月守"]


def template_calls(text: str) -> list[tuple[str, list[str]]]:
    """Return [(template_name, [raw params])] for top-level and nested {{...}} calls.

    Skips {{{param}}} placeholders and parser functions ({{#if:...}}).
    Pipes inside [[links]] or nested braces do not split parameters.
    """
    out: list[tuple[str, list[str]]] = []
    stack: list[int] = []
    i, n = 0, len(text)
    while i < n:
        if text.startswith("{{{", i):
            # triple brace placeholder: skip to matching }}}
            j = text.find("}}}", i + 3)
            i = n if j < 0 else j + 3
            continue
        if text.startswith("{{", i):
            stack.append(i)
            i += 2
            continue
        if text.startswith("}}", i) and stack:
            start = stack.pop()
            body = text[start + 2:i]
            parts = split_params(body)
            name = parts[0].strip()
            if name and not name.startswith("#") and ":" not in name.split("|")[0][:1]:
                out.append((name.replace("_", " "), parts[1:]))
            i += 2
            continue
        i += 1
    return out


def split_params(body: str) -> list[str]:
    parts, depth_b, depth_l, cur = [], 0, 0, []
    i = 0
    while i < len(body):
        two = body[i:i + 2]
        if two == "{{":
            depth_b += 1; cur.append(two); i += 2; continue
        if two == "}}" and depth_b:
            depth_b -= 1; cur.append(two); i += 2; continue
        if two == "[[":
            depth_l += 1; cur.append(two); i += 2; continue
        if two == "]]" and depth_l:
            depth_l -= 1; cur.append(two); i += 2; continue
        if body[i] == "|" and not depth_b and not depth_l:
            parts.append("".join(cur)); cur = []; i += 1; continue
        cur.append(body[i]); i += 1
    parts.append("".join(cur))
    return parts


def param_name(p: str, idx: int) -> str:
    if "=" in p:
        k = p.split("=", 1)[0].strip()
        if k and "{{" not in k and "[[" not in k and "\n" not in k:
            return k
    return f"#{idx}"  # positional


def param_names(params: list[str]) -> list[str]:
    """Names for each param; unnamed ones get MediaWiki positional numbers #1, #2..."""
    out, pos = [], 0
    for p in params:
        nm = param_name(p, 0)
        if nm.startswith("#"):
            pos += 1
            nm = f"#{pos}"
        out.append(nm)
    return out


def short(s: str, n: int = 60) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + "…"


CONTENT_GROUPS = ("characters", "pages", "templates", "gear", "relics", "runes",
                  "factions", "black_stones")
GROUP_SOURCE = {
    "characters": "Category:黑卫", "gear": "Category:装备", "relics": "Category:遗物",
    "runes": "Category:符文", "factions": "Category:阵线",
    "black_stones": "黑石, 黑石强化, 模板:推荐黑石 (no 黑石 category exists)",
    "pages": "fixed list", "templates": "used by character pages",
    "rendered": "action=parse",
}
SMW_LABEL = {"characters": "character", "gear": "gear item (装备)", "relics": "relic (遗物)",
             "runes": "rune (符文)", "factions": "faction (阵线)", "black_stones": "黑石 pages"}
# SMW DataItem type ids (SMW\DataItem::TYPE_*)
SMW_TYPES = {1: "number", 2: "text", 4: "boolean", 5: "uri", 6: "time", 7: "geo",
             8: "container", 9: "page", 10: "concept", 11: "property", 12: "error"}


def smw_props(resp: dict) -> tuple[list[dict], int]:
    q = resp.get("query", {})
    props = [p for p in q.get("data", []) if not p["property"].startswith("_")]
    return props, len(q.get("sobj", []) or [])


def smw_section() -> list[str]:
    L = ["", "## Semantic MediaWiki properties (action=browsebysubject)", "",
         "System properties (`_CDAT`, `_MDAT`, `_SKEY`, `_INST`, `_ASK`, …) are omitted. "
         "Type = SMW data item type. Sample = the page of the group with the most properties.", ""]
    for group, label in SMW_LABEL.items():
        files = sorted((RAW / "smw" / group).glob("*.json"))
        if not files:
            L += [f"### {label}", "", "- no SMW files", ""]
            continue
        freq = Counter()
        best = None
        for f in files:
            r = json.loads(f.read_text(encoding="utf-8"))
            props, nsobj = smw_props(r["response"])
            freq.update(p["property"] for p in props)
            if best is None or len(props) > len(best[1]):
                best = (r, props, nsobj)
        r, props, nsobj = best
        L += [f"### {label} — {len(files)} subjects, {len(freq)} distinct properties", ""]
        if not freq:
            L += ["- no user-defined properties on any page of this group", ""]
            continue
        L.append("All properties (pages having it): " + ", ".join(f"{k} ({v})" for k, v in freq.most_common()))
        L += ["", f"Sample **{r['subject']}** (page rev {r['page_revid']}, {r['source_url']}), "
              f"subobjects: {nsobj}", "", "| property | type | value |", "|---|---|---|"]
        for p in props:
            items = p["dataitem"]
            typ = ", ".join(sorted({SMW_TYPES.get(d["type"], str(d["type"])) for d in items}))
            val = " ‖ ".join(str(d["item"]) for d in items)
            L.append(f"| {p['property']} | {typ} | {short(val, 90).replace('|', '¦')} |")
        L.append("")
    return L


def completeness_section() -> list[str]:
    path = RAW / "completeness.json"
    if not path.exists():
        return ["", "## Completeness check", "", "- not run"]
    c = json.loads(path.read_text(encoding="utf-8"))
    d = c["diff"]
    L = ["", "## Completeness check (首页 tiles, PVE/PVP节奏榜 vs Category:黑卫)", "",
         f"- Category:黑卫: {c['category_count']}",
         f"- 首页 tiles: {c['home']['tile_count']} tiles, {c['home']['unique_links']} distinct links "
         f"(tiles are generated by `{c['home']['tile_rule']}`)"]
    for p, t in c["tier_lists"].items():
        L.append(f"- {p} (rev {t['revid']}): {len(t['links'])} distinct character links")

    def lst(xs):
        return ", ".join(xs) if xs else "none"

    L += ["", "**Linked but not in Category:黑卫**", "",
          f"- 首页: {lst(d['on_home_not_in_category'])}"]
    for p in c["tier_lists"]:
        L.append(f"- {p}: {lst(d[f'in_{p}_not_in_category'])}")
    for t, r in c["unknown_titles"].items():
        L.append(f"  - {t}: {r['status']}" + (f" → {r['target']}" if r.get("target") else ""))
    L.append(f"- downloaded as extra characters: {lst(c['extra_character_titles'])}")
    L += ["", "**Icon file name ≠ link target**", ""]
    mism = [(p, m) for p, t in c["tier_lists"].items() for m in t["icon_link_mismatch"]]
    mism += [("首页", {"file": m["icon_file"], "link": m["link"]}) for m in c["home"]["icon_link_mismatch"]]
    L += [f"- {p}: `{m['file']}` → {m['link']}" for p, m in mism] or ["- none"]
    for p, t in c["tier_lists"].items():
        if t["icons_without_link"]:
            L.append(f"- {p}: icons without link=: {lst(t['icons_without_link'])}")
        if t["plain_links"]:
            L.append(f"- {p}: other [[links]] on the page: {lst(t['plain_links'])}")
    if c["home"]["red_link_tiles"]:
        L.append("- 首页 red-link tiles: " + lst([str(x["link"]) for x in c["home"]["red_link_tiles"]]))
    L += ["", "**In Category:黑卫 but not linked**", "",
          f"- not on 首页 ({len(d['in_category_not_on_home'])}; 首页 shows only 稀有度 SP/SS): "
          + lst([f"{x['title']} ({'/'.join(x['稀有度']) if x['稀有度'] else '稀有度 null'})"
                 for x in d["in_category_not_on_home"]]),
          f"- SP/SS but still not on 首页: {lst(d['in_category_SP_or_SS_but_not_on_home'])}"]
    for p in c["tier_lists"]:
        L.append(f"- not in {p} ({len(d[f'in_category_not_in_{p}'])}): {lst(d[f'in_category_not_in_{p}'])}")
    return L


def main() -> None:
    man = json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))
    chars = sorted((RAW / "characters").glob("*.json"))
    names_used = Counter()             # template -> number of character pages calling it directly
    params_used: dict[str, Counter] = defaultdict(Counter)
    per_page = {}
    samples = {}
    values: dict[tuple[str, str], Counter] = defaultdict(Counter)   # (tpl, param) -> value counts
    for f in chars:
        rec = json.loads(f.read_text(encoding="utf-8"))
        calls = template_calls(rec["wikitext"])
        seen = set()
        for name, params in calls:
            seen.add(name)
            for nm, p in zip(param_names(params), params):
                params_used[name][nm] += 1
                if not nm.startswith("#"):
                    values[(name, nm)][p.split("=", 1)[1].strip()] += 1
        for name in seen:
            names_used[name] += 1
        per_page[rec["title"]] = {
            "direct_calls": sorted(seen),
            "transcluded": rec.get("templates", []),
            "length": len(rec["wikitext"]),
        }
        if rec["title"] in SAMPLES:
            samples[rec["title"]] = {
                "revid": rec["revid"], "source_url": rec["source_url"],
                "fetched_at": rec["fetched_at"],
                "calls": [{"template": nm,
                           "params": [{"name": nm,
                                       "example": short(p if nm.startswith("#") else p.split("=", 1)[1])}
                                      for nm, p in zip(param_names(ps), ps)]}
                          for nm, ps in calls],
            }

    # params whose value is empty, or one identical non-empty value, on >= 90% of uses
    empty_params, same_value = {}, {}
    for (tpl, nm), cnt in values.items():
        total = sum(cnt.values())
        if total < 5:
            continue
        if cnt.get("", 0) / total >= 0.9:
            empty_params[f"{tpl}.{nm}"] = f"{cnt['']}/{total}"
        top, c = next(((v, c) for v, c in cnt.most_common() if v), (None, 0))
        if top is not None and c / total >= 0.9:
            same_value[f"{tpl}.{nm}"] = {"value": top, "count": f"{c}/{total}"}

    # Semantic MediaWiki queries: data pulled from other pages at render time
    asks = {}
    for f in sorted(RAW.glob("*/*.json")):
        if f.parent.name not in CONTENT_GROUPS:
            continue
        rec = json.loads(f.read_text(encoding="utf-8"))
        q = re.findall(r"\{\{\s*#ask:\s*([^\n|]*)", rec["wikitext"])
        if q:
            asks[rec["title"]] = sorted(set(s.strip() for s in q))
    sparse = {t: p["direct_calls"] for t, p in per_page.items() if len(p["direct_calls"]) < 3}

    inv = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "character_pages": len(chars),
        "sparse_character_pages": sparse,
        "smw_ask_queries": asks,
        "params_mostly_empty": empty_params,
        "params_same_value_everywhere": same_value,
        "templates_called_directly": {k: {"pages": v, "params": dict(params_used[k].most_common())}
                                      for k, v in names_used.most_common()},
        "per_page": per_page,
        "samples": samples,
    }
    (RAW / "inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- REPORT.md ----
    groups = Counter(k.split("/", 1)[0] for k in man["pages"])
    smw_groups = Counter(k.split("/")[1] for k in man.get("smw", {}))
    cats = {}
    for f in (RAW / "categories").glob("*.json"):
        c = json.loads(f.read_text(encoding="utf-8"))
        cats[c["category"]] = len(c["members"])
    L = ["# Step 1 / 1b report — raw data", "",
         f"Generated: {inv['generated_at']}  ",
         f"Source: {man['source']} (license {man['license']})", "",
         "## Downloaded", "",
         "| folder | source | wikitext pages | SMW subjects |", "|---|---|---|---|"]
    for g in sorted(set(groups) | set(smw_groups)):
        src = GROUP_SOURCE.get(g, "")
        if src in cats:
            src += f" ({cats[src]} members)"
        L.append(f"| {g} | {src} | {groups.get(g, 0)} | {smw_groups.get(g, '—')} |")
    L.append(f"| **total** | | {sum(groups.values())} | {sum(smw_groups.values())} |")
    L += ["", "## Not downloaded", ""]
    if man["failed"]:
        for k, v in sorted(man["failed"].items()):
            L.append(f"- `{k}` — {v['reason']}")
    else:
        L.append("- none")
    for cat, other in (man.get("category_non_articles") or {}).items():
        if other:
            L.append(f"- {cat}: members outside main namespace (skipped on purpose): " + ", ".join(other))
    L += smw_section()
    L += completeness_section()
    L += ["", f"## Templates called directly in character pages ({len(chars)} pages)", "",
          "| template | pages | parameters (count) |", "|---|---|---|"]
    for k, v in names_used.most_common():
        ps = ", ".join(f"{p} ({c})" for p, c in params_used[k].most_common(25))
        more = "" if len(params_used[k]) <= 25 else f", … +{len(params_used[k]) - 25}"
        L.append(f"| {k} | {v} | {ps}{more} |")
    L += ["", "## Findings that matter for the next steps", "",
          "### Data pulled from other pages via `#ask` (Semantic MediaWiki)", "",
          "This content is NOT in the downloaded wikitext; it lives on the queried pages.", ""]
    L += [f"- {t}: " + "; ".join(f"`{q}`" for q in qs) for t, qs in asks.items()] or ["- none"]
    L += ["", "### Sparse character pages (fewer than 3 templates)", ""]
    L += [f"- {t}: only " + ", ".join(c) for t, c in sparse.items()] or ["- none"]
    L += ["", "### Parameters with the same non-empty value on ≥90% of uses", "",
          "Not judged automatically: some are wiki placeholder text (e.g. «立绘1», "
          "«10级好感度答案1»), others are genuinely shared values (gender, 神格 costs).", ""]
    L += [f"- `{k}` = «{v['value'][:40]}» ({v['count']})" for k, v in sorted(same_value.items())] or ["- none"]
    L += ["", "### Parameters empty on ≥90% of uses", ""]
    L += [f"- `{k}` ({v})" for k, v in sorted(empty_params.items())] or ["- none"]
    for t in SAMPLES:
        s = samples.get(t)
        L += ["", f"## Sample: {t}", ""]
        if not s:
            L.append("not downloaded")
            continue
        L.append(f"rev {s['revid']}, {s['source_url']}  ")
        L.append("Transcluded (incl. indirect): " + ", ".join(per_page[t]["transcluded"]))
        L.append("")
        for c in s["calls"]:
            ps = "; ".join(f"`{p['name']}`=" + p["example"] for p in c["params"]) or "(no params)"
            L.append(f"- **{c['template']}**: {ps}")
    (RAW / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"inventory: {len(chars)} character pages, {len(names_used)} templates called directly")


if __name__ == "__main__":
    main()
