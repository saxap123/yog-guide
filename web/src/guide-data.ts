export interface GuideName {
  text: string;
  zh?: string;
  href?: string;
}

export interface GuideArticle {
  id: string;
  title: string;
  summary: string;
  sections: { title: string; items: GuideName[][] }[];
  sources: { title: string; label: string; revid: number; date: string; interactive?: boolean }[];
  officialAnnouncements?: boolean;
}

export interface GuideData {
  articles: GuideArticle[];
  keep: { name: GuideName; slot: string; fuse?: number }[];
  deepMist: { floors: string; stones: GuideName[] }[];
}
