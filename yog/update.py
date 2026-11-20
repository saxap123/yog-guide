"""`python -m yog update` — refresh the guide from the wiki in one command (step 5).

  1. fetch        scraper/fetch.py: only pages whose revid changed (or new pages) are downloaded
  2. lookup       scraper/resolve_missing.py (step 2b), only when something changed
  3. parse        scraper/inventory.py, parse_zh/build.py  -> data/zh
  4. translate    translate/build_names.py, build_glossary.py, build_en.py -> data/en
                  Translations are keyed by the Chinese text, so everything already translated is
                  reused; only new / changed strings end up in translate/work/todo.json (not translated
                  automatically: add them to translate/manual/texts/, check with check_chunk.py, re-run
                  with --offline).
  5. check        translate/check_numbers.py (any zh/en number mismatch stops the update)
  6. report       translate/write_report.py -> data/en/REPORT.md
  7. tests        python -m unittest discover -s tests
  8. site         npm run build in web/ (IMAGES=icons)            [skipped with --no-build]
  9. deploy       npm run deploy in web/ -> branch gh-pages        [only with --deploy]

Afterwards: new names without English in data/names.json are listed, and data/CHANGELOG.md gets an
entry (records added / changed / removed, PvE tier changes, wiki pages with a new revid).

The "before" state is kept in translate/work/update_baseline.json until an update finishes, so an
update that stopped (failed check, missing translations) and is re-run with --offline still reports
everything against the last finished update.

Options:
  --offline   no network: skip steps 1–2 (use data/raw as it is)
  --rebuild   continue even when no wiki page has a new revid
  --no-build  stop after the tests (no site build)
  --deploy    publish web/dist to GitHub Pages after the build
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EN = DATA / "en"
MANIFEST = DATA / "raw" / "manifest.json"
NAMES = DATA / "names.json"
CHANGELOG = DATA / "CHANGELOG.md"
TODO = ROOT / "translate" / "work" / "todo.json"
BASELINE = ROOT / "translate" / "work" / "update_baseline.json"
WEB = ROOT / "web"

# provenance / bookkeeping fields: a change there alone is a new revision, not a data change
VOLATILE = {"fetched_at", "revid", "permalink", "rev_timestamp", "smw_api_request", "i18n",
            "template_revid", "effects_revid"}
COLLECTIONS = {"gear": "gear", "relics": "relic", "runes": "rune", "black_stones": "black stone",
               "factions": "faction"}
NAME_CATS = ["characters", "skills", "gear", "relics", "runes", "black_stones", "factions"]


def env() -> dict:
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    e["PYTHONUTF8"] = "1"
    return e


def jload(p: Path):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def h(v) -> str:
    return hashlib.sha1(json.dumps(v, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


# ---- snapshot of the data --------------------------------------------------------------------
def records() -> dict[str, dict]:
    """key -> {kind, label, fields: {field: hash}, revid} for every record of data/en."""
    out: dict[str, dict] = {}

    def add(key, kind, rec):
        zh = (rec.get("i18n") or {}).get("name_zh") or rec.get("page_title") or rec.get("name_zh")
        name = rec.get("name")
        label = f"{name} ({zh})" if name and zh and name != zh else (name or zh or key)
        out[key] = {"kind": kind, "label": label, "revid": rec.get("revid"),
                    "fields": {k: h(v) for k, v in rec.items() if k not in VOLATILE}}

    if (EN / "characters").is_dir():
        for p in sorted((EN / "characters").glob("*.json")):
            rec = jload(p)
            add(rec["id"], "character", rec)
    for f, kind in COLLECTIONS.items():
        p = EN / f"{f}.json"
        if p.exists():
            for rec in jload(p)["items"]:
                add(rec["id"], kind, rec)
    return out


def tiers() -> dict[str, str]:
    """PvE tier per character (the site shows PvE only)."""
    p = EN / "tiers.json"
    if not p.exists():
        return {}
    out = {}
    for t in jload(p)["items"]:
        if t.get("mode") == "PVE":
            out[f"{t.get('character')} ({t.get('character_zh')})"] = t.get("tier")
    return out


def names() -> dict[str, dict[str, str | None]]:
    if not NAMES.exists():
        return {}
    n = jload(NAMES)
    return {c: {zh: (e or {}).get("en") for zh, e in n.get(c, {}).items()} for c in NAME_CATS}


def revids() -> dict[str, int | None]:
    if not MANIFEST.exists():
        return {}
    return {k: v.get("revid") for k, v in jload(MANIFEST).get("pages", {}).items()}


def snapshot() -> dict:
    todo = jload(TODO).get("texts", {}) if TODO.exists() else {}
    return {"taken_at": now(), "revids": revids(), "records": records(), "tiers": tiers(),
            "names": names(), "todo": sorted(todo)}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ---- running the steps -----------------------------------------------------------------------
class StepFailed(Exception):
    pass


def run(title: str, cmd: list[str] | str, cwd: Path = ROOT, ok=(0,), capture=False, extra_env=None) -> tuple[int, str]:
    print(f"\n=== {title} ===", flush=True)
    e = env()
    if extra_env:
        e.update(extra_env)
    shell = isinstance(cmd, str)
    p = subprocess.Popen(cmd, cwd=cwd, env=e, shell=shell, stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.STDOUT if capture else None, text=True, encoding="utf-8", errors="replace")
    out = []
    if capture:
        for line in p.stdout:  # type: ignore[union-attr]
            sys.stdout.write(line)
            out.append(line)
    code = p.wait()
    if code not in ok:
        raise StepFailed(f"{title}: exit code {code}")
    return code, "".join(out)


def py(script: str) -> list[str]:
    return [sys.executable, str(ROOT / script)]


# ---- comparing ---------------------------------------------------------------------------------
def diff(before: dict, after: dict) -> dict:
    rb, ra = before["records"], after["records"]
    added = [ra[k] for k in ra if k not in rb]
    removed = [rb[k] for k in rb if k not in ra]
    changed, revised = [], []
    for k in ra:
        if k in rb:
            fb, fa = rb[k]["fields"], ra[k]["fields"]
            fields = sorted(f for f in set(fb) | set(fa) if fb.get(f) != fa.get(f))
            if fields:
                changed.append({**ra[k], "changed": fields, "revid_before": rb[k].get("revid")})
            elif ra[k].get("revid") != rb[k].get("revid"):
                revised.append({**ra[k], "revid_before": rb[k].get("revid")})
    tb, ta = before["tiers"], after["tiers"]
    tier_changes = [(c, tb.get(c), ta.get(c)) for c in sorted(set(tb) | set(ta)) if tb.get(c) != ta.get(c)]
    vb, va = before["revids"], after["revids"]
    pages = [(k, vb.get(k), va[k]) for k in sorted(va) if vb.get(k) != va[k]]
    gone_pages = [k for k in sorted(vb) if k not in va]
    nb, na = before["names"], after["names"]
    new_unpaired = [(c, zh) for c in NAME_CATS for zh, en in na.get(c, {}).items()
                    if en is None and (zh not in nb.get(c, {}) or nb[c][zh] is not None)]
    all_unpaired = sum(1 for c in NAME_CATS for en in na.get(c, {}).values() if en is None)
    new_names = [(c, zh, en) for c in NAME_CATS for zh, en in na.get(c, {}).items()
                 if en is not None and zh not in nb.get(c, {})]
    todo_new = [s for s in after["todo"] if s not in set(before["todo"])]
    return {"added": added, "removed": removed, "changed": changed, "revised": revised, "tiers": tier_changes,
            "pages": pages, "gone_pages": gone_pages, "new_unpaired": new_unpaired, "all_unpaired": all_unpaired,
            "new_names": new_names, "todo": after["todo"], "todo_new": todo_new}


def by_kind(items: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for it in sorted(items, key=lambda x: (x["kind"], x["label"])):
        out.setdefault(it["kind"], []).append(it)
    return out


def changelog_entry(d: dict, before: dict, unofficial_missing: dict) -> str:
    L = [f"## {now()[:10]} — update", ""]
    L.append(f"Compared with the data of {before['taken_at'][:10]}. "
             f"Wiki pages with a new revision: {len(d['pages'])}.")
    L.append("")
    if d["added"]:
        L.append("### Added")
        for kind, items in by_kind(d["added"]).items():
            L.append(f"- **{kind}** ({len(items)}): " + "; ".join(i["label"] for i in items))
        L.append("")
    if d["changed"]:
        L.append("### Changed")
        for kind, items in by_kind(d["changed"]).items():
            for i in items:
                rev = f" (revid {i['revid_before']} → {i['revid']})" if i.get("revid") != i.get("revid_before") else ""
                L.append(f"- {kind}: {i['label']} — {', '.join(i['changed'])}{rev}")
        L.append("")
    if d["tiers"]:
        L.append("### PvE tier list")
        for c, a, b in d["tiers"]:
            L.append(f"- {c}: {a or '—'} → {b or '—'}")
        L.append("")
    if d["removed"]:
        L.append("### Removed")
        for kind, items in by_kind(d["removed"]).items():
            L.append(f"- **{kind}** ({len(items)}): " + "; ".join(i["label"] for i in items))
        L.append("")
    if d["revised"]:
        L.append(f"New wiki revision without a data change: {len(d['revised'])} records "
                 f"({'; '.join(i['label'] for i in d['revised'][:20])}{' …' if len(d['revised']) > 20 else ''}).")
        L.append("")
    if d["new_unpaired"] or unofficial_missing:
        L.append("### Names without English")
        if d["new_unpaired"]:
            L.append(f"- new in `data/names.json` with `en: null` ({len(d['new_unpaired'])}): " +
                     "; ".join(f"{zh} ({c})" for c, zh in d["new_unpaired"]))
        if unofficial_missing:
            L.append(f"- left in Chinese inside English strings, not in `translate/manual/unofficial_names.json` "
                     f"({len(unofficial_missing)}): " + "; ".join(unofficial_missing))
        L.append("")
    if d["todo"]:
        L.append(f"Strings waiting for a translation: {len(d['todo'])} (`translate/work/todo.json`); "
                 "they show as «No data yet» on the site.")
        L.append("")
    if not any(d[k] for k in ("added", "changed", "removed", "tiers", "revised")):
        L.append("No data change.")
        L.append("")
    return "\n".join(L)


def write_changelog(entry: str) -> None:
    head = ("# Changelog (data)\n\nWhat changed in `data/en` with each `python -m yog update` "
            "(newest first). Source: BWIKI 依盖之书, CC BY-NC-SA 4.0.\n\n")
    old = CHANGELOG.read_text(encoding="utf-8") if CHANGELOG.exists() else head
    body = old[len(head):] if old.startswith(head) else old
    CHANGELOG.write_text(head + entry.rstrip() + "\n\n" + body.lstrip(), encoding="utf-8")


# ---- main ------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="python -m yog update", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--offline", action="store_true", help="skip the network steps (fetch, lookup)")
    ap.add_argument("--rebuild", action="store_true", help="continue even if no wiki page changed")
    ap.add_argument("--no-build", action="store_true", help="stop after the tests")
    ap.add_argument("--deploy", action="store_true", help="publish web/dist to GitHub Pages after the build")
    a = ap.parse_args(argv)

    if not (DATA / "raw" / "game_db" / "08.database").is_dir():
        print("data/raw/game_db/08.database not found: the translation step needs the local game snapshot.",
              file=sys.stderr)
        return 2

    resumed = BASELINE.exists()
    if resumed:
        before = jload(BASELINE)
        print(f"unfinished update found: comparing with the state of {before['taken_at']}")
    else:
        before = snapshot()
        BASELINE.parent.mkdir(parents=True, exist_ok=True)
        BASELINE.write_text(json.dumps(before, ensure_ascii=False), encoding="utf-8")

    warnings: list[str] = []
    try:
        if not a.offline:
            code, _ = run("1/9 fetch: wiki pages with a new revid", py("scraper/fetch.py"), ok=(0, 1))
            if code == 1:
                warnings.append("some pages failed to download (data/raw/manifest.json → failed); re-run later")
        now_rev = revids()
        changed_pages = [k for k in now_rev if before["revids"].get(k) != now_rev[k]]
        print(f"\nwiki pages with a new revision: {len(changed_pages)}")
        for k in changed_pages[:50]:
            print(f"  {k}: {before['revids'].get(k)} -> {now_rev[k]}")
        if not changed_pages and not a.rebuild and not resumed:
            BASELINE.unlink(missing_ok=True)
            print("nothing new on the wiki; data and site left as they are (use --rebuild to rebuild anyway)")
            return 1 if warnings else 0
        if changed_pages and not a.offline:
            run("2/9 lookup of unlinked build items (step 2b)", py("scraper/resolve_missing.py"))
        run("3/9 parse: inventory", py("scraper/inventory.py"))
        run("3/9 parse: data/raw -> data/zh", py("parse_zh/build.py"))
        run("4/9 translate: names", py("translate/build_names.py"))
        run("4/9 translate: glossary", py("translate/build_glossary.py"))
        _, out = run("4/9 translate: data/en (existing translations reused)", py("translate/build_en.py"), capture=True)
        unofficial_missing: dict = {}
        m = re.search(r"names left in Chinese \(add them to translate/manual/unofficial_names\.json\): (\{.*\})", out)
        if m:
            try:
                unofficial_missing = ast.literal_eval(m.group(1))
            except (ValueError, SyntaxError):
                pass
        run("5/9 check numbers", py("translate/check_numbers.py"))
        run("6/9 report", py("translate/write_report.py"))
        run("7/9 tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"])

        after = snapshot()
        d = diff(before, after)
        write_changelog(changelog_entry(d, before, unofficial_missing))
        BASELINE.unlink(missing_ok=True)

        if not a.no_build:
            run("8/9 site build (IMAGES=icons)", "npm run build", cwd=WEB, extra_env={"IMAGES": "icons"})
        if a.deploy:
            if a.no_build:
                raise StepFailed("--deploy needs the site build (drop --no-build)")
            run("9/9 deploy to GitHub Pages", "npm run deploy", cwd=WEB)
    except StepFailed as e:
        print(f"\nupdate stopped: {e}", file=sys.stderr)
        print("fix the problem and re-run (add --offline to skip downloading again); "
              "the changelog will compare with the last finished update.", file=sys.stderr)
        return 1

    # ---- summary --------------------------------------------------------------------------------
    print("\n=== summary ===")
    print(f"records added {len(d['added'])}, changed {len(d['changed'])}, removed {len(d['removed'])}, "
          f"PvE tier changes {len(d['tiers'])}  -> data/CHANGELOG.md")
    if d["new_unpaired"]:
        print(f"\nnew names without a pair in data/names.json ({len(d['new_unpaired'])}; "
              f"all names without English: {d['all_unpaired']}):")
        for c, zh in d["new_unpaired"]:
            print(f"  {c}: {zh}")
    else:
        print(f"no new names without English (all names without English: {d['all_unpaired']})")
    if unofficial_missing:
        print("\nnames left in Chinese in English strings (add to translate/manual/unofficial_names.json):")
        for zh, n in unofficial_missing.items():
            print(f"  {zh} ×{n}")
    if d["todo"]:
        print(f"\nstrings to translate: {len(d['todo'])} ({len(d['todo_new'])} new) in translate/work/todo.json —"
              " add them to translate/manual/texts/, check with translate/check_chunk.py,"
              " then: python -m yog update --offline --rebuild")
    for w in warnings:
        print(f"warning: {w}")
    if not a.no_build:
        print("\nsite built: web/dist" + ("" if a.deploy else "  (publish: python -m yog update --deploy, or npm run deploy in web/)"))
    return 1 if warnings else 0
