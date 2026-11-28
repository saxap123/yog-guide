import { DATA } from "../data.ts";
import type { GuideArticle, GuideName, GuideScreenshot } from "../guide-data.ts";
import { esc, zh } from "../ui.ts";

const WIKI = "https://wiki.biligame.com/bookofyog/";
const ANNOUNCEMENTS = "https://steamcommunity.com/app/1097430/announcements/";

function name(part: GuideName, bilingual = false): string {
  const text = esc(part.text);
  const label = part.zh ? `<span${part.text === part.zh ? ' lang="zh"' : ""}>${text}</span>` : text;
  const link = part.href
    ? `<a href="${esc(part.href)}"${part.href.startsWith("#") ? "" : ' class="ext" target="_blank" rel="noopener"'}>${label}</a>`
    : label;
  return link + (bilingual && part.zh !== part.text ? " " + zh(part.zh) : "");
}

function articleList(): string {
  return `
    <h1>Guides</h1>
    <p class="lead">Get started, protect valuable gear, and find your next upgrade.</p>
    <div class="grid guide-grid">
      ${DATA.guides.articles.map((article) => `
        <a class="ccard" href="#/guides/${esc(article.id)}">
          <span class="ccard-name">${esc(article.title)}</span>
          <span class="guide-card-summary">${esc(article.summary)}</span>
        </a>`).join("")}
    </div>`;
}

function screenshot({ title, alt, width, height, src, source, notes }: GuideScreenshot): string {
  return `
    <figure class="guide-screenshot">
      <a class="guide-screenshot-image" href="${esc(src)}" target="_blank" rel="noopener"
        aria-label="Open full-size screenshot of ${esc(title)}">
        <img src="${esc(src)}" width="${width}" height="${height}" alt="${esc(alt)}" loading="lazy" decoding="async">
      </a>
      <figcaption>
        <h3>${esc(title)}</h3>
        <ul>${notes.map((note) => `<li>${note.map((part) => name(part)).join("")}</li>`).join("")}</ul>
        <a class="ext small" href="${esc(source)}" target="_blank" rel="noopener">Wiki image source</a>
      </figcaption>
    </figure>`;
}

