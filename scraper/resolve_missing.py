"""Step 2b: look up build items / runes that step 2 could not link.

Reads the unlinked names from data/zh (characters/*.json), asks the wiki
  1. action=query&titles=…&redirects=1   (50 titles per request)
  2. list=search for every name still missing
and stores the answers in data/raw/missing_lookup.json. Pages found in step 1
(exact title or redirect) are downloaded like step 1b — wikitext into
data/raw/extra_items/, SMW into data/raw/smw/extra_items/ — and recorded in
manifest.json. Search hits are only candidates: they are stored, not downloaded.

Usage:  python scraper/resolve_missing.py      (from the yog-guide folder)
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch  # noqa: E402

ROOT = fetch.ROOT
ZH = ROOT / "data" / "zh"
OUT = fetch.RAW / "missing_lookup.json"
GROUP = "extra_items"
EXTRA_RUNES = ["逐日", "锻钢", "铁荆"]   # options of 断钢/逐日, 锻钢/绝刃 and the support rune 铁荆


def split_variants(name: str) -> list[str]:
    """A full-width comma separates alternatives (祭仪羽冠，界卫魔面)."""
    return [p.strip() for p in name.split("，") if p.strip()]


def unlinked_names() -> dict[str, list[str]]:
    """{lookup name: [where it is used]}"""
    out: dict[str, list[str]] = {}
    for f in sorted(glob.glob(str(ZH / "characters" / "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        for b in c.get("builds") or []:
            for name, gid in b["item_ids"].items():
                if gid is None:
                    for v in split_variants(name):
                        out.setdefault(v, []).append(f"{c['page_title']} / {b['level_tier']}")
        for key in ("main", "support"):
            for r in ((c.get("runes") or {}).get(key) or []):
                for n in ([o["name"] for o in r["options"] if not o["id"]] if r.get("options") else
                          ([r["name"]] if not r["id"] else [])):
                    out.setdefault(n, []).append(f"{c['page_title']} / 推荐符文.{key}")
    for n in EXTRA_RUNES:
        out.setdefault(n, [])
    return out


def query_titles(api: fetch.Api, names: list[str]) -> dict[str, dict]:
    res: dict[str, dict] = {}
    for i in range(0, len(names), fetch.BATCH):
        part = names[i:i + fetch.BATCH]
        alias = {t: t for t in part}
        pages: dict[str, dict] = {}
        redirects: dict[str, str] = {}
        for chunk in api.query_all(titles="|".join(part), redirects=1, prop="info|categories", cllimit="max"):
            q = chunk.get("query", {})
            for r in q.get("redirects", []):
                redirects[r["from"]] = r["to"]
            fetch._resolve(alias, q)
            for p in q.get("pages", []):
                rec = pages.setdefault(p["title"], {"title": p["title"], "pageid": p.get("pageid"), "ns": p.get("ns"),
                                                    "missing": bool(p.get("missing") or p.get("invalid")),
                                                    "revid": p.get("lastrevid"), "categories": []})
                rec["categories"] += [c["title"] for c in p.get("categories", [])]
        for req, real in alias.items():
            p = pages.get(real)
            res[req] = {
                "found": bool(p and not p["missing"]),
                "title": real if p and not p["missing"] else None,
                "redirected_from": req if (p and not p["missing"] and real != req) else None,
                "redirect_chain": {k: v for k, v in redirects.items() if k == req} or None,
                "pageid": p["pageid"] if p else None,
                "revid": p["revid"] if p else None,
                "categories": sorted(set(p["categories"])) if p else [],
            }
    return res


def search(api: fetch.Api, name: str) -> list[dict]:
    data = api.get(action="query", list="search", srsearch=name, srnamespace=0, srlimit=10,
                   srprop="size|wordcount|timestamp")
    return [{"title": h["title"], "pageid": h.get("pageid"), "size": h.get("size"), "timestamp": h.get("timestamp")}
            for h in data.get("query", {}).get("search", [])]


def main() -> int:
    names_where = unlinked_names()
    names = sorted(names_where)
    fetch.log(f"{len(names)} names to look up")
    api = fetch.Api()
    q = query_titles(api, names)
    result = {}
    for n in names:
        rec = {"used_in": names_where[n], "query": q.get(n), "search": None, "searched_at": None}
        if not (rec["query"] and rec["query"]["found"]):
            rec["search"] = search(api, n)
            rec["searched_at"] = fetch.now_iso()
        result[n] = rec
    found = sorted({r["query"]["title"] for r in result.values() if r["query"] and r["query"]["found"]})
    fetch.log(f"found by title/redirect: {len(found)}; searching done for {sum(1 for r in result.values() if r['search'] is not None)}")

    man = fetch.load_manifest()
    if found:
        fetch.download_group(api, man, GROUP, found, force=False,
                             extra={"in_category_装备": None, "found_via": "resolve_missing.py title/redirect lookup"})
        fetch.download_smw(api, man, GROUP, force=False)
    fetch.write_json(OUT, {
        "generated_at": fetch.now_iso(),
        "api": fetch.API,
        "method": "action=query&titles=…&redirects=1&prop=info|categories (batches of 50), then list=search (srnamespace=0) for names not found",
        "license": "CC BY-NC-SA 4.0, source: BWIKI bookofyog",
        "requests": api.requests,
        "names": result,
    })
    fetch.log(f"wrote {OUT.relative_to(ROOT)} ({api.requests} requests)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
