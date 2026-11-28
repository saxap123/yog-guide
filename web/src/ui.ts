import { at, type Origin, type Rec } from "./data.ts";
import images from "./generated/images.json";

export const esc = (s: unknown) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

const tipAttr = (text: string) => `data-tip="${esc(text)}" tabindex="0"`;

export const ORIGIN_LABEL: Record<Origin, string> = { o: "official", t: "translated", w: "wiki" };
export const ORIGIN_TIP: Record<Origin, string> = {
  o: "Official English from the game files or publisher announcements.",
  t: "Translated: our translation of the BWIKI text (no official English for it).",
  w: "Wiki: BWIKI data as written or rendered mechanically (numbers, levels, dates, scaling).",
};

export function originOf(rec: Rec, paths: string[]): Origin {
  let best: Origin = "w";
  for (const p of paths) {
    const o = rec._a.src[p] ?? "w";
    if (o === "t") return "t";
    if (o === "o") best = "o";
  }
  return best;
}

/** Source badge for a row made of one or more string paths. */
export function badge(rec: Rec, paths: string | string[]): string {
  const o = originOf(rec, Array.isArray(paths) ? paths : [paths]);
  return `<span class="src src-${o}" ${tipAttr(ORIGIN_TIP[o])}>${ORIGIN_LABEL[o]}</span>`;
}

export const badgeOf = (o: Origin) => `<span class="src src-${o}" ${tipAttr(ORIGIN_TIP[o])}>${ORIGIN_LABEL[o]}</span>`;

/** "Game vs wiki numbers differ" mark for a path (empty string when there is none). */
export function discMark(rec: Rec, path: string): string {
  const d = rec._a.disc[path];
  if (!d) return "";
  const game = d.game.length ? d.game.join(" ") : "—";
  const tip =
    `Game and wiki differ in numbers. The game text of this effect (game files 2026-09-22, text #${d.text_id}) ` +
    `has the same wording with other numbers; the wiki text is shown. ` +
    `Wiki numbers: ${d.wiki.join(" ")}. Game literal numbers: ${game} (the game's per-level values are not shown).`;
  return `<span class="disc" ${tipAttr(tip)}>≠ game</span>`;
}

export function noData(rec: Rec | null, path: string | null, extra?: string): string {
  const m = rec && path ? rec._a.miss[path] : undefined;
  const parts: string[] = [];
  if (m) parts.push(`Chinese on the wiki: ${m.zh}`, `Why: ${m.reason}`);
  if (extra) parts.push(extra);
  const tip = parts.length ? ` ${tipAttr(parts.join(" · "))}` : "";
  return `<span class="nodata"${tip}>No data yet</span>`;
}

/** Text of a string with its unofficial names marked (Chinese in the tooltip). */
export function richText(rec: Rec, path: string, s: string): string {
  const uo = rec._a.uo[path];
  if (!uo?.length) return esc(s);
  let out = "";
  let cur = 0;
  for (const u of uo) {
    const i = s.indexOf(u.en, cur);
    if (i < 0) continue;
    out += esc(s.slice(cur, i));
    const tip = `Unofficial name (our translation) · Chinese: ${u.zh}${u.note ? " · " + u.note : ""}`;
    out += `<span class="uo" ${tipAttr(tip)}>${esc(u.en)}<sup class="uo-tag">unofficial name</sup></span>`;
    cur = i + u.en.length;
  }
  return out + esc(s.slice(cur));
}

/** Value at path, rendered: text (+unofficial marks, +discrepancy), or "No data yet". */
export function val(rec: Rec, path: string, opts: { badge?: boolean; nl?: boolean } = {}): string {
  const v = at(rec, path);
  if (v === null || v === undefined || v === "") return noData(rec, path);
  let html = typeof v === "string" ? richText(rec, path, v) : esc(v);
  if (opts.nl) html = html.replace(/\r?\n/g, "<br>");
  html += discMark(rec, path);
  if (opts.badge) html += " " + badge(rec, path);
  return html;
}

export const has = (v: unknown) => !(v === null || v === undefined || v === "" || (Array.isArray(v) && !v.length));

/** Wiki link of a record (exact revision). */
export function wikiLink(rec: Rec, label = "Wiki page"): string {
  if (!rec.permalink && !rec.source_url) return "";
  const rev = rec.revid ? ` (rev ${rec.revid})` : "";
  return `<a class="ext" href="${esc(rec.permalink ?? rec.source_url)}" target="_blank" rel="noopener">${esc(label)}${rev}</a>`;
}

export function nameHtml(rec: Rec | undefined | null, href?: string, path = "name"): string {
  if (!rec) return noData(null, null);
  const n = rec.name ? richText(rec, path, rec.name) : noData(rec, path);
  return href ? `<a href="${href}">${n}</a>` : n;
}

export const zh = (s: string | null | undefined) => (s ? `<span class="zh" lang="zh">${esc(s)}</span>` : "");

