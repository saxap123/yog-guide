import { CHAR, DATA, GEAR_USED_BY, type Rec } from "../data.ts";
import { avatar, badge, esc, has, itemIcon, nameHtml, noData, val, wikiLink, zh } from "../ui.ts";

type Kind = "gear" | "relics" | "runes" | "stones" | "factions";

interface RefDef {
  title: string;
  icon: string | null; // placeholder label for items without an icon (gear uses its slot); null = no icons
  lead: string;
  items: () => Rec[];
  filters: { key: string; label: string; get: (r: Rec) => string | null }[];
  summary: (r: Rec) => string;
  body: (r: Rec) => string;
}

/** A labelled list of strings at `key` (each with its own source badge). */
function list(r: Rec, key: string, label: string, opts: { ordered?: boolean } = {}): string {
  const xs: unknown[] = r[key] ?? [];
  if (!xs.length) return "";
  const tag = opts.ordered ? "ol" : "ul";
  return `<div class="kv"><span class="k">${esc(label)}</span><span class="v"><${tag} class="plain">${xs
    .map((_, i) => `<li>${val(r, `${key}[${i}]`, { nl: true })} ${badge(r, `${key}[${i}]`)}</li>`)
    .join("")}</${tag}></span></div>`;
}

function one(r: Rec, key: string, label: string, always = false): string {
  if (!has(r[key]) && !always) return "";
  return `<div class="kv"><span class="k">${esc(label)}</span><span class="v">${val(r, key, { nl: true })} ${has(r[key]) ? badge(r, key) : ""}</span></div>`;
}

function usedBy(r: Rec): string {
  const ids = [...(GEAR_USED_BY.get(r.id!) ?? [])];
  if (!ids.length) return "";
  return `<div class="kv"><span class="k">In builds of</span><span class="v">${ids
    .map((id) => CHAR.get(id))
    .filter((c): c is Rec => !!c)
    .map((c) => `<a class="who" href="#/c/${esc(c.id)}">${avatar(c, "sm")}${nameHtml(c)}</a>`)
    .join(" ")}</span></div>`;
}

