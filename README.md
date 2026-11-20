# Yog Guide — Book of Yog build reference in English

**Website: <https://saxap123.github.io/yog-guide/>**

An English reference for **Book of Yog Idle RPG** (依盖之书): how to build every Blackguard (gear by
level, affixes, black stones 黑石, relics, runes), skills and blood ranks, the PvE tier list, and the
gear, relic, rune, black stone and front (阵线) lists.

- Search characters in English or Chinese; filter by element, rarity, front, PvE tier.
- Each build is shown as a paper doll — hover or tap a slot for the item, its effects and alternatives.
- Every line says where its English comes from: **official** (the game's own English), **translated**
  (our translation of the wiki), **wiki** (wiki data as written). Empty fields say «No data yet».
- PvP is not covered.

## Sources

- **BWIKI 依盖之书** — <https://wiki.biligame.com/bookofyog/> — all builds, tier lists and item data.
  Each record links to the exact wiki revision it comes from.
- **Official English names and texts** — from the game's own files (snapshot of 2026-09-22), used only
  where the wiki text and the game text match.
- What changed in each update: [data/CHANGELOG.md](data/CHANGELOG.md).

Something wrong or out of date? The wiki is the source: fix it there, and it will reach this guide with
the next update. Problems with the English: open an issue.

## Thanks

- **赧然丶 and the contributors of BWIKI 依盖之书**, who wrote and keep up the wiki this guide is built from.
- **Tebo**, for the [Book of Yog Guide](https://docs.google.com/spreadsheets/d/1dbjnqiQCUUlVBFMo5sSQAmQD0bFdh-_w3sEwGRBke5o).

## Licence

- Data (`data/en`, `data/names.json`, `data/glossary.json` and the other wiki-derived files):
  **CC BY-NC-SA 4.0**, adapted from BWIKI 依盖之书 (赧然丶 and contributors) — see [LICENSE-DATA.md](LICENSE-DATA.md).
- Code: **MIT** — see [LICENSE](LICENSE).
- **Game art © HangZhou QiHeShe Technology.** Game names and texts © HangZhou QiHeShe Technology.
  Unofficial fan project, not affiliated with the developer or with bilibili.

## For developers

How the data is downloaded, parsed, translated and built, and how to update the site
(`python -m yog update`): [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
