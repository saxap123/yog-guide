import { CHAR, GEAR, PVE, PVE_AS_OF, PVE_SOURCE, RELIC, RUNE, STONE, type Rec } from "../data.ts";
import { avatar, badge, badgeOf, ELEMENT_CLASS, esc, has, itemIcon, nameHtml, noData, originOf, richText, tierChip, val, wikiLink, zh } from "../ui.ts";
import { dollHtml, initDoll } from "./doll.ts";

const SLOT_ORDER = [
  "Weapon", "Off-hand", "Helmet", "Armor", "Handguard", "Belt", "Trousers", "Shoes",
  "Necklace", "Ring", "Earrings", "Emblem", "Card", "Relic",
];

const isPvp = (b: Rec) => b.qualifier === "PVP" || /\bPVP\b/i.test(b.level_tier ?? "");

// ---- main stat from skill scaling ---------------------------------------------------------
function mainStat(c: Rec): string {
  const by = new Map<string, { n: number; max: number; uses: string[]; paths: string[] }>();
  (c.skills ?? []).forEach((s: Rec, i: number) => {
    (s.scaling ?? []).forEach((sc: Rec, j: number) => {
      if (!sc.stat) return;
      const e = by.get(sc.stat) ?? { n: 0, max: 0, uses: [], paths: [] };
      e.n++;
      e.max = Math.max(e.max, ...(sc.values ?? [0]));
      const skillName = s.name ? richText(c, `skills[${i}].name`, s.name) : esc(s.name_zh);
      e.uses.push(`${skillName} <span class="muted">${esc(sc.percent ?? "")}${sc.effect ? " · " + esc(sc.effect) : ""}</span>`);
      e.paths.push(`skills[${i}].scaling[${j}].stat`);
      by.set(sc.stat, e);
    });
  });
  if (!by.size) return `<div class="kv"><span class="k">Main stat</span><span class="v">${noData(null, null, "no damage scaling in the wiki's skill texts")}</span></div>`;
  const ranked = [...by.entries()].sort((a, b) => b[1].n - a[1].n || b[1].max - a[1].max);
  const [top, info] = ranked[0];
  const others = ranked.slice(1);
  return `<div class="kv"><span class="k">Main stat</span><span class="v">
      <strong class="main-stat">${esc(top)}</strong> ${badge(c, info.paths)}
      <span class="muted">— scales ${info.n} skill effect${info.n > 1 ? "s" : ""}:</span>
      <ul class="uses">${info.uses.map((u) => `<li>${u}</li>`).join("")}</ul>
      ${others.length ? `<div class="muted small">Also scales: ${others.map(([s, e]) => `${esc(s)} (${e.n})`).join(", ")}</div>` : ""}
    </span></div>`;
}

// ---- affixes -------------------------------------------------------------------------------
function affixes(c: Rec): string {
  const a = c.affix_recommendations;
  const list = (key: "primary" | "secondary") => {
    const xs: string[] = a?.[key] ?? [];
    if (!xs.length) return noData(c, `affix_recommendations.${key}`);
    return `<ol class="affixes">${xs.map((_, i) => `<li>${val(c, `affix_recommendations.${key}[${i}]`)} ${badge(c, `affix_recommendations.${key}[${i}]`)}</li>`).join("")}</ol>`;
  };
  return `<div class="kv"><span class="k">Affixes — priority 1</span><span class="v">${list("primary")}</span></div>
          <div class="kv"><span class="k">Affixes — priority 2</span><span class="v">${list("secondary")}</span></div>`;
}

