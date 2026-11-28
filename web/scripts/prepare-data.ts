/**
 * Build-time data step: ../data/en (+ data/zh, names.json, glossary.json, translate/manual) ->
 * src/generated/data.json, which the site imports (embedded in the bundle, no fetches at runtime).
 *
 * For every English string it records where the text comes from:
 *   o  official   - English of the game files (official name, game text, glossary term from the game)
 *   t  translated - our translation of the wiki text (translate/manual), translated glossary term,
 *                   or a string with an unofficial name (translate/manual/unofficial_names.json)
 *   w  wiki       - wiki data as written or rendered mechanically (numbers, dates, levels, scaling)
 * Absent from the map = "w". Paths use the English keys: "skills[2].description", "builds[0].slots.Weapon".
 *
 * Also: i18n.missing (empty English) -> per path reason, i18n.unofficial_names -> per path names,
 * data/en/discrepancies.json (game vs wiki numbers) -> per path numbers.
 * Nothing is invented here: values are copied from data/en; only provenance is attached.
 */
import fs from "node:fs";
import path from "node:path";
import { prepareGuides } from "./prepare-guides.ts";

type O = "o" | "t" | "w";
type J = any; // eslint-disable-line @typescript-eslint/no-explicit-any

const ROOT = path.resolve(import.meta.dirname, "..", "..");
const EN = path.join(ROOT, "data", "en");
const ZH = path.join(ROOT, "data", "zh");
const OUT = path.join(import.meta.dirname, "..", "src", "generated", "data.json");
const HAN = /[㐀-鿿]/;

const load = (p: string): J => JSON.parse(fs.readFileSync(p, "utf8"));

// ---- lookups ------------------------------------------------------------------------------
const namesJson = load(path.join(ROOT, "data", "names.json"));
const names = new Map<string, Set<string>>();
for (const [cat, d] of Object.entries<J>(namesJson)) {
  if (cat === "meta") continue;
  for (const [zh, e] of Object.entries<J>(d)) {
    if (e.en) (names.get(zh) ?? names.set(zh, new Set()).get(zh)!).add(e.en);
  }
}
const gloss: Record<string, J> = load(path.join(ROOT, "data", "glossary.json")).terms;
const tm: Record<string, string | null> = {};
const tmDir = path.join(ROOT, "translate", "manual", "texts");
for (const f of fs.readdirSync(tmDir).filter((f) => f.endsWith(".json")).sort()) {
  Object.assign(tm, load(path.join(tmDir, f)).texts);
}
const unofficialTable: Record<string, { en: string; kind: string; note: string }> = load(
  path.join(ROOT, "translate", "manual", "unofficial_names.json"),
).names;

// same keys as translate/check_numbers.py SKIP (+ lore and provenance kept out of the site)
const SKIP = new Set([
  "id", "item_ids", "unlinked", "source_url", "permalink", "revid", "smw_api_request", "rev_timestamp",
  "template_source_url", "template_revid", "effects_source_url", "effects_revid", "fetched_at", "i18n",
  "name_zh", "character_zh", "language", "translation", "source", "license", "page_title",
  "placeholders_nulled", "parse_notes", "game_only_items", "game_only_note", "count", "skill_zh", "slot_zh",
  "quality_zh", "game", "used_in", "lore", "affection", "portraits", "possible_match", "wiki_lookup",
]);
const LORE_TOP = new Set(["description"]); // gear / relic flavour text (kept in Chinese in data/en)

const STAT_RE = /^(?<num>[+\-]?\d+(?:\.\d+)?%?|%)?(?<term>[^\d%][\s\S]*?)$/;
const NOTE_RE = /^(?<body>[\s\S]+?)[（(](?<note>[^（）()]+)[）)]$/;
const DATE_RE = /^(\d{4}年)?\d{1,2}月\d{1,2}日$/;
const SCALING_RE =
  /^[\d.%/()\-+~]+%(?:的)?(物理&法术强度|法术&物理强度|物理与法术强度|法术与物理强度|法术强度|物理强度|攻击力|最大生命值|体质)(?:的)?(.*)$/;

