/**
 * Build-time image step (step 4b). READ-ONLY on the game files.
 *
 *   IMAGES=icons (default)  character avatars (96 px) + icons of gear, relics, runes, black stones
 *   IMAGES=full             + full character portraits (512 px) for the character page — local builds only
 *   IMAGES=none             no game images; the site shows placeholders
 *
 * Source: data/raw/game_db/03.ui/image_ab/ (heroicons = portraits/avatars, 01.icon = item icons),
 * or the folder in YOG_IMAGE_SRC. Matching:
 *   character -> data/names.json game_id = tpl_sc_hero id -> files named by icon_portrait / id / avatarID
 *   gear, relic, rune, black stone -> names.json game_id (gear-game-<id> for game-only gear)
 *     -> iconID of tpl_sc_equipment / tpl_sc_heirloom / tpl_sc_rune / tpl_sc_blackStone -> file of that name
 * Output: web/public/img/** (WebP, git-ignored), src/generated/images.json (manifest),
 * docs/IMAGES_REPORT.md (what matched, what did not). Originals are never modified.
 */
import fs from "node:fs";
import path from "node:path";

type J = any; // eslint-disable-line @typescript-eslint/no-explicit-any
type Mode = "icons" | "full" | "none";

const WEB = path.resolve(import.meta.dirname, "..");
const ROOT = path.resolve(WEB, "..");
const DB = path.join(ROOT, "data", "raw", "game_db");
const TPL = path.join(DB, "08.database", "template");
const SRC = process.env.YOG_IMAGE_SRC ? path.resolve(process.env.YOG_IMAGE_SRC) : path.join(DB, "03.ui", "image_ab");
const OUT = path.join(WEB, "public", "img");
const MANIFEST = path.join(WEB, "src", "generated", "images.json");
const REPORT = path.join(ROOT, "docs", "IMAGES_REPORT.md");
const SIZE = { avatar: 96, portrait: 512, icon: 96 };
const EXT = /\.(png|jpe?g|webp|tga|bmp)$/i;

const mode = (process.env.IMAGES ?? "icons").toLowerCase() as Mode;
if (!["icons", "full", "none"].includes(mode)) {
  console.error(`IMAGES must be icons, full or none (got "${process.env.IMAGES}")`);
  process.exit(2);
}

const load = (p: string): J => JSON.parse(fs.readFileSync(p, "utf8"));

interface Manifest {
  mode: Mode;
  source: string;
  avatars: Record<string, string>;
  portraits: Record<string, string>;
  icons: Record<string, string>;
  /** record id -> base file used because the game has no icon of its own for it (runes only) */
  shared: Record<string, string>;
  frames: Record<string, { plate: string; border: string }>;
}
/** Runes whose iconID item_RuneStone_secondary_02_<N> is not in the files: the game's generic rune
 *  stone icon is shown instead, captioned with the rune's name on the site (step 5). */
const SHARED_RUNE_ICON = "item_runestone_secondary_02";
/** cell of the 01.title quality strips per English quality (grades 4 6 8 10 11 12 = cells 3..8) */
const QUALITY_CELL: Record<string, number> = { Epic: 3, Legend: 4, Mythic: 6, Eternal: 7, Archaic: 8 };
let frameNote = "";
const manifest: Manifest = { mode, source: path.relative(ROOT, SRC).replaceAll("\\", "/"), avatars: {}, portraits: {}, icons: {}, shared: {}, frames: {} };

// clean only our own output folder
fs.rmSync(OUT, { recursive: true, force: true });
fs.mkdirSync(path.dirname(MANIFEST), { recursive: true });

// ---- game tables (ids and icon names only) -------------------------------------------------
function rows(table: string): Map<string, Record<string, string>> {
  const p = path.join(TPL, `${table}.xml`);
  const out = new Map<string, Record<string, string>>();
  if (!fs.existsSync(p)) return out;
  const s = fs.readFileSync(p, "utf8");
  for (const m of s.matchAll(/<(\w+)>\s*(<id>[\s\S]*?)<\/\1>/g)) {
    const r: Record<string, string> = {};
    for (const f of m[2].matchAll(/<(\w+)>([^<]*)<\/\1>/g)) r[f[1]] = f[2];
    if (r.id) out.set(r.id, r);
  }
  return out;
}