// ---- tooltip (one floating element, mouse + keyboard + tap) --------------------------------
export function initTooltip() {
  const tip = document.getElementById("tip")!;
  let owner: HTMLElement | null = null;
  const show = (el: HTMLElement) => {
    owner = el;
    tip.textContent = el.dataset.tip ?? "";
    tip.hidden = false;
    const r = el.getBoundingClientRect();
    const tw = Math.min(360, window.innerWidth - 16);
    tip.style.maxWidth = `${tw}px`;
    const left = Math.max(8, Math.min(r.left, window.innerWidth - tip.offsetWidth - 8));
    let top = r.bottom + 6;
    if (top + tip.offsetHeight > window.innerHeight - 8) top = r.top - tip.offsetHeight - 6;
    tip.style.left = `${left + window.scrollX}px`;
    tip.style.top = `${top + window.scrollY}px`;
  };
  const hide = () => {
    owner = null;
    tip.hidden = true;
  };
  const find = (e: Event) => (e.target as HTMLElement | null)?.closest?.("[data-tip]") as HTMLElement | null;
  document.addEventListener("mouseover", (e) => {
    const el = find(e);
    if (el) show(el);
    else if (owner) hide();
  });
  document.addEventListener("focusin", (e) => {
    const el = find(e);
    if (el) show(el);
  });
  document.addEventListener("focusout", hide);
  document.addEventListener("click", (e) => {
    const el = find(e);
    if (el && el !== owner) show(el);
    else if (!el) hide();
  });
  document.addEventListener("keydown", (e) => e.key === "Escape" && hide());
  window.addEventListener("hashchange", hide);
}

export const ELEMENT_CLASS: Record<string, string> = {
  Fire: "el-fire", Frost: "el-frost", Lightning: "el-lightning", Physical: "el-physical", Light: "el-light", Dark: "el-dark",
};

export function tierChip(tier: string | undefined): string {
  if (!tier || tier === "not_ranked") return `<span class="tier tier-nr">Not ranked yet</span>`;
  return `<span class="tier tier-${esc(tier.toLowerCase().replaceAll(".", "-"))}">${esc(tier)}</span>`;
}

// ---- images (step 4b): generated manifest, placeholders when an image is missing ------------
interface ImageManifest {
  mode: "icons" | "full" | "none";
  avatars: Record<string, string>;
  portraits: Record<string, string>;
  icons: Record<string, string>;
  /** runes shown with the game's generic rune stone icon (no icon of their own in the game files) */
  shared?: Record<string, string>;
  frames?: Record<string, { plate: string; border: string }>;
}
export const IMG = images as unknown as ImageManifest;

/** Game quality frame (plate + border from 01.title) as inline CSS variables, if the build has it. */
function frameStyle(q: string | null | undefined): string {
  const f = q ? IMG.frames?.[q] : undefined;
  if (!f) return "";
  // url() inside a custom property resolves against the stylesheet (assets/), so pass absolute URLs
  const abs = (p: string) => new URL(p, document.baseURI).href;
  return ` style="--plate:url('${esc(abs(f.plate))}');--border:url('${esc(abs(f.border))}')"`;
}

/** Frame colour per quality: the colours the game's own texts use for these quality names
 *  (<color=#…> around 神话 / 永恒 / 史诗 / 传说); 太古 (Archaic) has no colour in the game texts. */
const QUALITY_CLASS: Record<string, string> = {
  Mythic: "q-mythic", Eternal: "q-eternal", Epic: "q-epic", Legend: "q-legend", Archaic: "q-archaic",
};
export const qualityClass = (q: string | null | undefined) => (q && QUALITY_CLASS[q]) || "q-none";

const initial = (rec: Rec | undefined | null) => {
  const s = (rec?.name || rec?.name_zh || "?").trim();
  return [...s][0]?.toUpperCase() ?? "?";
};

/** Character avatar (sizes: sm 40, md 56, lg 144) or a placeholder with the first letter of the name. */
export function avatar(c: Rec | undefined | null, size: "sm" | "md" | "lg" = "sm"): string {
  const src = c?.id ? IMG.avatars[c.id] : undefined;
  if (src) return `<span class="ava ava-${size}"><img src="${esc(src)}" alt="" loading="lazy" decoding="async"></span>`;
  return `<span class="ava ava-${size} ava-ph" aria-hidden="true">${esc(initial(c))}</span>`;
}

/** Full portrait (IMAGES=full only); falls back to the large avatar. */
export function portrait(c: Rec): string {
  const src = c.id ? IMG.portraits[c.id] : undefined;
  return src ? `<span class="portrait"><img src="${esc(src)}" alt="" decoding="async"></span>` : avatar(c, "lg");
}

/** Item icon with a quality frame; without an icon: a placeholder with the item's slot (or kind). */
export function itemIcon(rec: Rec | undefined | null, fallbackLabel: string, size: "sm" | "md" | "lg" = "sm"): string {
  const fs = frameStyle(rec?.quality);
  const q = fs ? "ico-f" : qualityClass(rec?.quality);
  const src = rec?.id ? IMG.icons[rec.id] : undefined;
  if (src && rec?.id && IMG.shared?.[rec.id]) {
    // generic rune stone icon: caption with the rune's name so the identical icons stay distinguishable
    const name = rec.name ?? rec.name_zh ?? "";
    return `<span class="ico ico-${size} ${q} ico-shared"${fs} ${tipAttr(`${name}: shared rune icon (the game files have no icon of its own for this rune)`)}>` +
      `<img src="${esc(src)}" alt="" loading="lazy" decoding="async"><span class="ico-cap">${esc(name)}</span></span>`;
  }
  if (src) return `<span class="ico ico-${size} ${q}"${fs}><img src="${esc(src)}" alt="" loading="lazy" decoding="async"></span>`;
  const label = rec?.slot ?? fallbackLabel;
  return `<span class="ico ico-${size} ${q} ico-ph"${fs} aria-hidden="true"><span>${esc(label)}</span></span>`;
}
