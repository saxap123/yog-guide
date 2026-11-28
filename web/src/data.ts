// Site data: generated at build time by scripts/prepare-data.ts from ../data/en (embedded, no fetches).
import raw from "./generated/data.json";
import type { GuideData } from "./guide-data.ts";

export type Origin = "o" | "t" | "w";

export interface Annot {
  src: Record<string, Origin>;
  miss: Record<string, { zh: string; reason: string }>;
  uo: Record<string, { zh: string; en: string; note: string; kind: string }[]>;
  disc: Record<string, { wiki: string[]; game: string[]; text_id: number }>;
}

/** Any record of the site (character, gear, relic …): plain JSON plus provenance in `_a`. */
export interface Rec {
  id?: string;
  name: string | null;
  name_zh: string;
  source_url?: string;
  permalink?: string;
  revid?: number;
  _a: Annot;
  [k: string]: any; // eslint-disable-line @typescript-eslint/no-explicit-any
}

interface Data {
  characters: Rec[];
  gear: Rec[];
  gear_note: string;
  relics: Rec[];
  runes: Rec[];
  stones: Rec[];
  factions: Rec[];
  tiers: Rec[];
  pve_sections: Record<string, string | null>;
  guides: GuideData;
}

export const DATA = raw as unknown as Data;

const index = (xs: Rec[]) => new Map(xs.filter((x) => x.id).map((x) => [x.id as string, x]));
export const CHAR = index(DATA.characters);
export const GEAR = index(DATA.gear);
export const RELIC = index(DATA.relics);
export const RUNE = index(DATA.runes);
export const STONE = index(DATA.stones);
export const FACTION = index(DATA.factions);

/** PvE tier entry per character id (PvP is not shown). */
export const PVE = new Map(DATA.tiers.map((t) => [t.character_id as string, t]));
export const PVE_AS_OF = DATA.tiers[0]?.as_of as string | undefined;
export const PVE_SOURCE = DATA.tiers[0]?.permalink as string | undefined;

export const TIER_ORDER = [...new Set(DATA.tiers.map((t) => t.tier as string))]
  .sort((a, b) => (a === "not_ranked" ? Infinity : Number(a.slice(1))) - (b === "not_ranked" ? Infinity : Number(b.slice(1))));
export const tierRank = (t: string | undefined) => {
  const i = TIER_ORDER.indexOf(t ?? "not_ranked");
  return i < 0 ? TIER_ORDER.length : i;
};

/** Which characters' builds use a gear item (from the build slot links). */
export const GEAR_USED_BY = new Map<string, Set<string>>();
for (const c of DATA.characters) {
  for (const b of c.builds ?? []) {
    const lists: (string | null)[][] = [
      ...Object.values<(string | null)[]>(b.slot_ids ?? {}),
      ...Object.values<(string | null)[][]>(b.alt_ids ?? {}).flat(),
      ...Object.values<(string | null)[]>(b.ext_ids ?? {}),
      b.sw_ids ?? [],
    ];
    for (const id of lists.flat()) {
      if (id) (GEAR_USED_BY.get(id) ?? GEAR_USED_BY.set(id, new Set()).get(id)!).add(c.id as string);
    }
  }
}

/** Value at "a.b[2].c". */
export function at(rec: unknown, path: string): any { // eslint-disable-line @typescript-eslint/no-explicit-any
  let o: any = rec; // eslint-disable-line @typescript-eslint/no-explicit-any
  for (const part of path.match(/[^.[\]]+|\[\d+\]/g) ?? []) {
    if (o == null) return undefined;
    o = part.startsWith("[") ? o[Number(part.slice(1, -1))] : o[part];
  }
  return o;
}
