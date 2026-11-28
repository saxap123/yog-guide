export interface GuideName {
  text: string;
  zh?: string;
  href?: string;
  icon?: { kind: "gear" | "characters" | "black_stones"; id: string };
}

export interface GuideScreenshot {
  title: string;
  alt: string;
  width: number;
  height: number;
  src: string;
  source: string;
  notes: GuideName[][];
}

export interface GuideArticle {
  id: string;
  title: string;
  summary: string;
  sections: { title: string; items: GuideName[][]; screenshots?: GuideScreenshot[] }[];
  sources: { title: string; label: string; revid: number; date: string; interactive?: boolean; author?: string }[];
  officialAnnouncements?: boolean;
}

export interface GuideData {
  articles: GuideArticle[];
  keep: { name: GuideName; slot: string; fuse?: number }[];
  deepMist: { floors: string; stones: GuideName[] }[];
}
