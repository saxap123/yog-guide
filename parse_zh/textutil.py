"""Wikitext / SMW value helpers: markup -> plain text, list splitting,
placeholder detection, skill scaling extraction.

Nothing here guesses data: unknown markup is kept as text and reported.
"""
from __future__ import annotations

import html
import re
import unicodedata

import mwparserfromhell as mwp
from mwparserfromhell.nodes import Argument, Comment, ExternalLink, HTMLEntity, Tag, Template, Text, Wikilink

# templates whose rendered output is (part of) their arguments
_PASS_ARG = {
    "颜色": "2",        # {{颜色|红|text}} -> text
    "阵线图标": "1",    # {{阵线图标|秘术|22px}} -> 秘术
    "符文图标": "1",
    "黑石图标": "1",
    "等级Tab": "1",
}
_DROP = {"空白占位符", "JS", "ResourceLoader"}

# every template seen while cleaning that is not handled above
UNKNOWN_TEMPLATES: dict[str, int] = {}


def _tpl_name(t: Template) -> str:
    return str(t.name).strip()


def _arg(t: Template, key: str) -> str | None:
    if t.has(key):
        return str(t.get(key).value)
    return None


def _render(nodes) -> str:
    out = []
    for n in nodes:
        if isinstance(n, Text):
            out.append(str(n.value))
        elif isinstance(n, Comment):
            continue
        elif isinstance(n, HTMLEntity):
            out.append(n.normalize())
        elif isinstance(n, Wikilink):
            title = str(n.title).strip()
            if title.lower().startswith(("file:", "文件:", "image:", "图像:")):
                continue
            out.append(_render(n.text.nodes) if n.text is not None else title)
        elif isinstance(n, ExternalLink):
            out.append(_render(n.title.nodes) if n.title is not None else str(n.url))
        elif isinstance(n, Tag):
            tag = str(n.tag).lower()
            if tag == "br":
                out.append("\n")
            elif tag in ("ref",):
                continue
            elif n.contents is not None:
                inner = _render(n.contents.nodes)
                out.append(inner + ("\n" if tag in ("p", "div", "li") else ""))
        elif isinstance(n, Template):
            name = _tpl_name(n)
            if name in _DROP:
                continue
            if name in _PASS_ARG:
                key = _PASS_ARG[name]
                v = _arg(n, key)
                if v is None and key == "2":
                    v = _arg(n, "1")
                out.append(_render(mwp.parse(v).nodes) if v else "")
            elif name == "消耗品icon":
                out.append(f"{(_arg(n, '1') or '').strip()}{(_arg(n, '2') or '').strip()}")
            else:
                UNKNOWN_TEMPLATES[name] = UNKNOWN_TEMPLATES.get(name, 0) + 1
                out.append(str(n))
        elif isinstance(n, Argument):
            out.append(str(n))
        else:
            out.append(str(n))
    return "".join(out)


def clean(value) -> str | None:
    """Wikitext or SMW-expanded HTML -> plain text. Empty -> None."""
    if value is None:
        return None
    s = str(value)
    # SMW stores pipes inside links as the broken bar
    s = s.replace("¦", "|")
    text = _render(mwp.parse(s).nodes)
    text = html.unescape(text).replace(" ", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.strip()
    return text or None


# "无" = none, "暂无" = not yet available: both mean "no data" for the record.
NONE_VALUES = {"无", "暂无"}


def clean_or_none(value) -> str | None:
    t = clean(value)
    if t is None or t in NONE_VALUES:
        return None
    return t


def split_list(value, sep: str = "、") -> list[str] | None:
    t = clean_or_none(value)
    if t is None:
        return None
    parts = [p.strip() for p in t.split(sep)]
    parts = [p for p in parts if p]
    return parts or None


# wiki placeholder text left in the page templates
_PLACEHOLDER_RES = [
    re.compile(r"^立绘\d+$"),
    re.compile(r"^事迹[0-9一二三四五六七八九十]+$"),
    re.compile(r"^角色故事$"),
    re.compile(r"^\d+级好感度(问题|答案)\d*$"),
]


def is_placeholder(text: str | None) -> bool:
    if text is None:
        return False
    return any(r.match(text) for r in _PLACEHOLDER_RES)


def real_or_none(value) -> tuple[str | None, bool]:
    """(cleaned text or None, was_placeholder)."""
    t = clean(value)
    if is_placeholder(t):
        return None, True
    return t, False


# ---------------------------------------------------------------- scaling
_NUM = r"\d+(?:\.\d+)?%"
_PCT = rf"\(?{_NUM}(?:\s*[-~/]\s*{_NUM})*\)?"
_STATS = [
    "物理&法术强度", "法术&物理强度", "物理与法术强度", "法术与物理强度",
    "法术强度", "物理强度", "攻击力", "最大生命值", "体质",
]
_EFFECT = r"(?:火焰|冰霜|闪电|雷电|黑暗|神圣|物理|混沌|绝对)?伤害|生命值|生命|护盾|治疗"
SCALING_RE = re.compile(
    rf"(?P<pct>{_PCT})\s*\*?\s*(?:的)?(?:自身)?(?P<stat>{'|'.join(map(re.escape, _STATS))})"
    rf"(?:的?(?P<effect>{_EFFECT}))?"
)


def extract_scaling(text: str | None) -> list[dict]:
    """Pairs 'percent + stat' written in the skill text, e.g. 500%法术强度的火焰伤害."""
    if not text:
        return []
    out = []
    for m in SCALING_RE.finditer(text):
        pct = m.group("pct")
        values = [float(v) for v in re.findall(r"\d+(?:\.\d+)?(?=%)", pct)]
        out.append({
            "percent": pct.strip("()"),
            "values": values,
            "stat": m.group("stat"),
            "effect": m.group("effect"),
            "text": m.group(0),
        })
    return out


# ---------------------------------------------------------------- names
_DOTS = "・•‧∙⋅·"


def normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKC", name)
    for d in _DOTS:
        s = s.replace(d, "·")
    return re.sub(r"\s+", "", s)


def safe_filename(title: str) -> str:
    return re.sub(r'[<>:"/\\|?*]', "_", title)
