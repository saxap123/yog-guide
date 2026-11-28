import { CHAR, DATA, PVE_AS_OF, PVE_SOURCE, TIER_ORDER, type Rec } from "../data.ts";
import { avatar, badge, ELEMENT_CLASS, esc, nameHtml, noData, tierChip, val, zh } from "../ui.ts";

export function renderTiers(app: HTMLElement) {
  const groups = new Map<string, Rec[]>(TIER_ORDER.map((t) => [t, []]));
  for (const t of DATA.tiers) groups.get(t.tier)?.push(t);

  const entry = (t: Rec) => {
    const c = t.character_id ? CHAR.get(t.character_id) : undefined;
    const name = c ? nameHtml(c, `#/c/${c.id}`) : t.character ? esc(t.character) : noData(t, "character");
    return `<li class="tentry">${c ? `<a href="#/c/${esc(c.id)}" tabindex="-1">${avatar(c, "md")}</a>` : avatar(null, "md")}<div class="tbody">
      <span class="tname">${name} ${t.character ? badge(t, "character") : ""} ${zh(t.character_zh)}</span>
      ${c?.element ? `<span class="el ${ELEMENT_CLASS[c.element] ?? ""}">${esc(c.element)}</span>` : ""}
      ${c?.rarity ? `<span class="rar">${esc(c.rarity)}</span>` : ""}
      ${t.note ? `<div class="tnote">${val(t, "note", { nl: true })} ${badge(t, "note")}</div>` : ""}
    </div></li>`;
  };

  app.innerHTML = `
    <h1>PvE tier list</h1>
    <p class="lead">From the wiki page PVE节奏榜${PVE_AS_OF ? `, <strong>as of ${esc(PVE_AS_OF)}</strong>` : ""}${
      PVE_SOURCE ? ` (<a class="ext" href="${esc(PVE_SOURCE)}" target="_blank" rel="noopener">source revision</a>)` : ""
    }. The PvP list is not shown.</p>
    ${[...groups.entries()]
      .filter(([, xs]) => xs.length)
      .map(
        ([tier, xs]) => `<section class="tgroup">
          <h2>${tierChip(tier)} <span class="count">${xs.length}</span></h2>
          ${DATA.pve_sections[tier] ? `<p class="tnote">${esc(DATA.pve_sections[tier])}</p>` : ""}
          <ul class="tlist">${xs.map(entry).join("")}</ul>
        </section>`,
      )
      .join("")}`;
  document.title = "PvE tier list — Yog Guide";
}