const glossO = (term: string): O | null => {
  const e = gloss[term];
  if (!e || !e.en) return null;
  return e.source === "game_db" ? "o" : "t";
};

function splitStat(s: string): string | null {
  const m = STAT_RE.exec(s.trim());
  if (!m?.groups?.term) return null;
  const term = m.groups.term.trim();
  return /\d/.test(term) ? null : term;
}

const stats = { o: 0, t: 0, w: 0, unknown: 0, unknownSamples: [] as string[] };

interface Ctx {
  ts: Record<string, J>; // i18n.text_sources
  uoPaths: Set<string>;
  gameOnly: boolean;
  lore: boolean; // skip top-level "description" (flavour text)
}

function leafOrigin(zh: unknown, en: string, p: string, ctx: Ctx): O {
  if (ctx.uoPaths.has(p)) return "t";
  const ts = ctx.ts[p] ?? ctx.ts[p.replace(/\.text$/, "")];
  if (ts) return ts.source === "game_db" ? "o" : ts.source === "translated" ? "t" : "w";
  if (ctx.gameOnly) return HAN.test(String(zh ?? "")) || /[a-z]/i.test(en) ? "o" : "w";
  if (typeof zh !== "string" || !HAN.test(zh)) return "w";
  if (names.get(zh)?.has(en)) return "o";
  const g = gloss[zh];
  if (g?.en === en) return g.source === "game_db" ? "o" : "t";
  if (tm[zh] === en) return "t";
  if (DATE_RE.test(zh) || SCALING_RE.test(zh)) return "w";
  // stat strings "17532魔力", lists "a、b", notes "term（note）", costs "1000怒气"
  let worst: O = "o";
  for (const part of zh.split("、")) {
    let body = part.trim();
    const m = NOTE_RE.exec(body);
    if (m?.groups) {
      body = m.groups.body;
      worst = "t";
    }
    const term = splitStat(body);
    const o = term ? glossO(term) : null;
    if (!o) {
      // not a name, glossary term, manual translation or derived value: build_en.py's text() then took
      // the English from the game dictionary (exact entry / same-shape game text) -> official
      stats.unknown++;
      if (stats.unknownSamples.length < 8) stats.unknownSamples.push(`${p}: ${zh} -> ${en}`);
      return "o";
    }
    if (o === "t") worst = "t";
  }
  return worst;
}

interface Annot {
  src: Record<string, O>;
  miss: Record<string, { zh: string; reason: string }>;
  uo: Record<string, { zh: string; en: string; note: string; kind: string }[]>;
  disc: Record<string, { wiki: string[]; game: string[]; text_id: number }>;
}

const join = (p: string, k: string) => (p ? `${p}.${k}` : k);

/** Walk en (and zh in parallel), filling a.src; returns zh-path -> en-path map for nulls. */
function walk(zh: J, en: J, p: string, zp: string, ctx: Ctx, a: Annot, nulls: Map<string, string>, top: boolean) {
  if (en === null || en === undefined) {
    nulls.set(zp, p);
    return;
  }
  if (Array.isArray(en)) {
    en.forEach((v, i) => walk(Array.isArray(zh) ? zh[i] : undefined, v, `${p}[${i}]`, `${zp}[${i}]`, ctx, a, nulls, false));
    return;
  }
  if (typeof en === "object") {
    const zk = zh && typeof zh === "object" ? Object.keys(zh) : [];
    const ek = Object.keys(en);
    const byPos = zk.some((k) => HAN.test(k)) && !ek.some((k) => HAN.test(k) && !SKIP.has(k));
    ek.forEach((k, i) => {
      if (SKIP.has(k) || (top && LORE_TOP.has(k) && ctx.lore)) return;
      const zkey = byPos ? zk[i] : k;
      walk(zh?.[zkey], en[k], join(p, k), join(zp, zkey), ctx, a, nulls, false);
    });
    return;
  }
  if (typeof en === "string") {
    const o = leafOrigin(zh, en, p, ctx);
    stats[o]++;
    if (o !== "w") a.src[p] = o;
  }
}

