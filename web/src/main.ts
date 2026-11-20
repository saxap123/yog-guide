import "./style.css";
import { badgeOf, initTooltip } from "./ui.ts";
import { renderCard } from "./views/card.ts";
import { renderList } from "./views/list.ts";
import { renderRef, type Kind } from "./views/refs.ts";
import { renderTiers } from "./views/tiers.ts";

const app = document.getElementById("app")!;
const REFS: Kind[] = ["gear", "relics", "runes", "stones", "factions"];

function route() {
  const parts = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  const [head, id] = parts;
  let nav = "chars";
  if (head === "c" && id) {
    renderCard(app, id);
  } else if (head === "tiers") {
    nav = "tiers";
    renderTiers(app);
  } else if ((REFS as string[]).includes(head)) {
    nav = head;
    renderRef(app, head as Kind, id);
  } else {
    renderList(app);
    document.title = "Yog Guide — Book of Yog build reference";
  }
  document.querySelectorAll<HTMLAnchorElement>("#nav a").forEach((a) => a.classList.toggle("on", a.dataset.nav === nav));
  if (!(REFS as string[]).includes(head) || !id) window.scrollTo(0, 0);
}

document.getElementById("legend")!.innerHTML = `
  <h2>Sources</h2>
  <ul class="legend-list">
    <li>${badgeOf("o")} English from the game files (official names and texts)</li>
    <li>${badgeOf("t")} our translation of the wiki text</li>
    <li>${badgeOf("w")} wiki data as written (numbers, levels, dates)</li>
    <li><span class="disc">≠ game</span> the game text has other numbers than the wiki (hover for both)</li>
    <li><span class="uo">Name<sup class="uo-tag">unofficial name</sup></span> no official English; our translation, Chinese in the tooltip</li>
    <li><span class="nodata">No data yet</span> empty on the wiki or no English yet</li>
  </ul>`;

initTooltip();
window.addEventListener("hashchange", route);
route();