// ---- records of the site -> game ids --------------------------------------------------------
const names = load(path.join(ROOT, "data", "names.json"));
const EN = path.join(ROOT, "data", "en");
const gid = (cat: string, zh: string | null | undefined): string | null => {
  const v = zh ? names[cat]?.[zh]?.game_id : null;
  if (v === null || v === undefined || v === "") return null;
  return Array.isArray(v) ? v.join(",") : String(v);
};

interface Want {
  kind: "character" | "gear" | "relic" | "rune" | "stone";
  id: string; // site record id
  label: string; // for the report
  gameId: string | null;
  why?: string;
}
const wants: Want[] = [];
for (const f of fs.readdirSync(path.join(EN, "characters")).sort()) {
  const c = load(path.join(EN, "characters", f));
  wants.push({ kind: "character", id: c.id, label: `${c.name ?? "—"} (${c.page_title})`, gameId: gid("characters", c.page_title) });
}
for (const g of load(path.join(EN, "gear.json")).items) {
  const m = /^gear-game-(\d+)$/.exec(g.id);
  wants.push({ kind: "gear", id: g.id, label: `${g.name ?? "—"} (${g.page_title ?? g.name_zh})`, gameId: m ? m[1] : gid("gear", g.page_title) });
}
for (const r of load(path.join(EN, "relics.json")).items) {
  wants.push({ kind: "relic", id: r.id, label: `${r.name ?? "—"} (${r.page_title})`, gameId: gid("relics", r.page_title) });
}
for (const r of load(path.join(EN, "runes.json")).items) {
  wants.push({ kind: "rune", id: r.id, label: `${r.name ?? "—"} (${r.page_title})`, gameId: gid("runes", r.page_title) });
}
for (const s of load(path.join(EN, "black_stones.json")).items) {
  const zh = s.i18n?.name_zh;
  wants.push({ kind: "stone", id: s.id, label: `${s.name ?? "—"} (${zh})`, gameId: gid("black_stones", zh) });
}

const TABLE: Record<Want["kind"], string> = {
  character: "tpl_sc_hero", gear: "tpl_sc_equipment", relic: "tpl_sc_heirloom", rune: "tpl_sc_rune", stone: "tpl_sc_blackStone",
};
const tables = new Map<string, Map<string, Record<string, string>>>();
const dbOk = fs.existsSync(TPL);
if (dbOk) for (const t of new Set(Object.values(TABLE))) tables.set(t, rows(t));

// ---- image files ------------------------------------------------------------------------------
const files: { path: string; base: string; rel: string }[] = [];
function scan(dir: string) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) scan(p);
    else if (EXT.test(e.name)) files.push({ path: p, base: e.name.replace(EXT, "").toLowerCase(), rel: path.relative(SRC, p) });
  }
}
const srcOk = mode !== "none" && fs.existsSync(SRC);
if (srcOk) scan(SRC);
const heroFiles = files.filter((f) => /heroicon/i.test(f.rel));
const iconFiles = files.filter((f) => /(^|[\\/])01\.icon([\\/]|$)/i.test(f.rel));
const byBase = (list: typeof files) => {
  const m = new Map<string, (typeof files)[number]>();
  for (const f of list) if (!m.has(f.base)) m.set(f.base, f);
  return m;
};
const iconIdx = byBase(iconFiles);
// files directly in heroicons/ (not bust/, npcicon/)
const heroTop = byBase(heroFiles.filter((f) => /^heroicons[\\/][^\\/]+$/i.test(f.rel)));
const allIdx = byBase(files);

