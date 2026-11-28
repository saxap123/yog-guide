"""Steps 1 and 1b: download raw data from the Book of Yog BWIKI via the MediaWiki API.

Data source: https://wiki.biligame.com/bookofyog/ (CC BY-NC-SA 4.0).

What it does
  1. Lists the categories 黑卫, 装备, 遗物, 符文, 阵线 (paginated by cmcontinue).
  2. Downloads wikitext + revid of every member page, batched 50 per request.
  3. Downloads a fixed list of overview pages and the 黑石 pages (the wiki has
     no 黑石 category; set effects are hard-coded in 黑石 and 模板:推荐黑石).
  4. Downloads every template / module transcluded by the character pages.
  5. Saves the Semantic MediaWiki data of every page (action=browsebysubject).
  6. Saves the rendered HTML of 首页 and runs the completeness check
     (completeness.py); characters found there but missing from Category:黑卫
     are downloaded too and kept on later runs.

Resumable: every finished page is written at once and recorded in
data/raw/manifest.json. A re-run only downloads pages whose current revid
differs from the stored one (or that are not on disk yet). SMW data is
re-fetched when the page revid changed (see docs/DEVELOPMENT.md for the caveat).

No parsing, no translation: the files hold the API answer as-is.

Usage:  python scraper/fetch.py            (from the yog-guide folder)
        python scraper/fetch.py --force    (ignore stored revids)
        python scraper/fetch.py --guides-only    (refresh the guide source cache)
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

API = "https://wiki.biligame.com/bookofyog/api.php"
WIKI_BASE = "https://wiki.biligame.com/bookofyog/"
USER_AGENT = (
    "yog-guide-scraper/0.2 (personal non-commercial offline reference; "
    "python-requests/" + requests.__version__ + ")"
)
# group folder -> category
CATEGORY_GROUPS = {
    "characters": "Category:黑卫",
    "gear": "Category:装备",
    "relics": "Category:遗物",
    "runes": "Category:符文",
    "factions": "Category:阵线",
}
EXTRA_PAGES = [
    "PVE节奏榜", "PVP节奏榜", "装备", "黑石", "符文",
    "遗物", "阵线", "天赋推荐", "黑话解读", "首页",
]
# No Category:黑石 exists. Effects are hard-coded in these pages.
BLACK_STONE_PAGES = ["黑石", "黑石强化", "模板:推荐黑石"]
SMW_GROUPS = ["characters", "gear", "relics", "runes", "factions", "black_stones"]
RENDERED_PAGES = ["首页"]

TIMEOUT = 30
BACKOFF = [2, 4, 8, 16, 32]   # 5 retries after the first attempt
PAUSE = (1.0, 2.0)            # random pause between requests, seconds
BATCH = 50                    # titles per query (API limit for normal users)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.json"
COMPLETENESS = RAW / "completeness.json"
GUIDE_DATA = ROOT / "translate" / "manual" / "guides.json"

_UNSAFE = '<>:"/\\|?*'


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def page_url(title: str) -> str:
    return WIKI_BASE + quote(title.replace(" ", "_"), safe="/:")


def safe_name(title: str) -> str:
    return "".join("_" if c in _UNSAFE or ord(c) < 32 else c for c in title).strip(" .")


def write_json(path: Path, obj) -> None:
    """Atomic write: tmp file + replace, so an interrupt never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def log(msg: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


class RetryableError(Exception):
    pass


class Api:
    def __init__(self, session: requests.Session | None = None) -> None:
        self.s = session or requests.Session()
        self.s.headers["User-Agent"] = USER_AGENT
        self.last = 0.0
        self.requests = 0

    def get(self, **params) -> dict:
        params.update(format="json", formatversion=2, maxlag=5)
        err: Exception | None = None
        for attempt in range(len(BACKOFF) + 1):
            wait = random.uniform(*PAUSE) - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
            try:
                self.requests += 1
                r = self.s.get(API, params=params, timeout=TIMEOUT)
                self.last = time.monotonic()
                if r.status_code in (429, 500, 502, 503, 504):
                    raise RetryableError(f"HTTP {r.status_code}")
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    code = data["error"].get("code")
                    if code in ("maxlag", "ratelimited", "readonly"):
                        raise RetryableError(f"API error {code}")
                    raise RuntimeError(f"API error: {data['error']}")  # not retried
                return data
            except (requests.RequestException, ValueError, RetryableError) as e:
                self.last = time.monotonic()
                err = e
                if attempt < len(BACKOFF):
                    log(f"  retry {attempt + 1}/{len(BACKOFF)} in {BACKOFF[attempt]}s: {e}")
                    time.sleep(BACKOFF[attempt])
        raise RuntimeError(f"gave up after {len(BACKOFF)} retries: {err}")

    def query_all(self, **params) -> list[dict]:
        """Run a query following 'continue' and return every response chunk."""
        out, cont = [], {}
        while True:
            data = self.get(action="query", **params, **cont)
            out.append(data)
            if "continue" not in data:
                return out
            cont = data["continue"]


def load_manifest(path: Path | None = None) -> dict:
    path = path or MANIFEST
    if path.exists():
        with open(path, encoding="utf-8") as f:
            man = json.load(f)
    else:
        man = {"source": WIKI_BASE, "license": "CC BY-NC-SA 4.0", "pages": {}, "failed": {}}
    man.setdefault("smw", {})
    return man


def category_members(api: Api, category: str) -> list[dict]:
    members = []
    for chunk in api.query_all(list="categorymembers", cmtitle=category,
                               cmlimit="max", cmprop="ids|title|type"):
        members += chunk["query"]["categorymembers"]
    return members


def _resolve(alias: dict[str, str], q: dict) -> None:
    for n in q.get("normalized", []) + q.get("redirects", []):
        for k, v in list(alias.items()):
            if v == n["from"]:
                alias[k] = n["to"]


def page_meta(api: Api, titles: list[str]) -> dict[str, dict]:
    """Current revid + transcluded templates for each title (batched).

    Returns {requested_title: {"title", "pageid", "ns", "revid", "missing", "templates"}}.
    """
    result: dict[str, dict] = {}
    for i in range(0, len(titles), BATCH):
        part = titles[i:i + BATCH]
        pages: dict[str, dict] = {}
        alias = {t: t for t in part}
        for chunk in api.query_all(titles="|".join(part), prop="info|templates",
                                   tllimit="max", redirects=1):
            q = chunk.get("query", {})
            _resolve(alias, q)
            for p in q.get("pages", []):
                rec = pages.setdefault(p["title"], {
                    "title": p["title"], "pageid": p.get("pageid"), "ns": p.get("ns"),
                    "revid": None, "missing": False, "templates": [],
                })
                rec["revid"] = rec["revid"] or p.get("lastrevid")
                rec["missing"] = rec["missing"] or bool(p.get("missing") or p.get("invalid"))
                rec["templates"] += [t["title"] for t in p.get("templates", [])]
        for req, real in alias.items():
            if real in pages:
                result[req] = pages[real]
    return result


def fetch_contents(api: Api, titles: list[str]) -> dict[str, dict]:
    """Wikitext of up to BATCH titles per request. Returns {requested_title: content}."""
    result: dict[str, dict] = {}
    for i in range(0, len(titles), BATCH):
        part = titles[i:i + BATCH]
        alias = {t: t for t in part}
        got: dict[str, dict] = {}
        for chunk in api.query_all(titles="|".join(part), prop="revisions",
                                   rvprop="ids|timestamp|content", rvslots="main", redirects=1):
            q = chunk.get("query", {})
            _resolve(alias, q)
            for p in q.get("pages", []):
                if p.get("missing") or not p.get("revisions"):
                    continue
                rev = p["revisions"][0]
                got[p["title"]] = {
                    "title": p["title"], "pageid": p["pageid"], "ns": p["ns"],
                    "revid": rev["revid"], "rev_timestamp": rev["timestamp"],
                    "wikitext": rev["slots"]["main"]["content"],
                }
        for req, real in alias.items():
            if real in got:
                result[req] = {**got[real], "redirected_from": req if real != req else None}
    return result


def _fail(man: dict, key: str, reason: str, manifest_path: Path | None = None) -> None:
    man["failed"][key] = {"reason": reason, "at": now_iso()}
    write_json(manifest_path or MANIFEST, man)


def download_group(api: Api, man: dict, group: str, titles: list[str], force: bool,
                   meta: dict[str, dict] | None = None, extra: dict | None = None, *,
                   manifest_path: Path | None = None) -> dict[str, dict]:
    log(f"[{group}] {len(titles)} titles: checking revids")
    meta = meta if meta is not None else page_meta(api, titles)
    todo = []
    skipped = 0
    for title in titles:
        key = f"{group}/{title}"
        m = meta.get(title)
        if m is None or m["missing"]:
            _fail(man, key, "page missing on wiki", manifest_path)
            log(f"  {title}: MISSING")
            continue
        old = man["pages"].get(key)
        path = RAW / group / (safe_name(title) + ".json")
        if not force and old and old.get("revid") == m["revid"] and path.exists():
            skipped += 1
            man["failed"].pop(key, None)
            continue
        todo.append(title)
    done = 0
    for i in range(0, len(todo), BATCH):
        part = todo[i:i + BATCH]
        try:
            contents = fetch_contents(api, part)
        except Exception as e:  # noqa: BLE001 - record and continue
            for t in part:
                _fail(man, f"{group}/{t}", str(e), manifest_path)
            log(f"  batch of {len(part)} FAILED ({e})")
            continue
        for title in part:
            key = f"{group}/{title}"
            c = contents.get(title)
            if c is None:
                _fail(man, key, "no content returned", manifest_path)
                log(f"  {title}: FAILED (no content returned)")
                continue
            fetched = now_iso()
            rec = {
                **c,
                "group": group,
                "source_url": page_url(c["title"]),
                "permalink": f"{API.replace('api.php', 'index.php')}?oldid={c['revid']}",
                "fetched_at": fetched,
                "templates": sorted(set(meta[title]["templates"])),
                "license": "CC BY-NC-SA 4.0, source: BWIKI bookofyog",
                **(extra or {}),
            }
            path = RAW / group / (safe_name(title) + ".json")
            write_json(path, rec)
            man["pages"][key] = {"title": c["title"], "revid": c["revid"],
                                 "file": path.relative_to(RAW).as_posix(),
                                 "fetched_at": fetched}
            man["failed"].pop(key, None)
            done += 1
        write_json(manifest_path or MANIFEST, man)
        log(f"  [{group}] {min(i + BATCH, len(todo))}/{len(todo)} fetched")
    log(f"[{group}] downloaded {done}, unchanged {skipped}")
    return meta


def download_smw(api: Api, man: dict, group: str, force: bool) -> None:
    """Raw Semantic MediaWiki data (action=browsebysubject) for every page of a group."""
    keys = sorted(k for k in man["pages"] if k.split("/", 1)[0] == group)
    log(f"[smw/{group}] {len(keys)} pages")
    done = skipped = 0
    for key in keys:
        page = man["pages"][key]
        title = page["title"]
        skey = f"smw/{key}"
        path = RAW / "smw" / group / (safe_name(key.split("/", 1)[1]) + ".json")
        old = man["smw"].get(skey)
        if not force and old and old.get("page_revid") == page["revid"] and path.exists():
            skipped += 1
            continue
        try:
            data = api.get(action="browsebysubject", subject=title)
        except Exception as e:  # noqa: BLE001
            _fail(man, skey, str(e))
            log(f"  {title}: SMW FAILED ({e})")
            continue
        fetched = now_iso()
        write_json(path, {
            "subject": title,
            "group": group,
            "page_revid": page["revid"],
            "source_url": page_url(title),
            "api_request": f"{API}?action=browsebysubject&subject={quote(title)}&format=json",
            "fetched_at": fetched,
            "license": "CC BY-NC-SA 4.0, source: BWIKI bookofyog",
            "response": data,
        })
        man["smw"][skey] = {"page_revid": page["revid"], "file": path.relative_to(RAW).as_posix(),
                            "fetched_at": fetched}
        man["failed"].pop(skey, None)
        done += 1
        if done % 25 == 0:
            write_json(MANIFEST, man)
            log(f"  [smw/{group}] {done} fetched")
    write_json(MANIFEST, man)
    log(f"[smw/{group}] downloaded {done}, unchanged {skipped}")


def download_rendered(api: Api, man: dict, title: str) -> None:
    """Rendered HTML (action=parse). SMW query results change without a new revid,
    so this is fetched on every run."""
    key = f"rendered/{title}"
    try:
        data = api.get(action="parse", page=title, prop="text|links|revid")
    except Exception as e:  # noqa: BLE001
        _fail(man, key, str(e))
        return
    fetched = now_iso()
    path = RAW / "rendered" / (safe_name(title) + ".json")
    write_json(path, {"title": title, "source_url": page_url(title), "fetched_at": fetched,
                      "license": "CC BY-NC-SA 4.0, source: BWIKI bookofyog", "response": data})
    man["pages"][key] = {"title": title, "revid": data["parse"].get("revid"),
                         "file": path.relative_to(RAW).as_posix(), "fetched_at": fetched}
    man["failed"].pop(key, None)
    write_json(MANIFEST, man)
    log(f"[rendered] {title}")


def download_guide_sources(api: Api, force: bool) -> int:
    """Download the current wiki revisions and compare them with the reviewed guide sources."""
    with GUIDE_DATA.open(encoding="utf-8") as f:
        sources = json.load(f)["wiki"]
    path = RAW / "guides" / "manifest.json"
    man = load_manifest(path)
    man["run_started"] = now_iso()
    download_group(api, man, "guides", list(sources), force, manifest_path=path)
    changes = []
    for title, reviewed in sources.items():
        key = f"guides/{title}"
        if key in man["failed"]:
            log(f"  {title}: {man['failed'][key]['reason']}")
            continue
        current = man["pages"][key]["revid"]
        if current != reviewed["revid"]:
            changes.append(title)
            log(f"  {title}: reviewed revision {reviewed['revid']}, current revision {current}")
    man["run_finished"] = now_iso()
    man["api_requests_last_run"] = api.requests
    write_json(path, man)
    log(f"Guides: {len(changes)} source revisions to review, {len(man['failed'])} failed")
    return 1 if man["failed"] else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-download everything")
    ap.add_argument("--guides-only", action="store_true", help="refresh sources for the progression guides")
    args = ap.parse_args()

    api = Api()
    if args.guides_only:
        return download_guide_sources(api, args.force)
    man = load_manifest()
    man["run_started"] = now_iso()
    man.setdefault("category_non_articles", {})
    if isinstance(man["category_non_articles"], list):   # format of step 1
        man["category_non_articles"] = {"Category:黑卫": man["category_non_articles"]}

    # 1-2. category groups
    metas: dict[str, dict] = {}
    titles_by_group: dict[str, list[str]] = {}
    for group, cat in CATEGORY_GROUPS.items():
        log(f"listing {cat}")
        members = category_members(api, cat)
        write_json(RAW / "categories" / (safe_name(cat.split(":", 1)[1]) + ".json"), {
            "category": cat, "source_url": page_url(cat),
            "fetched_at": now_iso(), "members": members,
        })
        titles = [m["title"] for m in members if m.get("ns") == 0]
        other = [m["title"] for m in members if m.get("ns") != 0]
        man["category_non_articles"][cat] = other
        log(f"  {len(members)} members, {len(titles)} articles, {len(other)} other (not downloaded)")
        titles_by_group[group] = titles
        metas[group] = download_group(api, man, group, titles, args.force)

    # characters that are linked from 首页 / tier lists but not in Category:黑卫
    extra_chars: list[str] = []
    if COMPLETENESS.exists():
        prev = json.loads(COMPLETENESS.read_text(encoding="utf-8"))
        extra_chars = [t for t in prev.get("extra_character_titles", [])
                       if t not in titles_by_group["characters"]]
    if extra_chars:
        download_group(api, man, "characters", extra_chars, args.force,
                       extra={"in_category_黑卫": False})

    # 3. overview pages, 黑石 sources
    download_group(api, man, "pages", EXTRA_PAGES, args.force)
    download_group(api, man, "black_stones", BLACK_STONE_PAGES, args.force)

    # 4. templates/modules used by character pages
    usage: dict[str, list[str]] = {}
    for t, m in metas["characters"].items():
        for tpl in m.get("templates", []):
            usage.setdefault(tpl, []).append(t)
    write_json(RAW / "template_usage.json", {
        "note": "templates/modules transcluded by character pages (from prop=templates)",
        "fetched_at": now_iso(),
        "usage": {k: sorted(v) for k, v in sorted(usage.items())},
    })
    download_group(api, man, "templates", sorted(usage), args.force)

    # 5. SMW data
    for group in SMW_GROUPS:
        download_smw(api, man, group, args.force)

    # 6. rendered main page + completeness check
    for t in RENDERED_PAGES:
        download_rendered(api, man, t)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import completeness  # same folder
    found = completeness.run(api)
    new = [t for t in found if t not in titles_by_group["characters"] and t not in extra_chars]
    if new:
        log(f"completeness: {len(new)} characters outside Category:黑卫 -> downloading")
        download_group(api, man, "characters", new, args.force, extra={"in_category_黑卫": False})
        download_smw(api, man, "characters", args.force)
        completeness.run(api)

    man["run_finished"] = now_iso()
    man["api_requests_last_run"] = api.requests
    write_json(MANIFEST, man)
    log(f"done: {len(man['pages'])} pages, {len(man['smw'])} SMW subjects on disk, "
        f"{len(man['failed'])} failed, {api.requests} API requests")
    return 0 if not man["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