function annotate(zhRec: J, enRec: J, opts: { lore?: boolean; gameOnly?: boolean } = {}): Annot {
  const i18n = enRec.i18n ?? {};
  const a: Annot = { src: {}, miss: {}, uo: {}, disc: {} };
  for (const u of i18n.unofficial_names ?? []) {
    const t = unofficialTable[u.zh];
    (a.uo[u.path] ??= []).push({ zh: u.zh, en: u.en, note: t?.note ?? "", kind: t?.kind ?? "" });
  }
  const ctx: Ctx = { ts: i18n.text_sources ?? {}, uoPaths: new Set(Object.keys(a.uo)), gameOnly: !!opts.gameOnly, lore: !!opts.lore };
  const nulls = new Map<string, string>();
  walk(zhRec, enRec, "", "", ctx, a, nulls, true);
  for (const m of i18n.missing ?? []) {
    // missing paths are in zh keys ("builds[1].slots.卡牌"); the null may be the leaf or a .name below it
    const enPath =
      nulls.get(m.path) ?? nulls.get(`${m.path}.name`) ?? nulls.get(`${m.path}.text`) ?? m.path;
    a.miss[enPath] = { zh: m.zh, reason: m.reason };
  }
  return a;
}

// ---- trimming (only what the site shows) -------------------------------------------------
function strip(rec: J, drop: string[]): J {
  const out: J = {};
  for (const [k, v] of Object.entries(rec)) if (!drop.includes(k)) out[k] = v;
  return out;
}

// ---- characters ---------------------------------------------------------------------------
const zhChars = new Map<string, J>();
for (const f of fs.readdirSync(path.join(ZH, "characters"))) {
  const r = load(path.join(ZH, "characters", f));
  zhChars.set(r.id, r);
}
const disc = load(path.join(EN, "discrepancies.json"));
const discBy = new Map<string, J[]>();
for (const x of disc.items) (discBy.get(x.record_zh) ?? discBy.set(x.record_zh, []).get(x.record_zh)!).push(x);

function addDisc(a: Annot, recordZh: string, kinds: string[], toEnPath: (p: string) => string) {
  for (const x of discBy.get(recordZh) ?? []) {
    if (!kinds.includes(x.kind)) continue;
    a.disc[toEnPath(x.path)] = { wiki: x.wiki_numbers, game: x.game_numbers, text_id: x.text_id };
  }
}

const characters: J[] = [];
for (const f of fs.readdirSync(path.join(EN, "characters")).sort()) {
  const en = load(path.join(EN, "characters", f));
  const zh = zhChars.get(en.id);
  if (!zh) throw new Error(`no data/zh record for ${en.id}`);
  const a = annotate(zh, en);
  addDisc(a, en.page_title, ["skill", "blood_rank"], (p) => (p.startsWith("blood_ranks.ranks[") ? `${p}.text` : p));
  // build slot -> gear ids (zh slot values are item names; a full-width ， separates variants)
  const builds = (en.builds ?? []).map((b: J, bi: number) => {
    const zb = zh.builds[bi];
    const zkeys = Object.keys(zb.slots ?? {});
    const ids = (v: string | null) =>
      v ? v.split("，").map((n) => (b.item_ids ?? {})[n.trim()] ?? null) : [];
    const slot_ids: Record<string, (string | null)[]> = {};
    Object.keys(b.slots ?? {}).forEach((k, i) => (slot_ids[k] = ids(zb.slots[zkeys[i]])));
    const alt_ids: Record<string, (string | null)[][]> = {};
    const zak = Object.keys(zb.alternatives ?? {});
    Object.keys(b.alternatives ?? {}).forEach((k, i) => {
      alt_ids[k] = (zb.alternatives[zak[i]] ?? []).map((n: string) => ids(n));
    });
    const ext_ids: Record<string, (string | null)[]> = {};
    const zek = Object.keys(zb.extracts ?? {});
    Object.keys(b.extracts ?? {}).forEach((k, i) => {
      const v = zb.extracts[zek[i]];
      ext_ids[k] = typeof v === "string" ? ids(v) : [];
    });
    const sw = zb.signature_weapon ? ids(zb.signature_weapon) : [];
    return { ...strip(b, ["item_ids", "unlinked"]), slot_ids, alt_ids, ext_ids, sw_ids: sw };
  });
  characters.push({
    ...strip(en, ["unlinked", "placeholders_nulled", "parse_notes", "lore", "affection", "portraits", "i18n", "in_category_黑卫"]),
    name_zh: en.page_title,
    builds,
    _a: a,
  });
}