const DEFS: Record<Kind, RefDef> = {
  gear: {
    title: "Gear",
    icon: "Item",
    lead: "Items from the wiki's item pages, plus items named in wiki builds that exist only in the game files (marked “game files”).",
    items: () => DATA.gear,
    filters: [
      { key: "slot", label: "All slots", get: (r) => r.slot },
      { key: "quality", label: "All qualities", get: (r) => r.quality },
    ],
    summary: (r) =>
      `${r.slot ? `<span class="muted">${esc(r.slot)}</span>` : ""}${r.quality ? ` · <span class="muted">${esc(r.quality)}</span>` : ""}${
        r.source === "game_db" ? ` <span class="tag">game files</span>` : ""
      }`,
    body: (r) => {
      const set = r.set;
      const setHtml = set?.bonuses?.length
        ? `<div class="kv"><span class="k">Set: ${val(r, "set.name")}</span><span class="v"><ul class="plain">${set.bonuses
            .map((b: Rec, i: number) => `<li><span class="pieces">${esc(b.pieces)}-piece</span> ${val(r, `set.bonuses[${i}].text`)} ${badge(r, `set.bonuses[${i}].text`)}</li>`)
            .join("")}</ul></span></div>`
        : "";
      const emb = (r.embed_recommendations ?? []) as Rec[];
      const embHtml = emb.length
        ? `<div class="kv"><span class="k">Socket recommendations</span><span class="v"><ul class="plain">${emb
            .map((e, i) => `<li><strong>${val(r, `embed_recommendations[${i}].name`)}</strong> — ${val(r, `embed_recommendations[${i}].effect`)} ${badge(r, [`embed_recommendations[${i}].name`, `embed_recommendations[${i}].effect`])}</li>`)
            .join("")}</ul></span></div>`
        : one(r, "embed_recommendations_raw", "Socketing");
      const notes = (r.notes ?? []) as string[];
      return [
        r.max_level ? `<div class="kv"><span class="k">Max level</span><span class="v">${esc(r.max_level)}</span></div>` : "",
        `<div class="kv"><span class="k">Skill</span><span class="v">${val(r, "skill", { nl: true })} ${has(r.skill) ? badge(r, "skill") : ""}</span></div>`,
        one(r, "main_stat", "Main stat"),
        list(r, "sub_stats", "Sub stats"),
        list(r, "exclusive", "Exclusive"),
        list(r, "prefixes", "Prefixes"),
        list(r, "suffixes", "Suffixes"),
        setHtml,
        one(r, "extract_skill", "Extraction"),
        embHtml,
        list(r, "obtain", "Obtain"),
        usedBy(r),
        notes.length ? `<div class="kv"><span class="k">Notes</span><span class="v"><ul class="plain muted">${notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></span></div>` : "",
        r.source === "game_db" ? `<p class="muted small">No wiki page — data from the game files dated 2026-09-22.</p>` : `<p>${wikiLink(r)}</p>`,
      ].join("");
    },
  },
  relics: {
    title: "Relics",
    icon: "Relic",
    lead: "Relics from the wiki.",
    items: () => DATA.relics,
    filters: [
      { key: "type", label: "All types", get: (r) => r.type },
      { key: "quality", label: "All qualities", get: (r) => r.quality },
    ],
    summary: (r) => `${r.type ? `<span class="muted">${esc(r.type)}</span>` : ""}${r.quality ? ` · <span class="muted">${esc(r.quality)}</span>` : ""}`,
    body: (r) =>
      [
        r.character
          ? `<div class="kv"><span class="k">Character</span><span class="v">${
              r.character.id && CHAR.get(r.character.id) ? `<a href="#/c/${esc(r.character.id)}">${val(r, "character.name")}</a>` : val(r, "character.name")
            } ${r.character.name ? badge(r, "character.name") : ""}</span></div>`
          : "",
        r.max_level ? `<div class="kv"><span class="k">Max level</span><span class="v">${esc(r.max_level)}</span></div>` : "",
        list(r, "skills", "Skills"),
        one(r, "advanced_fixed_skill", "Advanced (fixed)"),
        list(r, "advanced_random_skills", "Advanced (random)"),
        list(r, "exclusive", "Exclusive"),
        list(r, "prefixes", "Prefixes"),
        list(r, "suffixes", "Suffixes"),
        list(r, "obtain", "Obtain"),
        `<p>${wikiLink(r)}</p>`,
      ].join(""),
  },
  runes: {
    title: "Runes",
    icon: "Rune",
    lead: "Runes from the wiki.",
    items: () => DATA.runes,
    filters: [{ key: "type", label: "All types", get: (r) => r.type }],
    summary: (r) => (r.type ? `<span class="muted">${esc(r.type)}</span>` : ""),
    body: (r) =>
      [
        r.max_level ? `<div class="kv"><span class="k">Max level</span><span class="v">${esc(r.max_level)}</span></div>` : "",
        one(r, "attribute", "Attribute"),
        one(r, "exclusive_attribute", "Exclusive attribute"),
        list(r, "exclusive", "Exclusive"),
        list(r, "skills", "Skills"),
        list(r, "prefixes", "Prefixes"),
        list(r, "suffixes", "Suffixes"),
        (r.edges ?? []).length
          ? `<div class="kv"><span class="k">Edges</span><span class="v">${(r.edges as Rec[])
              .map((e, i) => `<span class="swatch" style="background:${/^#[0-9a-f]{3,8}$/i.test(e.color ?? "") ? e.color : "transparent"}"></span> ${val(r, `edges[${i}].color_name`)} × ${esc(e.count)} ${badge(r, `edges[${i}].color_name`)}`)
              .join("<br>")}</span></div>`
          : "",
        list(r, "obtain", "Obtain"),
        `<p>${wikiLink(r)}</p>`,
      ].join(""),
  },
  stones: {
    title: "Black Stones",
    icon: "Black Stone",
    lead: "黑石 — set effects for 2, 4 and 8 pieces, from the wiki page 黑石.",
    items: () => DATA.stones,
    filters: [],
    summary: () => "",
    body: (r) =>
      `<ul class="plain">${(r.effects ?? [])
        .map((e: Rec, i: number) => `<li><span class="pieces">${esc(e.pieces)}-piece</span> ${val(r, `effects[${i}].text`)} ${badge(r, `effects[${i}].text`)}</li>`)
        .join("") || `<li>${noData(r, "effects")}</li>`}</ul><p>${wikiLink(r)}</p>`,
  },
  factions: {
    title: "Fronts",
    icon: null,
    lead: "阵线 — fronts (factions) and their thresholds, from the wiki.",
    items: () => DATA.factions,
    filters: [{ key: "type", label: "All types", get: (r) => r.type }],
    summary: (r) => (r.type ? `<span class="muted">${esc(r.type)}</span>` : ""),
    body: (r) => {
      const members = DATA.characters.filter((c) => c.factions && [c.factions.base?.id, ...(c.factions.others ?? []).map((x: Rec) => x.id)].includes(r.id));
      return [
        one(r, "effect_on_page", "Effect"),
        `<div class="kv"><span class="k">Thresholds</span><span class="v"><ul class="plain">${(r.thresholds ?? [])
          .map((t: Rec, i: number) => `<li><span class="pieces">${esc(t.label ?? (t.levels ?? []).join("/"))}</span> ${val(r, `thresholds[${i}].text`, { nl: true })} ${badge(r, `thresholds[${i}].text`)}</li>`)
          .join("") || `<li>${noData(r, "thresholds")}</li>`}</ul></span></div>`,
        members.length
          ? `<div class="kv"><span class="k">Characters</span><span class="v">${members.map((c) => `<a class="who" href="#/c/${esc(c.id)}">${avatar(c, "sm")}${nameHtml(c)}</a>`).join(" ")}</span></div>`
          : "",
        `<p>${wikiLink(r)}</p>`,
      ].join("");
    },
  },
};

