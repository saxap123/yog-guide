// "Paper doll" view of one build, laid out like the wiki template 模板:黑卫配装:
// left column 头盔 卡牌 衣服 腰带 裤子 鞋子 武器, right column 项链 耳坠 戒指 圣物 徽章 副手 护手,
// the character in the middle; extracts (萃取) and the signature weapon (专武) next to their slot.
// Hover or click on a slot opens an item card (effects + source marks, alternatives, extract).
import { GEAR, type Rec } from "../data.ts";
import { badge, esc, has, itemIcon, noData, portrait, richText, val, zh } from "../ui.ts";

export const LEFT = ["Helmet", "Card", "Armor", "Belt", "Trousers", "Shoes", "Weapon"];
export const RIGHT = ["Necklace", "Earrings", "Ring", "Relic", "Emblem", "Off-hand", "Handguard"];
const SIGNATURE = "Signature weapon";

type Ids = (string | null)[] | undefined;
const linked = (ids: Ids): string[] | null => (ids && ids.length && ids.every(Boolean) ? (ids as string[]) : null);

/** Label inside a slot button: plain text (no focusable children inside a button). */
function slotLabel(value: string | null, ids: Ids): string {
  if (!value) return `<span class="nodata">No data yet</span>`;
  const ok = linked(ids);
  if (ok && ok.length > 1) return ok.map((id) => esc(GEAR.get(id)?.name ?? "?")).join(" / ");
  return esc(value);
}

function slotButton(b: Rec, bi: number, key: string, side: "l" | "r"): string {
  const isSig = key === SIGNATURE;
  const value: string | null = isSig ? b.signature_weapon : b.slots?.[key] ?? null;
  const ids: Ids = isSig ? b.sw_ids : b.slot_ids?.[key];
  const first = linked(ids)?.[0];
  const g = first ? GEAR.get(first) : undefined;
  const iconLabel = isSig ? "Weapon" : key;
  const alts = isSig ? 0 : (b.alternatives?.[key] ?? []).length;
  const ext = isSig ? null : b.extracts?.[key];
  const more = [alts ? `+${alts} alternative${alts > 1 ? "s" : ""}` : "", ext ? "+ extract" : ""].filter(Boolean);
  return `<button type="button" class="dslot dslot-${side}${value ? "" : " dslot-empty"}" data-bi="${bi}" data-slot="${esc(key)}" aria-haspopup="dialog">
    ${itemIcon(g ?? null, iconLabel, "lg")}
    <span class="dslot-txt"><span class="dslot-slot">${esc(key)}</span><span class="dslot-name">${slotLabel(value, ids)}</span>${
      more.length ? `<span class="dslot-more">${more.join(" · ")}</span>` : ""
    }</span></button>`;
}

export function dollHtml(c: Rec, b: Rec, bi: number): string {
  const left = [...LEFT];
  if (b.signature_weapon) left.push(SIGNATURE);
  return `<div class="doll" data-bi="${bi}">
    <div class="doll-col doll-left">${left.map((k) => slotButton(b, bi, k, "l")).join("")}</div>
    <div class="doll-center">${portrait(c)}<div class="doll-name">${c.name ? esc(c.name) : esc(c.name_zh)}</div>
      <div class="muted small">${b.level_tier ? esc(b.level_tier) : ""}</div></div>
    <div class="doll-col doll-right">${RIGHT.map((k) => slotButton(b, bi, k, "r")).join("")}</div>
  </div>`;
}

// ---- item card ---------------------------------------------------------------------------------
function effects(g: Rec): string {
  const rows: string[] = [];
  rows.push(`<div class="pi-fx"><span class="k">Skill</span> ${val(g, "skill", { nl: true })} ${has(g.skill) ? badge(g, "skill") : ""}</div>`);
  if (g.set?.bonuses?.length) {
    rows.push(`<div class="pi-fx"><span class="k">Set ${val(g, "set.name")}</span><ul class="plain">${g.set.bonuses
      .map((x: Rec, i: number) => `<li><span class="pieces">${esc(x.pieces)}-piece</span> ${val(g, `set.bonuses[${i}].text`)} ${badge(g, `set.bonuses[${i}].text`)}</li>`)
      .join("")}</ul></div>`);
  }
  if ((g.exclusive ?? []).length) {
    rows.push(`<div class="pi-fx"><span class="k">Exclusive</span> ${(g.exclusive as string[])
      .map((_, i) => `${val(g, `exclusive[${i}]`)} ${badge(g, `exclusive[${i}]`)}`)
      .join("; ")}</div>`);
  }
  return rows.join("");
}