// ---- matching ----------------------------------------------------------------------------------
interface Hit { want: Want; key: string | null; avatar?: string; portrait?: string; icon?: string; note?: string; shared?: boolean }
const hits: Hit[] = [];
for (const w of wants) {
  const h: Hit = { want: w, key: null };
  hits.push(h);
  if (!w.gameId) { h.note = "no game id in data/names.json (name not in the game files)"; continue; }
  // names.json may list several game rows ("1001,2001"): the first row that exists is used
  const ids = w.gameId.split(",").map((s) => s.trim());
  const id = ids.find((i) => tables.get(TABLE[w.kind])?.has(i)) ?? ids[0];
  w.gameId = id;
  const row = tables.get(TABLE[w.kind])?.get(id);
  if (!dbOk) { h.note = "game tables not found"; continue; }
  if (!row) { h.note = `no row ${w.gameId} in ${TABLE[w.kind]}`; continue; }
  if (w.kind === "character") {
    const keys = [...new Set([row.icon_portrait, row.id, row.avatarID].filter((k) => k && k !== "0"))].map((k) => k.toLowerCase());
    h.key = keys.join(" / ");
    // heroicons/ per hero (checked by eye on 741, 719, 708, 402):
    //   square_<k>    300x196 head-and-shoulders crop -> avatar (square crop from the centre)
    //   circular_<k>  246x358 framed card with the rarity badge (only a fallback for the avatar)
    //   portrait_<k>  or portrait_<k>_0..3: full art; the numbered files are layers of one picture
    //                 (2048x2048 each, some are 32x32 stubs); the complete one is the largest file in bytes
    const k = keys.find((x) => heroTop.has(`square_${x}`) || heroTop.has(`circular_${x}`) || heroTop.has(`portrait_${x}`) || heroTop.has(`portrait_${x}_0`));
    if (!k) {
      h.note = srcOk ? `no square_/circular_/portrait_ file for ${keys.join(" / ")} in heroicons` : undefined;
      continue;
    }
    const sq = heroTop.get(`square_${k}`) ?? heroTop.get(`circular_${k}`);
    if (sq) h.avatar = sq.path;
    if (sq && !heroTop.has(`square_${k}`)) h.note = `no square_${k}; avatar cut from the card circular_${k}`;
    if (!sq) h.note = `no square_${k} or circular_${k}`;
    const layerRe = new RegExp(`^portrait_${k}(_\\d+)?$`);
    const layers = [...heroTop.values()].filter((f) => layerRe.test(f.base));
    const best = layers.sort((a, b) => fs.statSync(b.path).size - fs.statSync(a.path).size)[0];
    if (best) h.portrait = best.path;
  } else {
    const key = (row.iconID ?? "").toLowerCase();
    h.key = key || null;
    if (!key || key === "0") { h.note = `no iconID in ${TABLE[w.kind]} row ${w.gameId}`; continue; }
    let f = iconIdx.get(key) ?? allIdx.get(key);
    if (!f) {
      // size variants: iconID item_blackStone11 -> files item_blackStone11_128.png / _50.png (largest wins)
      const sizeRe = new RegExp(`^${key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}_(\\d{2,4})$`);
      f = iconFiles
        .filter((x) => sizeRe.test(x.base))
        .sort((a, b) => Number(sizeRe.exec(b.base)![1]) - Number(sizeRe.exec(a.base)![1]))[0];
      if (f) h.note = `size variant ${path.basename(f.path)}`;
    }
    if (!f && w.kind === "rune" && key.startsWith(`${SHARED_RUNE_ICON}_`) && iconIdx.has(SHARED_RUNE_ICON)) {
      f = iconIdx.get(SHARED_RUNE_ICON)!;
      h.shared = true;
      h.note = `no file ${row.iconID}; shared icon ${path.basename(f.path)}, captioned with the rune name`;
    }
    if (f) h.icon = f.path;
    else if (srcOk) h.note = `no file ${row.iconID} in 01.icon` +
      (/_\d+$/.test(key) && allIdx.has(key.replace(/_\d+$/, "")) ? ` (only ${key.replace(/_\d+$/, "")} exists; the _N variant is not in the files, not substituted)` : "");
  }
}