const state: Record<string, Record<string, string>> = {};

export function renderRef(app: HTMLElement, kind: Kind, openId?: string) {
  const def = DEFS[kind];
  const st = (state[kind] ??= { q: "" });
  const items = def.items();
  const opts = def.filters.map((f) => {
    const vals = [...new Set(items.map(f.get).filter((x): x is string => !!x))].sort();
    return `<select data-f="${f.key}" aria-label="${esc(f.label)}"><option value="">${esc(f.label)}</option>${vals
      .map((v) => `<option${st[f.key] === v ? " selected" : ""}>${esc(v)}</option>`)
      .join("")}</select>`;
  });
  app.innerHTML = `
    <h1>${esc(def.title)} <span class="count" id="count"></span></h1>
    <p class="lead">${esc(def.lead)}</p>
    <div class="filters">
      <input type="search" id="q" placeholder="Search — English or 中文" value="${esc(st.q)}" aria-label="Search" />
      ${opts.join("")}
    </div>
    <div id="items" class="items"></div>`;
  const box = app.querySelector<HTMLElement>("#items")!;
  const count = app.querySelector<HTMLElement>("#count")!;

  const draw = () => {
    const q = (st.q ?? "").trim().toLowerCase();
    const hits = items.filter((r) => {
      if (q && ![r.name, r.name_zh].filter(Boolean).join(" ").toLowerCase().includes(q)) return false;
      return def.filters.every((f) => !st[f.key] || f.get(r) === st[f.key]);
    });
    count.textContent = `${hits.length} / ${items.length}`;
    box.innerHTML = hits
      .map(
        (r) => `<details class="item" id="item-${esc(r.id)}"${r.id === openId ? " open" : ""}>
          <summary>${def.icon ? itemIcon(r, def.icon) : ""}<span class="item-name">${nameHtml(r)} ${r.name ? badge(r, "name") : ""}</span> ${zh(r.name_zh)} <span class="item-sum">${def.summary(r)}</span></summary>
          <div class="item-body" data-id="${esc(r.id)}"></div>
        </details>`,
      )
      .join("") || `<p class="muted">Nothing matches.</p>`;
    // bodies are rendered when opened (keeps the page light)
    const fill = (d: HTMLDetailsElement) => {
      const b = d.querySelector<HTMLElement>(".item-body")!;
      if (!b.dataset.done) {
        b.innerHTML = def.body(items.find((x) => x.id === b.dataset.id)!);
        b.dataset.done = "1";
      }
    };
    box.querySelectorAll<HTMLDetailsElement>("details").forEach((d) => {
      if (d.open) fill(d);
      d.addEventListener("toggle", () => d.open && fill(d));
    });
  };
  app.querySelector<HTMLInputElement>("#q")!.addEventListener("input", (e) => {
    st.q = (e.target as HTMLInputElement).value;
    draw();
  });
  app.querySelectorAll<HTMLSelectElement>("select[data-f]").forEach((s) =>
    s.addEventListener("input", () => {
      st[s.dataset.f!] = s.value;
      draw();
    }),
  );
  if (openId) {
    // make sure the linked item is visible even with filters set
    st.q = "";
    for (const f of def.filters) st[f.key] = "";
    app.querySelector<HTMLInputElement>("#q")!.value = "";
    app.querySelectorAll<HTMLSelectElement>("select[data-f]").forEach((s) => (s.value = ""));
  }
  draw();
  if (openId) document.getElementById(`item-${openId}`)?.scrollIntoView({ block: "start" });
  document.title = `${def.title} — Yog Guide`;
}

export type { Kind };