function keepTable(): string {
  const rows = DATA.guides.keep;
  const slots = [...new Set(rows.map(({ slot }) => slot))].sort();
  return `
    <section class="guide-reference" aria-labelledby="keep-heading">
      <h2 id="keep-heading">Decomposition keep list</h2>
      <div class="filters">
        <input type="search" data-guide-search placeholder="Search in English or Chinese" aria-label="Search keep list" />
        <select data-guide-slot aria-label="Gear slot">
          <option value="">All slots</option>
          ${slots.map((slot) => `<option>${esc(slot)}</option>`).join("")}
        </select>
        <label class="guide-checkbox"><input type="checkbox" data-guide-fuse /> Three-star fusion only</label>
      </div>
      <p class="muted guide-result" data-guide-count role="status">${rows.length} items</p>
      <div class="guide-table-wrap">
        <table class="guide-table" aria-labelledby="keep-heading">
          <thead><tr><th scope="col">Item</th><th scope="col">Slot</th><th scope="col">Wiki fusion advice</th></tr></thead>
          <tbody>${rows.map((row) => `
            <tr data-slot="${esc(row.slot)}" data-fuse="${row.fuse ?? ""}">
              <td>${name(row.name, true)}</td><td>${esc(row.slot)}</td>
              <td>${row.fuse ? `${row.fuse} stars` : "—"}</td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
    </section>`;
}

function deepMistTable(): string {
  return `
    <section class="guide-reference" aria-labelledby="deep-mist-heading">
      <h2 id="deep-mist-heading">Deep Mist Black Stone drops</h2>
      <div class="filters">
        <input type="search" data-guide-search placeholder="Search by stone name or floor band" aria-label="Search Deep Mist drops" />
      </div>
      <p class="muted guide-result" data-guide-count role="status">${DATA.guides.deepMist.length} floor bands</p>
      <div class="guide-table-wrap">
        <table class="guide-table" aria-labelledby="deep-mist-heading">
          <thead><tr><th scope="col">Floors</th><th scope="col">Listed Black Stones</th></tr></thead>
          <tbody>${DATA.guides.deepMist.map(({ floors, stones }) => `
            <tr><th scope="row">${esc(floors)}</th>
              <td><ul class="guide-inline">${stones.map((stone) => `<li>${name(stone, true)}</li>`).join("")}</ul></td>
            </tr>`).join("")}</tbody>
        </table>
      </div>
    </section>`;
}

function sourceLinks(article: GuideArticle): string {
  return `
    <section class="guide-sources" aria-labelledby="guide-sources-heading">
      <h2 id="guide-sources-heading">Sources</h2>
      <ul>
        ${article.sources.map((source) => {
          const revision = WIKI + "index.php?oldid=" + source.revid;
          const href = source.interactive ? WIKI + encodeURIComponent(source.title) : revision;
          return `<li><a class="ext" href="${esc(href)}" target="_blank" rel="noopener">${esc(source.label)}</a>
            <span class="muted">${source.author ? ` · <span lang="zh">${esc(source.author)}</span>` : ""} · <time datetime="${esc(source.date)}">${esc(source.date)}</time></span>
            ${source.interactive ? ` · <a href="${esc(revision)}" target="_blank" rel="noopener">Wiki revision</a>` : ""}</li>`;
        }).join("")}
        ${article.officialAnnouncements
          ? `<li><a class="ext" href="${ANNOUNCEMENTS}" target="_blank" rel="noopener">Official Steam announcements</a></li>` : ""}
      </ul>
      <p class="muted">Adapted into English from BWIKI 依盖之书 by 赧然丶 and contributors.
        <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target="_blank" rel="noopener">CC BY-NC-SA 4.0</a>.</p>
    </section>`;
}

function bindTableFilters(app: HTMLElement): void {
  const section = app.querySelector<HTMLElement>(".guide-reference");
  if (!section) return;
  const search = section.querySelector<HTMLInputElement>("[data-guide-search]")!;
  const slot = section.querySelector<HTMLSelectElement>("[data-guide-slot]");
  const fuse = section.querySelector<HTMLInputElement>("[data-guide-fuse]");
  const count = section.querySelector<HTMLElement>("[data-guide-count]")!;
  const table = section.querySelector<HTMLTableElement>("table")!;
  const tableWrap = table.parentElement!;
  const normalize = (value: string) => value.trim().toLowerCase().replaceAll("–", "-");
  const rows = Array.from(table.tBodies[0].rows, (row) => ({
    row, search: normalize(Array.from(row.cells, (cell) => cell.textContent ?? "").join(" ")),
  }));

  function draw(): void {
    const query = normalize(search.value);
    let matches = 0;
    for (const entry of rows) {
      const { row } = entry;
      const visible = entry.search.includes(query)
        && (!slot?.value || row.dataset.slot === slot.value)
        && (!fuse?.checked || row.dataset.fuse === "3");
      row.hidden = !visible;
      if (visible) matches += 1;
    }
    tableWrap.hidden = matches === 0;
    const noun = slot ? "items" : "floor bands";
    count.textContent = matches ? `${matches} of ${rows.length} ${noun}` : `No matching ${noun}.`;
  }

  search.addEventListener("input", draw);
  slot?.addEventListener("change", draw);
  fuse?.addEventListener("change", draw);
  draw();
}

export function renderGuides(app: HTMLElement, id?: string): void {
  const article = DATA.guides.articles.find((entry) => entry.id === id);
  document.title = `${article?.title ?? "Guides"} — Yog Guide`;
  if (!article) {
    app.innerHTML = articleList();
    return;
  }

  app.innerHTML = `
    <article class="guide-article">
      <p class="guide-back"><a href="#/guides">All guides</a></p>
      <h1>${esc(article.title)}</h1>
      <p class="lead">${esc(article.summary)}</p>
      ${article.sections.map((section) => `
        <section>
          <h2>${esc(section.title)}</h2>
          <ul>${section.items.map((item) => `<li>${item.map((part) => name(part)).join("")}</li>`).join("")}</ul>
          ${section.screenshots?.map(screenshot).join("") ?? ""}
        </section>`).join("")}
      ${article.id === "gear-to-lock" ? keepTable() : ""}
      ${article.id === "stages-and-farming" ? deepMistTable() : ""}
      ${article.id === "teams-and-pvp" ? '<p><a href="#/factions">Fronts reference</a> · <a href="#/tiers">PvE tier list</a></p>' : ""}
      ${sourceLinks(article)}
    </article>`;
  bindTableFilters(app);
}