// ---- builds --------------------------------------------------------------------------------
function itemCell(c: Rec, value: string | null, ids: (string | null)[] | undefined, path: string, slot = "Item"): string {
  if (!value) return `<span class="cell-item">${itemIcon(null, slot)}${noData(c, path)}</span>`;
  const okIds = ids && ids.length && ids.every(Boolean) ? (ids as string[]) : null;
  if (okIds && okIds.length === 1) {
    const g = GEAR.get(okIds[0]);
    const gameOnly = g?.source === "game_db" ? ` <span class="tag" data-tip="No wiki page: item data from the game files (2026-09-22)" tabindex="0">game files</span>` : "";
    return `<span class="cell-item">${itemIcon(g, slot)}<a href="#/gear/${esc(okIds[0])}">${richText(c, path, value)}</a>${gameOnly}</span>`;
  }
  if (okIds) {
    return okIds.map((id) => `<span class="cell-item">${itemIcon(GEAR.get(id), slot)}${nameHtml(GEAR.get(id), `#/gear/${id}`)}</span>`).join(` <span class="muted">or</span> `);
  }
  return `<span class="cell-item">${itemIcon(null, slot)}${richText(c, path, value)} <span class="tag" data-tip="Not linked to an item page (see data/en/REPORT.md)" tabindex="0">no item page</span></span>`;
}

function buildPanel(c: Rec, b: Rec, bi: number): string {
  const base = `builds[${bi}]`;
  const rows: string[] = [];
  if (b.tier_note) rows.push(`<p class="note">${val(c, `${base}.tier_note`)} ${badge(c, `${base}.tier_note`)}</p>`);
  if (b.empty) {
    rows.push(`<p>${noData(c, base, "the wiki has no items for this build yet")}</p>`);
    return rows.join("");
  }
  rows.push(dollHtml(c, b, bi));
  rows.push(`<details class="btable"><summary>Build table</summary>`);
  const keys = [...SLOT_ORDER.filter((k) => k in (b.slots ?? {})), ...Object.keys(b.slots ?? {}).filter((k) => !SLOT_ORDER.includes(k))];
  rows.push(`<table class="slots"><thead><tr><th>Slot</th><th>Item</th><th>Source</th></tr></thead><tbody>
    ${keys
      .map((k) => {
        const p = `${base}.slots.${k}`;
        const v = b.slots[k];
        return `<tr><th scope="row">${esc(k)}</th><td>${itemCell(c, v, b.slot_ids?.[k], p, k)}</td><td>${v ? badge(c, p) : ""}</td></tr>`;
      })
      .join("")}</tbody></table>`);
  const alts = Object.entries<string[]>(b.alternatives ?? {});
  if (alts.length) {
    rows.push(`<h4>Alternatives</h4><ul class="alts">${alts
      .map(([k, xs]) => `<li><span class="k">${esc(k)}:</span> ${xs
        .map((v, i) => `${itemCell(c, v, b.alt_ids?.[k]?.[i], `${base}.alternatives.${k}[${i}]`, k)} ${v ? badge(c, `${base}.alternatives.${k}[${i}]`) : ""}`)
        .join(" · ")}</li>`)
      .join("")}</ul>`);
  }
  const ext = Object.entries<string>(b.extracts ?? {});
  if (ext.length) {
    rows.push(`<h4>Extracts</h4><ul class="alts">${ext
      .map(([k, v]) => `<li><span class="k">${esc(k)}:</span> ${itemCell(c, v, b.ext_ids?.[k], `${base}.extracts.${k}`, k)} ${badge(c, `${base}.extracts.${k}`)}</li>`)
      .join("")}</ul>`);
  }
  if (b.signature_weapon) {
    rows.push(`<p><span class="k">Signature weapon:</span> ${itemCell(c, b.signature_weapon, b.sw_ids, `${base}.signature_weapon`, "Weapon")} ${badge(c, `${base}.signature_weapon`)}</p>`);
  }
  rows.push(`</details>`);
  return rows.join("");
}

function builds(c: Rec): string {
  const all: { b: Rec; i: number }[] = (c.builds ?? []).map((b: Rec, i: number) => ({ b, i }));
  const shown = all.filter(({ b }) => !isPvp(b));
  const hidden = all.length - shown.length;
  if (!shown.length) {
    return `<div class="kv"><span class="k">Builds by level</span><span class="v">${noData(null, null)}${hidden ? ` <span class="muted small">(PvP builds are not shown)</span>` : ""}</span></div>`;
  }
  const tabs = shown
    .map(({ b, i }, n) => {
      const label = b.level_tier ? richText(c, `builds[${i}].level_tier`, b.level_tier) : noData(c, `builds[${i}].level_tier`);
      const kind = b.tier_kind === "level" ? (b.levels?.length ? `Lv ${b.levels.join("/")}` : b.level ? `Lv ${b.level}` : "") : "special";
      return `<button type="button" role="tab" class="tab" id="tab-${i}" aria-controls="panel-${i}" aria-selected="${n === 0}" data-panel="${i}">
        ${label}${kind ? ` <span class="tab-kind">${esc(kind)}</span>` : ""}</button>`;
    })
    .join("");
  const panels = shown
    .map(({ b, i }, n) => `<div role="tabpanel" class="panel" id="panel-${i}" aria-labelledby="tab-${i}"${n === 0 ? "" : " hidden"}>
        <div class="panel-head">Tab label: ${badge(c, `builds[${i}].level_tier`)}</div>${buildPanel(c, b, i)}</div>`)
    .join("");
  return `<div class="builds"><h3>Builds by level</h3>
    <div class="tabs" role="tablist">${tabs}</div>${panels}
    ${hidden ? `<p class="muted small">PvP builds are not shown (${hidden}).</p>` : ""}</div>`;
}

// ---- black stones, relic, runes -------------------------------------------------------------
function stones(c: Rec): string {
  const bs = c.black_stones;
  if (!bs?.stones?.length) return `<div class="kv"><span class="k">Black Stones <span lang="zh">黑石</span></span><span class="v">${noData(c, "black_stones")}</span></div>`;
  const items = bs.stones
    .map((s: Rec, i: number) => {
      const st = s.id ? STONE.get(s.id) : undefined;
      const name = s.name ? richText(c, `black_stones.stones[${i}].name`, s.name) : noData(c, `black_stones.stones[${i}].name`);
      const link = s.id ? `<a href="#/stones/${esc(s.id)}">${name}</a>` : name;
      const fx = (st?.effects ?? [])
        .map((e: Rec, j: number) => ({ e, j }))
        .filter(({ e }: { e: Rec }) => !s.count || e.pieces <= s.count)
        .map(({ e, j }: { e: Rec; j: number }) => `<li><span class="pieces">${esc(e.pieces)}-piece</span> ${val(st!, `effects[${j}].text`)} ${badge(st!, `effects[${j}].text`)}</li>`)
        .join("");
      return `<li><span class="cell-item">${itemIcon(st, "Black Stone")}<strong>${s.count ? esc(s.count) + " × " : ""}${link}</strong></span> ${s.name ? badge(c, `black_stones.stones[${i}].name`) : ""}
        ${fx ? `<ul class="fx">${fx}</ul>` : ""}</li>`;
    })
    .join("");
  const note = bs.note ? `<p class="note">${val(c, "black_stones.note")} ${badge(c, "black_stones.note")}</p>` : "";
  return `<div class="kv"><span class="k">Black Stones <span lang="zh">黑石</span></span><span class="v"><ul class="stones plain">${items}</ul>${note}</span></div>`;
}

function relics(c: Rec): string {
  const rs: Rec[] = c.relics ?? [];
  const body = rs.length
    ? rs
        .map((r, i) => {
          const rel = r.id ? RELIC.get(r.id) : undefined;
          const n = r.name ? richText(c, `relics[${i}].name`, r.name) : noData(c, `relics[${i}].name`);
          return `<span class="cell-item">${itemIcon(rel, "Relic")}${r.id ? `<a href="#/relics/${esc(r.id)}">${n}</a>` : n} ${r.name ? badge(c, `relics[${i}].name`) : ""} ${rel ? zh(rel.name_zh) : ""}</span>`;
        })
        .join("<br>")
    : noData(c, "relics");
  return `<div class="kv"><span class="k">Relic</span><span class="v">${body}</span></div>`;
}

function runeList(c: Rec, key: "main" | "support"): string {
  const xs: Rec[] = c.runes?.[key] ?? [];
  if (!xs.length) return noData(c, `runes.${key}`);
  return `<ol class="runes plain">${xs
    .map((r, i) => {
      const p = `runes.${key}[${i}].name`;
      const n = r.name ? richText(c, p, r.name) : noData(c, p);
      const ru = r.id ? RUNE.get(r.id) : undefined;
      return `<li><span class="cell-item">${itemIcon(ru, "Rune")}${ru ? `<a href="#/runes/${esc(r.id)}">${n}</a>` : n} ${r.name ? badge(c, p) : ""}</span></li>`;
    })
    .join("")}</ol>`;
}

function runes(c: Rec): string {
  if (!c.runes) return `<div class="kv"><span class="k">Runes</span><span class="v">${noData(c, "runes")}</span></div>`;
  return `<div class="kv"><span class="k">Runes — main</span><span class="v">${runeList(c, "main")}</span></div>
    <div class="kv"><span class="k">Runes — support</span><span class="v">${runeList(c, "support")}</span></div>
    ${c.runes.note ? `<div class="kv"><span class="k">Rune note</span><span class="v">${val(c, "runes.note")} ${badge(c, "runes.note")}</span></div>` : ""}`;
}

// ---- skills and blood ranks --------------------------------------------------------------
function skills(c: Rec): string {
  const ss: Rec[] = c.skills ?? [];
  if (!ss.length) return `<p>${noData(c, "skills")}</p>`;
  return ss
    .map((s, i) => {
      const p = `skills[${i}]`;
      const name = s.name ? richText(c, `${p}.name`, s.name) : noData(c, `${p}.name`);
      const meta = [
        s.cooldown_s ? `CD ${esc(s.cooldown_s)} s` : s.cooldown_raw ? `CD ${val(c, `${p}.cooldown_raw`)}` : "",
        s.cost && s.cost !== "0" ? `Cost ${val(c, `${p}.cost`)}` : "",
      ].filter(Boolean).join(" · ");
      return `<article class="skill">
        <header><span class="slot">${val(c, `${p}.slot`)}</span>
          <h4>${name} ${s.name ? badge(c, `${p}.name`) : ""} ${zh(s.name_zh)}</h4>
          ${meta ? `<span class="muted small">${meta}</span>` : ""}</header>
        <p>${val(c, `${p}.description`, { nl: true })} ${has(s.description) ? badge(c, `${p}.description`) : ""}</p>
      </article>`;
    })
    .join("");
}

function bloodRanks(c: Rec): string {
  const br = c.blood_ranks;
  if (!br?.ranks?.length) return `<p>${noData(c, "blood_ranks")}</p>`;
  const rows = br.ranks
    .map((r: Rec, i: number) => {
      const p = `blood_ranks.ranks[${i}].text`;
      return `<tr><th scope="row">${esc(r.rank)}</th><td>${val(c, p, { nl: true })}</td><td>${has(r.text) ? badge(c, p) : ""}</td></tr>`;
    })
    .join("");
  const rec = br.recommendation
    ? `<p class="note"><span class="k">Recommendation:</span> ${val(c, "blood_ranks.recommendation")} ${badge(c, "blood_ranks.recommendation")}</p>`
    : "";
  return `<table class="ranks"><thead><tr><th>Rank</th><th>Effect</th><th>Source</th></tr></thead><tbody>${rows}</tbody></table>${rec}`;
}

// ---- page -------------------------------------------------------------------------------------
export function renderCard(app: HTMLElement, id: string) {
  const c = CHAR.get(id);
  if (!c) {
    app.innerHTML = `<h1>Not found</h1><p><a href="#/">Back to the character list</a></p>`;
    return;
  }
  const t = PVE.get(id);
  const f = c.factions;
  const fac = (x: Rec | undefined, p: string) =>
    x ? (x.name ? `<a href="#/factions/${esc(x.id)}">${richText(c, p, x.name)}</a>` : noData(c, p)) : "";
  const facs = f
    ? [fac(f.base, "factions.base.name") + ' <span class="muted small">(base)</span>', ...(f.others ?? []).map((x: Rec, i: number) => fac(x, `factions.others[${i}].name`))].join(", ")
    : noData(c, "factions");
  const facPaths = f ? ["factions.base.name", ...(f.others ?? []).map((_: Rec, i: number) => `factions.others[${i}].name`)] : [];
  const tierTip = t ? `PvE tier list of the wiki${PVE_AS_OF ? `, as of ${PVE_AS_OF}` : ""}` : "";

  app.innerHTML = `
    <p class="crumbs"><a href="#/">Characters</a> /</p>
    <header class="hero">
      <div>
        <h1 class="hero-name">${avatar(c, "md")}<span>${nameHtml(c)} ${c.name ? badge(c, "name") : ""}</span></h1>
        <div class="hero-zh">${zh(c.name_zh)}${c.profile?.real_name ? ` · <span class="muted">real name</span> ${val(c, "profile.real_name")} ${badge(c, "profile.real_name")}` : ""}</div>
      </div>
      <div class="hero-tier" data-tip="${esc(tierTip)}" tabindex="0">
        <span class="muted small">PvE tier</span> ${tierChip(t?.tier)}
        ${t?.note ? `<div class="small">${val(t, "note", { nl: true })} ${badge(t, "note")}</div>` : ""}
        ${PVE_AS_OF ? `<div class="muted small">as of ${esc(PVE_AS_OF)}${PVE_SOURCE ? ` · <a class="ext" href="${esc(PVE_SOURCE)}" target="_blank" rel="noopener">source</a>` : ""}</div>` : ""}
      </div>
    </header>
    <dl class="facts">
      <div><dt>Element</dt><dd>${c.element ? `<span class="el ${ELEMENT_CLASS[c.element] ?? ""}">${esc(c.element)}</span> ${badge(c, "element")}` : noData(c, "element")}</dd></div>
      <div><dt>Rarity</dt><dd>${c.rarity ? `<span class="rar">${esc(c.rarity)}</span> ${badgeOf("w")}` : noData(c, "rarity")}</dd></div>
      <div><dt>Release</dt><dd>${val(c, "profile.release_date")} ${c.profile?.release_date ? badge(c, "profile.release_date") : ""}</dd></div>
      <div class="wide"><dt>Fronts <span lang="zh">阵线</span></dt><dd>${facs} ${facPaths.length ? badgeOf(originOf(c, facPaths)) : ""}</dd></div>
      <div class="wide"><dt>Wiki</dt><dd>${wikiLink(c)}</dd></div>
    </dl>
    ${c.note ? `<p class="note">${val(c, "note", { nl: true })} ${badge(c, "note")}</p>` : ""}

    <section class="howto">
      <h2>How to build</h2>
      ${mainStat(c)}
      ${affixes(c)}
      ${builds(c)}
      ${stones(c)}
      ${relics(c)}
      ${runes(c)}
    </section>

    <section><h2>Skills</h2>${skills(c)}</section>
    <section><h2>Blood ranks <span lang="zh">血阶</span></h2>${bloodRanks(c)}</section>`;

  // tabs
  const closePop = initDoll(app, c);
  const tabs = [...app.querySelectorAll<HTMLButtonElement>(".tab")];
  const select = (btn: HTMLButtonElement) => {
    closePop();
    for (const t2 of tabs) {
      const on = t2 === btn;
      t2.setAttribute("aria-selected", String(on));
      app.querySelector<HTMLElement>(`#panel-${t2.dataset.panel}`)!.hidden = !on;
    }
  };
  tabs.forEach((btn, i) => {
    btn.addEventListener("click", () => select(btn));
    btn.addEventListener("keydown", (e) => {
      const d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
      if (!d) return;
      const next = tabs[(i + d + tabs.length) % tabs.length];
      next.focus();
      select(next);
    });
  });
  document.title = `${c.name ?? c.name_zh} — Yog Guide`;
}