function itemBlock(c: Rec, value: string | null, ids: Ids, path: string, slot: string): string {
  if (!value) return `<div class="pi">${itemIcon(null, slot, "md")}<div class="pi-body">${noData(c, path)}</div></div>`;
  const ok = linked(ids);
  if (!ok) {
    return `<div class="pi">${itemIcon(null, slot, "md")}<div class="pi-body">
      <div class="pi-name">${richText(c, path, value)} ${badge(c, path)}</div>
      <div class="muted small">No item page (see data/en/REPORT.md)</div>
      <div class="pi-fx"><span class="k">Effects</span> ${noData(c, path)}</div></div></div>`;
  }
  return ok
    .map((id) => {
      const g = GEAR.get(id)!;
      const name = ok.length === 1 ? richText(c, path, value) : esc(g.name ?? g.name_zh);
      const meta = [g.slot, g.quality, g.source === "game_db" ? "game files (no wiki page)" : ""].filter(Boolean).map(esc).join(" · ");
      return `<div class="pi">${itemIcon(g, slot, "md")}<div class="pi-body">
        <div class="pi-name"><a href="#/gear/${esc(id)}">${name}</a> ${badge(c, path)} ${zh(g.name_zh)}</div>
        ${meta ? `<div class="muted small">${meta}</div>` : ""}${effects(g)}</div></div>`;
    })
    .join("");
}

export function itemCardHtml(c: Rec, b: Rec, bi: number, key: string): string {
  const base = `builds[${bi}]`;
  if (key === SIGNATURE) {
    return `<div class="pop-head">Signature weapon</div>${itemBlock(c, b.signature_weapon, b.sw_ids, `${base}.signature_weapon`, "Weapon")}`;
  }
  const parts = [`<div class="pop-head">${esc(key)}${b.level_tier ? ` · ${esc(b.level_tier)}` : ""}</div>`];
  parts.push(itemBlock(c, b.slots?.[key] ?? null, b.slot_ids?.[key], `${base}.slots.${key}`, key));
  if (b.extracts?.[key]) {
    parts.push(`<h5>Extract</h5>`, itemBlock(c, b.extracts[key], b.ext_ids?.[key], `${base}.extracts.${key}`, key));
  }
  const alts: string[] = b.alternatives?.[key] ?? [];
  if (alts.length) {
    parts.push(`<h5>Alternatives</h5>`, ...alts.map((v, i) => itemBlock(c, v, b.alt_ids?.[key]?.[i], `${base}.alternatives.${key}[${i}]`, key)));
  }
  return parts.join("");
}

// ---- popover behaviour: hover (mouse), click/tap or Enter pins it; Esc / outside click closes --
export function initDoll(root: HTMLElement, c: Rec) {
  let pop = document.getElementById("pop");
  if (!pop) {
    pop = document.createElement("div");
    pop.id = "pop";
    pop.setAttribute("role", "dialog");
    pop.hidden = true;
    document.body.appendChild(pop);
  }
  const P = pop;
  let owner: HTMLElement | null = null;
  let pinned = false;
  let timer = 0;

  const place = (btn: HTMLElement) => {
    if (window.innerWidth < 700) {
      P.classList.add("pop-sheet");
      P.style.left = P.style.top = "";
      return;
    }
    P.classList.remove("pop-sheet");
    const r = btn.getBoundingClientRect();
    const w = P.offsetWidth;
    const right = btn.classList.contains("dslot-l");
    let left = right ? r.right + 8 : r.left - w - 8;
    left = Math.max(8, Math.min(left, window.innerWidth - w - 8));
    let top = r.top;
    top = Math.max(8, Math.min(top, window.innerHeight - P.offsetHeight - 8));
    P.style.left = `${left + window.scrollX}px`;
    P.style.top = `${top + window.scrollY}px`;
  };
  const open = (btn: HTMLElement, pin: boolean) => {
    window.clearTimeout(timer);
    const bi = Number(btn.dataset.bi);
    const b = c.builds[bi];
    P.innerHTML = itemCardHtml(c, b, bi, btn.dataset.slot!);
    P.setAttribute("aria-label", `${btn.dataset.slot} item`);
    P.hidden = false;
    owner?.classList.remove("on");
    owner = btn;
    btn.classList.add("on");
    btn.setAttribute("aria-expanded", "true");
    pinned = pin;
    place(btn);
  };
  const close = () => {
    window.clearTimeout(timer);
    P.hidden = true;
    owner?.classList.remove("on");
    owner?.setAttribute("aria-expanded", "false");
    owner = null;
    pinned = false;
  };
  const later = () => {
    window.clearTimeout(timer);
    timer = window.setTimeout(() => !pinned && close(), 200);
  };

  root.querySelectorAll<HTMLElement>(".dslot").forEach((btn) => {
    btn.addEventListener("pointerenter", (e) => {
      if (e.pointerType === "mouse" && !pinned) open(btn, false);
    });
    btn.addEventListener("pointerleave", (e) => e.pointerType === "mouse" && later());
    btn.addEventListener("click", () => {
      if (owner === btn && pinned) close();
      else open(btn, true);
    });
  });
  P.onpointerenter = () => window.clearTimeout(timer);
  P.onpointerleave = (e) => e.pointerType === "mouse" && later();
  const onDoc = (e: Event) => {
    if (!owner) return;
    const t = e.target as Node;
    if (!P.contains(t) && !owner.contains(t)) close();
  };
  const onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape" && owner) {
      const o = owner;
      close();
      o.focus();
    }
  };
  document.addEventListener("click", onDoc);
  document.addEventListener("keydown", onKey);
  const cleanup = () => {
    close();
    document.removeEventListener("click", onDoc);
    document.removeEventListener("keydown", onKey);
    window.removeEventListener("hashchange", cleanup);
  };
  window.addEventListener("hashchange", cleanup);
  return close;
}
