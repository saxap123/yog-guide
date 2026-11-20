"""Match a wiki (Chinese) text against a game dictionary text and fill the English one.

Game texts are templates: `{0}`, `{1}` … (skills, gear, relics) or `*` (factions) stand
for values the game fills in. A wiki text is the same sentence with the values written
out. To reuse the official English we

1. normalise both Chinese strings (NFKC, no whitespace, no final full stop),
2. turn the game template into a regex (placeholder -> capture group),
3. full-match the wiki text and take the captured values (they must look numeric),
4. put the values into the English template,
5. accept only if the Arabic numbers of the wiki text and of the filled English text
   are the same multiset (gamedict.numbers).

Second tier (`lose=True`): the same, on loose() forms — punctuation removed, name brackets
unified, doubled characters collapsed. This accepts wiki texts that differ from the game
text only by punctuation or a typo such as 且且; any other change of wording still fails,
so e.g. 提升 (increase) on the wiki vs 下降 (decrease) in the game is never taken from the game.

A game text without placeholders is accepted when it equals the wiki text after
normalisation (step 5 still applies).
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

from gamedict import numbers

PH_RE = re.compile(r"\{(\d+)\}|\*")
VALUE_RE = re.compile(r"^[\d\.\%\+\-\(\)~～/×xX±\s]*\d[\d\.\%\+\-\(\)~～/×xX±\s]*$")
NUMERIC_RUN = re.compile(r"[\d\.\%\+\-\(\)~/\*\{\}]*(?:\d|\*)[\d\.\%\+\-\(\)~/\*\{\}]*")
LOOSE_DROP = re.compile(r"[，。、；：,.;:!！?？()（）\"“”'‘’…·<>《》]")
DOUBLE_HAN = re.compile(r"([㐀-鿿])\1")
STRAY_BRACES = re.compile(r"\{(?!\d+\})|(?<!\{\d)(?<!\{\d\d)\}")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"\s+", "", s)
    s = s.replace("～", "~").replace("—", "-").replace("–", "-")
    return s.rstrip("。.!！;；,")


def loose(s: str) -> str:
    """norm() + no punctuation, one kind of name brackets, doubled characters collapsed.
    Numeric runs ('82.9%', '(10.00%-20.00%)', '{0}') are kept as they are; stray braces dropped."""
    s = norm(s).replace("[", "【").replace("]", "】").replace("「", "【").replace("」", "】")
    s = STRAY_BRACES.sub("", s)

    def clean(t):
        return DOUBLE_HAN.sub(r"\1", LOOSE_DROP.sub("", t))

    out, pos = [], 0
    for m in NUMERIC_RUN.finditer(s):
        out.append(clean(s[pos:m.start()]))
        out.append(m.group(0))
        pos = m.end()
    out.append(clean(s[pos:]))
    return "".join(out)


def shape(s: str) -> str:
    """Key for candidate lookup: normalised text with every numeric run / placeholder -> '#'."""
    return NUMERIC_RUN.sub("#", norm(s))


def _template_regex(zh_tpl: str, lose: bool = False):
    parts, order, pos = [], [], 0
    t = loose(zh_tpl) if lose else norm(zh_tpl)
    star = 0
    for m in PH_RE.finditer(t):
        parts.append(re.escape(t[pos:m.start()]))
        if m.group(1) is not None:
            key = int(m.group(1))
        else:
            key = ("*", star)
            star += 1
        order.append(key)
        parts.append("(.+?)")
        pos = m.end()
    parts.append(re.escape(t[pos:]))
    return re.compile("".join(parts)), order


def fill(wiki_zh: str, game_zh: str, game_en: str, lose: bool = False) -> dict | None:
    """Return {'en', 'values', 'loose'} if the wiki text is the game text with values filled in."""
    if not (wiki_zh and game_zh and game_en):
        return None
    rx, order = _template_regex(game_zh, lose)
    m = rx.fullmatch(loose(wiki_zh) if lose else norm(wiki_zh))
    if not m:
        return None
    values: dict = {}
    for key, val in zip(order, m.groups()):
        if lose:
            val = val.rstrip(".")
        if not VALUE_RE.match(val):
            return None
        if key in values and values[key] != val:
            return None
        values[key] = val
    star = 0
    missing = False

    def sub(mm):
        nonlocal star, missing
        if mm.group(1) is not None:
            key = int(mm.group(1))
        else:
            key = ("*", star)
            star += 1
        if key not in values:
            missing = True
            return mm.group(0)
        return values[key]

    en = PH_RE.sub(sub, game_en)
    # "{0}%" in the English template + a wiki value that already has its % sign
    en = en.replace("%%", "%")
    if missing:
        return None
    if Counter(numbers(wiki_zh)) != Counter(numbers(en)):
        return None
    return {"en": en, "values": [values[k] for k in order], "loose": lose}


def fill_any(wiki_zh: str, game_zh: str, game_en: str) -> dict | None:
    return fill(wiki_zh, game_zh, game_en) or fill(wiki_zh, game_zh, game_en, lose=True)


class ShapeIndex:
    """shape(zh) / loose shape -> dictionary ids, for texts that are not tied to one table row."""

    def __init__(self, gd):
        self.gd = gd
        self.idx: dict[str, list[int]] = {}
        self.lidx: dict[str, list[int]] = {}
        for tid, e in gd.text.items():
            z = (e.get("zhcn") or "").strip()
            if z and (e.get("en") or "").strip():
                self.idx.setdefault(shape(z), []).append(tid)
                self.lidx.setdefault(NUMERIC_RUN.sub("#", loose(z)), []).append(tid)

    def match(self, wiki_zh: str) -> dict | None:
        """Best verified fill among dictionary texts of the same shape (strict first, then loose).
        Ambiguous (different English results) -> the most frequent result, others listed."""
        for lose, idx, key in ((False, self.idx, shape(wiki_zh)),
                               (True, self.lidx, NUMERIC_RUN.sub("#", loose(wiki_zh)))):
            results = []
            for tid in idx.get(key, []):
                r = fill(wiki_zh, self.gd.zh(tid), self.gd.en(tid), lose)
                if r:
                    results.append((tid, r))
            if not results:
                continue
            counts = Counter(r["en"] for _, r in results)
            best = max(counts, key=lambda s: (counts[s], -min(t for t, r in results if r["en"] == s)))
            tid = min(t for t, r in results if r["en"] == best)
            return {"en": best, "text_id": tid, "loose": lose,
                    "alternatives": sorted(set(counts) - {best}) or None}
        return None
