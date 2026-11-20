import { DATA, FACTION, PVE, PVE_AS_OF, tierRank, TIER_ORDER, type Rec } from "../data.ts";
import { avatar, badge, ELEMENT_CLASS, esc, nameHtml, noData, tierChip, zh } from "../ui.ts";

const state = { q: "", element: "", rarity: "", faction: "", tier: "" };

const RARITY_ORDER = ["SP", "SS", "S", "A", "B"];
const uniq = (xs: (string | null | undefined)[]) => [...new Set(xs.filter((x): x is string => !!x))];

function factionIds(c: Rec): string[] {
  const f = c.factions;
  if (!f) return [];
  return [f.base?.id, ...(f.others ?? []).map((x: Rec) => x.id)].filter(Boolean);
}

function matches(c: Rec): boolean {
  const q = state.q.trim().toLowerCase();
  if (q) {
    const hay = [c.name, c.name_zh, c.profile?.real_name].filter(Boolean).join(" ").toLowerCase();
    if (!hay.includes(q)) return false;
  }
  if (state.element && c.element !== state.element) return false;
  if (state.rarity && c.rarity !== state.rarity) return false;
  if (state.faction && !factionIds(c).includes(state.faction)) return false;
  if (state.tier && (PVE.get(c.id!)?.tier ?? "not_ranked") !== state.tier) return false;
  return true;
}

function card(c: Rec): string {
  const t = PVE.get(c.id!);
  const base = c.factions?.base;
  return `<a class="ccard" href="#/c/${esc(c.id)}">${avatar(c, "md")}<div class="ccard-main">
    <div class="ccard-top">
      <span class="ccard-name">${nameHtml(c)} ${c.name ? badge(c, "name") : ""}</span>
      ${tierChip(t?.tier)}
    </div>
    <div class="ccard-zh">${zh(c.name_zh)}</div>
    <div class="ccard-meta">
      ${c.element ? `<span class="el ${ELEMENT_CLASS[c.element] ?? ""}">${esc(c.element)}</span>` : noData(c, "element")}
      ${c.rarity ? `<span class="rar">${esc(c.rarity)}</span>` : ""}
      <span class="muted">${base?.name ? esc(base.name) : noData(c, "factions.base.name")}</span>
    </div>
  </div></a>`;
}

function options(values: string[], current: string, label: (v: string) => string = (v) => v) {
  return values.map((v) => `<option value="${esc(v)}"${v === current ? " selected" : ""}>${esc(label(v))}</option>`).join("");
}

export function renderList(app: HTMLElement) {
  const chars = [...DATA.characters].sort(
    (a, b) =>
      tierRank(PVE.get(a.id!)?.tier) - tierRank(PVE.get(b.id!)?.tier) ||
      RARITY_ORDER.indexOf(a.rarity) - RARITY_ORDER.indexOf(b.rarity) ||
      (a.name ?? a.name_zh).localeCompare(b.name ?? b.name_zh),
  );
  const elements = uniq(chars.map((c) => c.element)).sort();
  const rarities = RARITY_ORDER.filter((r) => chars.some((c) => c.rarity === r));
  const facIds = uniq(chars.flatMap(factionIds));
  const facs = facIds.map((id) => FACTION.get(id)).filter((f): f is Rec => !!f).sort((a, b) => (a.name ?? "").localeCompare(b.name ?? ""));
  const tiers = TIER_ORDER.filter((t) => chars.some((c) => (PVE.get(c.id!)?.tier ?? "not_ranked") === t));

  app.innerHTML = `
    <h1>Characters <span class="count" id="count"></span></h1>
    <p class="lead">Blackguards of Book of Yog Idle RPG. Search by English or Chinese name; PvE tier from the wiki's PvE tier list${PVE_AS_OF ? ` (as of ${esc(PVE_AS_OF)})` : ""}.</p>
    <div class="filters">
      <input type="search" id="q" placeholder="Search name — English or 中文" value="${esc(state.q)}" aria-label="Search by English or Chinese name" />
      <select id="element" aria-label="Element"><option value="">All elements</option>${options(elements, state.element)}</select>
      <select id="rarity" aria-label="Rarity"><option value="">All rarities</option>${options(rarities, state.rarity)}</select>
      <select id="faction" aria-label="Front (faction)"><option value="">All fronts</option>${facs
        .map((f) => `<option value="${esc(f.id)}"${f.id === state.faction ? " selected" : ""}>${esc(f.name ?? f.name_zh)} · ${esc(f.name_zh)}</option>`)
        .join("")}</select>
      <select id="tier" aria-label="PvE tier"><option value="">All PvE tiers</option>${options(tiers, state.tier, (t) => (t === "not_ranked" ? "Not ranked yet" : t))}</select>
      <button type="button" id="reset" class="btn">Reset</button>
    </div>
    <div class="grid" id="grid"></div>`;

  const grid = app.querySelector<HTMLElement>("#grid")!;
  const count = app.querySelector<HTMLElement>("#count")!;
  const draw = () => {
    const hits = chars.filter(matches);
    count.textContent = `${hits.length} / ${chars.length}`;
    grid.innerHTML = hits.length ? hits.map(card).join("") : `<p class="muted">No characters match these filters.</p>`;
  };
  for (const id of ["q", "element", "rarity", "faction", "tier"] as const) {
    const el = app.querySelector<HTMLInputElement | HTMLSelectElement>(`#${id}`)!;
    el.addEventListener("input", () => {
      state[id] = el.value;
      draw();
    });
  }
  app.querySelector("#reset")!.addEventListener("click", () => {
    Object.assign(state, { q: "", element: "", rarity: "", faction: "", tier: "" });
    renderList(app);
  });
  draw();
}
