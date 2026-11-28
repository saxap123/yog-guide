/** Resolve guide terms and cross-links using the same source data as the catalog. */
import fs from "node:fs";
import path from "node:path";
import type { GuideArticle, GuideData, GuideName } from "../src/guide-data.ts";

interface NameEntry {
  en?: string | null;
}

interface CatalogEntry {
  id?: string;
  name?: string | null;
  name_zh?: string;
}

interface GuideSource {
  guides: (Omit<GuideArticle, "sections" | "sources"> & {
    sections: { title: string; items: string[] }[];
    sources: string[];
  })[];
  wiki: Record<string, Omit<GuideArticle["sources"][number], "title">>;
  keep: { name: string; slot: string; fuse?: number }[];
  deepMist: { floors: string; stones: string[] }[];
}

interface Catalogs {
  gear: CatalogEntry[];
  characters: CatalogEntry[];
  factions: CatalogEntry[];
  stones: CatalogEntry[];
}

type NamedKind = "gear" | "characters" | "factions" | "black_stones";
type NamedTable = Record<NamedKind, Record<string, NameEntry>>;

export function prepareGuides(
  root: string, gloss: Record<string, NameEntry>, names: NamedTable, catalogs: Catalogs,
): GuideData {
  const source: GuideSource = JSON.parse(fs.readFileSync(path.join(root, "translate/manual/guides.json"), "utf8"));
  const { stones, ...namedCatalogs } = catalogs;
  const catalog: Record<NamedKind, CatalogEntry[]> = { ...namedCatalogs, black_stones: stones };
  const routes: Record<NamedKind, string> = {
    gear: "gear", characters: "c", factions: "factions", black_stones: "stones",
  };
  const wikiUrl = (title: string) => "https://wiki.biligame.com/bookofyog/" + encodeURIComponent(title);

  function named(kind: NamedKind, title: string): GuideName {
    const en = names[kind][title]?.en ?? undefined;
    const exact = catalog[kind].filter((row) => row.name_zh === title);
    const byName = en && exact.length === 0 ? catalog[kind].filter((row) => row.name === en) : [];
    const matches = exact.length ? exact : byName;
    const match = matches.length === 1 ? matches[0] : undefined;
    const english = match?.name ?? en;
    return {
      text: english ?? title,
      zh: title,
      href: match?.id ? `#/${routes[kind]}/${encodeURIComponent(match.id)}` : wikiUrl(title),
    };
  }

  function glossaryTerm(title: string): string {
    const en = gloss[title]?.en;
    if (!en) throw new Error(`Guide term missing from the glossary: ${title}`);
    return en;
  }

  function paragraph(text: string): GuideName[] {
    const tokens = text.split(/\[\[([tcfg]):([^\]]+)\]\]/g);
    const kinds = { c: "characters", f: "factions", g: "gear" } as const;
    const parts: GuideName[] = [{ text: tokens[0] }];
    for (let i = 1; i < tokens.length; i += 3) {
      const token = tokens[i] as "t" | keyof typeof kinds;
      const title = tokens[i + 1];
      parts.push(token === "t" ? { text: glossaryTerm(title) } : named(kinds[token], title));
      parts.push({ text: tokens[i + 2] });
    }
    return parts.filter((part) => part.text);
  }

  return {
    articles: source.guides.map((guide) => ({
      ...guide,
      sections: guide.sections.map(({ title, items }) => ({ title, items: items.map(paragraph) })),
      sources: guide.sources.map((title) => {
        const reference = source.wiki[title];
        if (!reference?.revid) throw new Error(`Missing wiki revision for guide source: ${title}`);
        return { title, ...reference };
      }),
    })),
    keep: source.keep.map(({ name, slot, fuse }) => ({
      name: named("gear", name), slot: glossaryTerm(slot), fuse,
    })),
    deepMist: source.deepMist.map(({ floors, stones }) => ({
      floors, stones: stones.map((name) => named("black_stones", name)),
    })),
  };
}