// ---- collections --------------------------------------------------------------------------
function coll(file: string, kinds: string[], opts: { lore?: boolean } = {}, discPath = (p: string) => p) {
  const e = load(path.join(EN, `${file}.json`));
  let zItems: J[] = [];
  if (fs.existsSync(path.join(ZH, `${file}.json`))) zItems = load(path.join(ZH, `${file}.json`)).items;
  const zById = new Map(zItems.map((z, i) => [z.id ?? i, z]));
  return {
    meta: strip(e, ["items"]),
    items: e.items.map((it: J, i: number) => {
      const gameOnly = it.source === "game_db";
      const z = gameOnly ? { name: it.name_zh, slot: it.slot_zh, quality: it.quality_zh, skill: it.skill_zh } : zById.get(it.id ?? i);
      const a = annotate(z, it, { ...opts, gameOnly });
      const zhName = it.i18n?.name_zh ?? it.page_title ?? it.name_zh;
      if (kinds.length) addDisc(a, zhName, kinds, discPath);
      if (gameOnly && it.skill === null && it.skill_zh) {
        a.miss["skill"] = { zh: it.skill_zh, reason: "the game's English skill text has other numbers than its Chinese text; not used" };
      }
      return {
        ...strip(it, ["i18n", "smw_api_request", "unlinked", "description", "description_source", "game", "skill_zh", "slot_zh", "quality_zh"]),
        name_zh: zhName,
        _a: a,
      };
    }),
  };
}

const gear = coll("gear", ["gear_skill"], { lore: true });
const relics = coll("relics", ["relic_skill"], { lore: true });
const runes = coll("runes", []);
const stones = coll("black_stones", []);
const factions = coll("factions", ["faction"], {}, (p) => (p.startsWith("thresholds[") ? `${p}.text` : p));
const tiersAll = coll("tiers", []);
// PvP is not shown on the site
const tiers = { meta: tiersAll.meta, items: tiersAll.items.filter((t: J) => t.mode === "PVE") };

const out = {
  generated_from: "data/en (yog-guide), snapshot of the game files 2026-09-22",
  characters,
  gear: gear.items,
  gear_note: gear.meta.game_only_note,
  relics: relics.items,
  runes: runes.items,
  stones: stones.items,
  factions: factions.items,
  tiers: tiers.items,
  guides: prepareGuides(ROOT, gloss, namesJson, {
    characters, gear: gear.items, factions: factions.items, stones: stones.items,
  }),
  unofficial_count: Object.keys(unofficialTable).length,
};

fs.mkdirSync(path.dirname(OUT), { recursive: true });
fs.writeFileSync(OUT, JSON.stringify(out));
const size = fs.statSync(OUT).size;
console.log(
  `data.json: ${characters.length} characters, ${gear.items.length} gear, ${relics.items.length} relics, ` +
    `${runes.items.length} runes, ${stones.items.length} black stones, ${factions.items.length} factions, ` +
    `${tiers.items.length} PvE tier entries; ${(size / 1024).toFixed(0)} KiB`,
);
console.log(`string origins: official ${stats.o}, translated ${stats.t}, wiki ${stats.w}; short game-dictionary texts (counted as official): ${stats.unknown}`);
for (const s of stats.unknownSamples) console.log("  e.g.", s);