// ---- conversion --------------------------------------------------------------------------------
async function convert() {
  if (!srcOk) return;
  const sharp = (await import("sharp")).default;
  const done = new Map<string, string>(); // source+size -> url (icons are shared between items)
  const write = async (src: string, sub: string, name: string, px: number, fit: "contain" | "cover", position = "top") => {
    const k = `${src}|${px}|${fit}|${position}`;
    if (done.has(k)) return done.get(k)!;
    const rel = `img/${sub}/${name}.webp`;
    fs.mkdirSync(path.join(OUT, sub), { recursive: true });
    await sharp(src)
      .resize(px, px, { fit, position, withoutEnlargement: true, background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .webp({ quality: 82, alphaQuality: 90 })
      .toFile(path.join(OUT, sub, `${name}.webp`));
    done.set(k, rel);
    return rel;
  };
  // Quality frames from 01.title: two strips of 9 cells (128 px, one every 130 px) in item-grade order.
  // Grades: tpl_sc_equipment.equipmentGrade tops out at 10 for Mythic, 11 for Eternal, 12 for Archaic;
  // cell colours agree with the colours the game's texts give 史诗 / 传说 / 不朽 / 神话 / 永恒.
  const plate = path.join(SRC, "01.title", "ui_common_物品品质底板.png");
  const border = path.join(SRC, "01.title", "ui_common_物品品质边框.png");
  if (fs.existsSync(plate) && fs.existsSync(border)) {
    fs.mkdirSync(path.join(OUT, "frame"), { recursive: true });
    for (const [q, cell] of Object.entries(QUALITY_CELL)) {
      const urls: string[] = [];
      for (const [src, part] of [[plate, "plate"], [border, "border"]] as const) {
        const rel = `img/frame/${part}-${cell}.webp`;
        if (!fs.existsSync(path.join(WEB, "public", rel))) {
          await sharp(src).extract({ left: cell * 130, top: 0, width: 128, height: 128 }).resize(SIZE.icon, SIZE.icon)
            .webp({ quality: 85, alphaQuality: 95 }).toFile(path.join(WEB, "public", rel));
        }
        urls.push(rel);
      }
      manifest.frames[q] = { plate: urls[0], border: urls[1] };
    }
  } else frameNote = "quality frame strips not found in 01.title; CSS colours are used";
  for (const h of hits) {
    const w = h.want;
    if (w.kind === "character") {
      if (h.avatar) {
        const card = /circular_/i.test(path.basename(h.avatar));
        manifest.avatars[w.id] = await write(h.avatar, "avatar", w.gameId!, SIZE.avatar, "cover", card ? "top" : "centre");
        h.avatar = path.relative(SRC, h.avatar);
      }
      if (h.portrait) {
        if (mode === "full") manifest.portraits[w.id] = await write(h.portrait, "portrait", w.gameId!, SIZE.portrait, "contain");
        h.portrait = path.relative(SRC, h.portrait);
      }
    } else if (h.icon) {
      const name = path.basename(h.icon).replace(EXT, "").toLowerCase();
      manifest.icons[w.id] = await write(h.icon, "icon", name, SIZE.icon, "contain");
      if (h.shared) manifest.shared[w.id] = name;
      h.icon = path.relative(SRC, h.icon);
    }
  }
}

// ---- report ------------------------------------------------------------------------------------
function report() {
  const L: string[] = [];
  const w = (s = "") => L.push(s);
  const KINDS: [Want["kind"], string][] = [["character", "characters"], ["gear", "gear"], ["relic", "relics"], ["rune", "runes"], ["stone", "black stones (黑石)"]];
  const has = (h: Hit) => (h.want.kind === "character" ? !!manifest.avatars[h.want.id] : !!manifest.icons[h.want.id]);
  w("# Images report (step 4b)");
  w();
  w(`Generated by \`web/scripts/prepare-images.ts\` (mode \`IMAGES=${mode}\`). Source: \`${manifest.source}\` ` +
    (srcOk ? `(${files.length} image files: heroicons ${heroFiles.length}, 01.icon ${iconFiles.length}).` : mode === "none" ? "(not read: IMAGES=none)." : "— **folder not found**, no images; the site shows placeholders."));
  w("Game files are read only; output is WebP in `web/public/img/` (git-ignored). Game art © HangZhou QiHeShe Technology, used for reference.");
  w();
  w("| kind | records | game id + icon name | image file found |");
  w("|---|---|---|---|");
  for (const [k, label] of KINDS) {
    const hs = hits.filter((h) => h.want.kind === k);
    w(`| ${label} | ${hs.length} | ${hs.filter((h) => h.key).length} | ${hs.filter(has).length} |`);
  }
  w();
  if (mode === "full") w(`Full portraits: ${Object.keys(manifest.portraits).length}.\n`);
  w("Characters: avatar = `heroicons/square_<id>` (300×196 head crop, cut to a square from the centre); full portrait " +
    "(IMAGES=full) = `portrait_<id>` or the largest (in bytes) of its layer files `portrait_<id>_0..3`; `circular_<id>` " +
    "(a framed card) is used for the avatar only when there is no `square_`.\n");
  w(Object.keys(manifest.frames).length
    ? "Quality frames: `01.title/ui_common_物品品质底板.png` (plate) + `ui_common_物品品质边框.png` (border), cells " +
      Object.entries(QUALITY_CELL).map(([q, c]) => `${q} ${c}`).join(", ") + ". The strips are in grade order; " +
      "Archaic is the last cell by that order only (the game texts give 太古 no colour). Items without a quality " +
      "(runes, black stones, game-only gear without a fixed quality) keep a neutral CSS frame.\n"
    : `Quality frames: ${frameNote || "not used"}.\n`);
  for (const [k, label] of KINDS) {
    const miss = hits.filter((h) => h.want.kind === k && !has(h));
    if (!miss.length) continue;
    w(`## Without an image: ${label} (${miss.length})`);
    w();
    w("| record | game id | icon name | why |");
    w("|---|---|---|---|");
    for (const h of miss) w(`| ${h.want.label} | ${h.want.gameId ?? "—"} | ${h.key ?? "—"} | ${h.note ?? (srcOk ? "—" : "image folder not available")} |`);
    w();
  }
  const shared = hits.filter((h) => h.shared && manifest.icons[h.want.id]);
  if (shared.length) {
    w(`## Shared icon: runes (${shared.length})`);
    w();
    w(`The game has no file for these runes' own iconID; the generic rune stone icon \`${SHARED_RUNE_ICON}\` ` +
      "is shown, captioned with the rune's name (tooltip: shared icon).");
    w();
    w("| record | game id | icon name |");
    w("|---|---|---|");
    for (const h of shared) w(`| ${h.want.label} | ${h.want.gameId} | ${h.key} |`);
    w();
  }
  const cropped = hits.filter((h) => h.note?.startsWith("no small avatar"));
  if (cropped.length) w(`Avatars cropped from a portrait: ${cropped.map((h) => h.want.label).join(", ")}.\n`);
  fs.mkdirSync(path.dirname(REPORT), { recursive: true });
  fs.writeFileSync(REPORT, L.join("\n"));
}

await convert();
fs.writeFileSync(MANIFEST, JSON.stringify(manifest));
report();
const n = (k: Want["kind"]) => hits.filter((h) => h.want.kind === k).length;
console.log(
  `images (${mode}): avatars ${Object.keys(manifest.avatars).length}/${n("character")}, portraits ${Object.keys(manifest.portraits).length}, ` +
    `icons ${Object.keys(manifest.icons).length}/${n("gear") + n("relic") + n("rune") + n("stone")}` +
    (mode !== "none" && !srcOk ? ` — image folder not found: ${SRC}` : ""),
);
if (mode === "full") console.log("IMAGES=full: full portraits are for local builds only — do not publish this dist/.");
