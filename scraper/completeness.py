"""Completeness check: is every character linked from 首页 and the tier lists in Category:黑卫?

Sources (all already in data/raw):
  - categories/黑卫.json          Category:黑卫 members
  - rendered/首页.json            rendered HTML of the main page (tiles come from an SMW #ask,
                                  so the wikitext alone has no names)
  - pages/PVE节奏榜.json, PVP节奏榜.json   hand-written [[file:Xicon.png|link=X]] lists
  - smw/characters/*.json         only for the 稀有度 value, to explain who is not on 首页

Only link targets and icon file names are read; nothing else is interpreted.
Writes data/raw/completeness.json. Called by fetch.py; can be run alone
(it then makes a few API requests to check that unknown titles exist).
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = RAW / "completeness.json"
TIER_PAGES = ["PVE节奏榜", "PVP节奏榜"]

_FILE_LINK = re.compile(r"\[\[\s*(?:file|File|文件|图像|Image|image)\s*:\s*([^|\]]+?)\s*\|([^\]]*)\]\]")
_PLAIN_LINK = re.compile(r"\[\[(?!\s*(?:file|File|文件|图像|Image|image|分类|Category)\s*:)([^|\]]+)(?:\|[^\]]*)?\]\]")
_TILE = re.compile(r'<div data-param1="[^"]*"[^>]*>(.*?)</div>', re.S)
_A = re.compile(r'<a\s[^>]*?title="([^"]+)"[^>]*>(.*?)</a>', re.S)
_ALT = re.compile(r'alt="([^"]+)"')


def norm(t: str) -> str:
    t = html.unescape(t).replace("_", " ").strip()
    return t[:1].upper() + t[1:] if t else t


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def icon_name(fname: str) -> str | None:
    f = fname.strip()
    return f[:-len("icon.png")].strip() if f.lower().endswith("icon.png") else None


def tier_links(wikitext: str) -> tuple[list[dict], list[str]]:
    icons = []
    for fname, params in _FILE_LINK.findall(wikitext):
        link = None
        for p in params.split("|"):
            if p.strip().startswith("link="):
                link = p.strip()[5:].strip()
        icons.append({"file": fname.strip(), "icon_name": icon_name(fname), "link": norm(link) if link else None})
    plain = [norm(x) for x in _PLAIN_LINK.findall(wikitext)]
    return icons, plain


def home_tiles(parse_html: str) -> list[dict]:
    out = []
    for block in _TILE.findall(parse_html):
        a = _A.search(block)
        alt = _ALT.search(block)
        out.append({
            "link": norm(re.sub(r"\s*[（(](?:页面不存在|page does not exist)[)）]$", "", a.group(1)))
                    if a else None,
            "red_link": bool(a and 'class="new"' in a.group(0).split(">", 1)[0]),
            "icon_file": html.unescape(alt.group(1)) if alt else None,
        })
    return out


def run(api=None) -> list[str]:
    """Write completeness.json and return titles to add to the characters group."""
    cat = [m["title"] for m in _load(RAW / "categories" / "黑卫.json")["members"] if m["ns"] == 0]
    catset = set(cat)

    rarity = {}
    for f in (RAW / "smw" / "characters").glob("*.json"):
        r = _load(f)
        for prop in r["response"].get("query", {}).get("data", []):
            if prop["property"] == "稀有度":
                rarity[r["subject"]] = [d["item"] for d in prop["dataitem"]]

    rendered = _load(RAW / "rendered" / "首页.json")
    tiles = home_tiles(rendered["response"]["parse"]["text"])
    home = sorted({t["link"] for t in tiles if t["link"]})

    tiers = {}
    for page in TIER_PAGES:
        rec = _load(RAW / "pages" / f"{page}.json")
        icons, plain = tier_links(rec["wikitext"])
        tiers[page] = {
            "revid": rec["revid"], "source_url": rec["source_url"],
            "links": sorted({i["link"] for i in icons if i["link"]}),
            "icons_without_link": [i["file"] for i in icons if not i["link"]],
            "icon_link_mismatch": [i for i in icons if i["link"] and i["icon_name"]
                                   and norm(i["icon_name"]) != i["link"]],
            "plain_links": sorted(set(plain)),
        }

    mentioned = set(home)
    for t in tiers.values():
        mentioned |= set(t["links"])
    unknown = sorted(mentioned - catset)

    # resolve unknown titles on the wiki (exists? redirect into the category?)
    resolved = {}
    if unknown and api is not None:
        import fetch
        meta = fetch.page_meta(api, unknown)
        for t in unknown:
            m = meta.get(t)
            if m is None or m["missing"]:
                resolved[t] = {"status": "missing on wiki"}
            elif m["title"] != t:
                resolved[t] = {"status": "redirect", "target": m["title"],
                               "target_in_category": m["title"] in catset}
            else:
                resolved[t] = {"status": "exists, not in Category:黑卫", "ns": m["ns"]}
    elif unknown and OUT.exists():
        resolved = _load(OUT).get("unknown_titles", {})

    extra = sorted({t for t, r in resolved.items()
                    if r.get("status") == "exists, not in Category:黑卫" and r.get("ns") == 0}
                   | {r["target"] for r in resolved.values()
                      if r.get("status") == "redirect" and not r.get("target_in_category")})

    not_home = sorted(catset - set(home))
    out = {
        "note": "Only link targets / icon names compared; tier labels are not read.",
        "category_count": len(cat),
        "home": {
            "source_url": rendered["source_url"], "fetched_at": rendered["fetched_at"],
            "tile_count": len(tiles), "unique_links": len(home),
            "tile_rule": "模板:首页黑卫 / 模板:新首页黑卫: #ask [[分类:黑卫]][[稀有度::SP||SS]]",
            "red_link_tiles": [t for t in tiles if t["red_link"]],
            "icon_link_mismatch": [t for t in tiles if t["link"] and t["icon_file"]
                                   and icon_name(t["icon_file"])
                                   and norm(icon_name(t["icon_file"])) != t["link"]],
        },
        "tier_lists": tiers,
        "diff": {
            "on_home_not_in_category": sorted(set(home) - catset),
            **{f"in_{p}_not_in_category": sorted(set(t["links"]) - catset) for p, t in tiers.items()},
            "in_category_not_on_home": [{"title": t, "稀有度": rarity.get(t)} for t in not_home],
            "in_category_SP_or_SS_but_not_on_home": [t for t in not_home
                                                     if set(rarity.get(t) or []) & {"SP", "SS"}],
            **{f"in_category_not_in_{p}": sorted(catset - set(t["links"])) for p, t in tiers.items()},
        },
        "unknown_titles": resolved,
        "extra_character_titles": extra,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"completeness: {len(cat)} in category, {len(home)} on 首页, "
          + ", ".join(f"{p} {len(t['links'])}" for p, t in tiers.items())
          + f", {len(unknown)} not in category, {len(extra)} to download")
    return extra


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fetch
    run(fetch.Api())
