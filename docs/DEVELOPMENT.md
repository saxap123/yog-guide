# yog-guide — developer notes

Local English build reference for **Book of Yog Idle RPG** (依盖之书).
Works fully offline on local data once downloaded.

## Data source and license

All game data comes from the community wiki **BWIKI — 依盖之书**:
<https://wiki.biligame.com/bookofyog/>, licensed **CC BY-NC-SA 4.0**.

- Every record keeps `source_url`, `fetched_at` and (for wikitext) `permalink` to the exact revision.
- Non-commercial use only; derived data is shared under the same license.
- Game files are never modified (the game uses EasyAntiCheat). A local snapshot of the unpacked
  game database (2026-09-22, `data/raw/game_db/`, git-ignored) is **read** in step 3 for official
  English names and texts; only the strings actually used end up in the repository.

## Layout

```
yog-guide/
  yog/                python -m yog update (step 5: the whole pipeline in one command)
  scraper/
    fetch.py          download everything (steps 1 + 1b), resumable, incremental
    completeness.py   首页 / PVE·PVP节奏榜 vs Category:黑卫 (called by fetch.py)
    inventory.py      lists templates, parameters, SMW properties; writes REPORT.md
    resolve_missing.py  step 2b: wiki lookup (titles+redirects, then search) of unlinked build items/runes
  parse_zh/
    build.py          step 2: data/raw -> data/zh (Chinese JSON), writes data/zh/REPORT.md
    textutil.py       markup -> text, list splitting, placeholders, skill scaling
    report.py         REPORT.md writer
    gamedb.py         read-only lookups in the unpacked game DB (ids only)
  docs/GAMEDB.md      what is in data/raw/game_db/08.database (for step 3)
  docs/DEVELOPMENT.md this file
  schema/             JSON Schemas (draft 2020-12) of the data/zh records
  translate/          step 3 (reads data/zh + the local game snapshot, writes data/en)
    gamedict.py       read-only loader of the game tables and dictionary; numbers()
    textmatch.py      wiki text vs game template ({0}) alignment, number-checked
    build_names.py    -> data/names.json
    build_glossary.py -> data/glossary.json (manual/glossary.json: terms without a game entry)
    build_en.py       -> data/en (manual/texts/*.json: our translations of wiki texts)
    check_numbers.py  every number of a zh string must be in its en string
    check_chunk.py    the same check for one translation file
    write_report.py   -> data/en/REPORT.md
    unofficial.py     step 4: names left in Chinese -> manual/unofficial_names.json (called by build_en.py)
  tests/
    test_retry.py     retry/backoff unit tests (no network)
    test_parse.py     schema validation of data/zh, links, SMW cross-check, manual page checks
    test_translate.py data/en vs data/zh (numbers, structure), names/glossary, game-only gear, .gitignore
  data/raw/
    manifest.json        group/title -> revid, file, fetched_at; SMW entries; failed list
    categories/*.json    member lists of 黑卫, 装备, 遗物, 符文, 阵线
    characters/          Category:黑卫 pages (wikitext)
    gear/                Category:装备 pages
    relics/              Category:遗物 pages
    runes/               Category:符文 pages
    factions/            Category:阵线 pages
    black_stones/        黑石, 黑石强化, 模板:推荐黑石 (there is no 黑石 category)
    pages/               PVE节奏榜, PVP节奏榜, 装备, 黑石, 符文, 遗物, 阵线, 天赋推荐, 黑话解读, 首页
    templates/           templates transcluded by character pages
    smw/<group>/*.json   raw action=browsebysubject answer for every page of the groups above
    rendered/首页.json    action=parse of the main page (its tiles come from an SMW query)
    template_usage.json, completeness.json, inventory.json, REPORT.md, fetch*.log
    missing_lookup.json  step 2b: API answers for every unlinked name
    extra_items/         pages found by step 2b (wikitext; SMW in smw/extra_items)
    game_db/08.database/ unpacked game files — local, read-only, git-ignored (not downloaded)
  data/names.json             zh name -> official English name (game_db) or null (unverified)
  data/glossary.json          zh term -> English (game_db exact match, else translated)
  data/en/                    English mirror of data/zh (characters/<id>.json, gear.json …, REPORT.md)
  data/zh/
    characters/<title>.json   one record per Category:黑卫 page
    gear.json, relics.json, runes.json, black_stones.json, factions.json, tiers.json
    REPORT.md                 empty fields per character, unlinked build items, parse problems
```

Wikitext file fields: `title, pageid, ns, revid, rev_timestamp, wikitext, templates,
source_url, permalink, fetched_at, group, license`.
SMW file fields: `subject, group, page_revid, source_url, api_request, fetched_at, response`.
File names are the page title with `<>:"/\|?*` replaced by `_` (the real title is
inside the file and in `manifest.json`).

## Running

Requires Python 3.10+ and `requests`.

```bash
cd yog-guide
python scraper/fetch.py
python scraper/inventory.py
python -m unittest discover -s tests -v
```

- Timeout 30 s, up to 5 retries with 2/4/8/16/32 s backoff (network errors,
  HTTP 429/5xx, invalid JSON, API `maxlag`/`ratelimited`), 1–2 s random pause
  between requests, descriptive User-Agent, `maxlag=5`. Wikitext is fetched 50
  pages per request; SMW data one page per request (~450 requests, ~15 min).
- Progress is saved after every page/batch. After an interruption just run it
  again. Pages with an unchanged revid are skipped (a no-change run is ~21 requests).
  `--force` re-downloads everything.
- SMW data is re-fetched only when the page revid changes. If a *template*
  changes, the wiki can re-store SMW values without a new page revid — use
  `--force` after template edits on the wiki. `rendered/首页` is fetched every run.
- Characters linked from 首页 or the tier lists but missing from Category:黑卫
  are downloaded automatically into `characters/` with `"in_category_黑卫": false`.
- Exit code 1 means some pages failed; they are listed in `manifest.json → failed`
  and in `REPORT.md`.

## Step 2: parsing (Chinese JSON, no translation)

Requires `mwparserfromhell` and `jsonschema` (`pip install mwparserfromhell jsonschema`;
without a C compiler use `WITHOUT_EXTENSION=1 pip install mwparserfromhell` — the
pure-Python parser gives the same result). Works offline on `data/raw` only.

```bash
python parse_zh/build.py
python -m unittest discover -s tests -v
```

- Collections (`gear.json`, …) are `{kind, license, source, count, items}`; the item
  schema is in `schema/<kind>.schema.json`. Characters are one file each.
- Ids: `char-/gear-/relic-/rune-/faction-<pageid>`, `black_stone-NN` (order on page 黑石).
- Every record has `source_url`, `revid`, `permalink`. Missing data is `null`;
  wiki placeholder text, `无` and `暂无` become `null` (see `data/zh/REPORT.md`).
- Build item names are linked to `gear.json` by exact name (then NFKC / middle-dot
  normalisation); a full-width `，` inside a slot separates variants. Unmatched names stay
  `null` in `item_ids`; `builds[].unlinked[name]` gives `reason` (`game_only`,
  `typo_candidate`, `not_an_item`, `nowhere`), `game_id`, and a `possible_match` marked
  `unverified` (typos are never corrected or linked).
- `builds[].tier_kind` = `level` (+ `level`, `levels`, `qualifier`) or `special`
  (+ `tier_note`, a short English explanation); `level_tier` keeps the label as written.
- Step 2b (`python scraper/resolve_missing.py`, network, ~115 requests) refreshes
  `data/raw/missing_lookup.json` and `extra_items/`; run `parse_zh/build.py` afterwards.
- If `data/raw/game_db/08.database` (or `data/raw/GameDB/08.database`) exists, unlinked
  names are also looked up there; without it `game_id` is `null`. See `docs/GAMEDB.md`.

## Notes for the parsing step

- Gear builds of a character (`黑卫配装`) are passed as `{{#arraydefine:…}}`, which
  stores an empty value in SMW — slot items exist **only in the wikitext**, not in
  `smw/characters`. Each character may have several `黑卫配装` calls; on 千宵月守
  they are level tabs `450/700级` and `1000级` (tab labels are plain HTML before the call).
- 黑石 has no pages or SMW properties of its own: the 2/4/8-piece effects of the
  18 stones are hard-coded in `黑石` (HTML tabs) and in `模板:推荐黑石`.
- Many character fields hold wiki placeholder text (`立绘1`, `事迹1`, `10级好感度答案`).
- Not downloaded: images (e.g. `天赋推荐` is mostly `天赋说明.png`), templates
  used only by overview/item pages.

## Step 3: English names, glossary, translation

Needs the local game snapshot in `data/raw/game_db/08.database` (read-only; not in git).

```bash
python translate/build_names.py
python translate/build_glossary.py
python translate/build_en.py
python translate/check_numbers.py      # exit 1 on any zh/en number mismatch
python translate/write_report.py             # data/en/REPORT.md
python -m unittest discover -s tests -v
```

- **Names** (`data/names.json`): characters, skills, gear, relics, runes, 黑石, 阵线. Chinese
  name → game table row (`title_id` / `name_id`) → dictionary English, `source: "game_db"`,
  `game_id`, `text_id`. Not found → `en: null`, `status: "unverified"` (+ `possible_match`,
  never applied). Alias: 璨然银龙 is 燦然银龙 in the game. Black stones drop the game's
  `Gem·` prefix (kept in `en_game`); factions are the game's `X阵线` rows ("Resonance Front").
- **Glossary** (`data/glossary.json`): stats, affixes, statuses, slots, qualities, elements,
  resources (怒气, 源力), sources … English by exact Chinese match in the game dictionary;
  otherwise our translation (`source: "translated"`, `translate/manual/glossary.json`).
- **data/en**: same structure as data/zh, plus `i18n` per record (`name_zh`, counts per
  source, `text_sources` for long texts, `missing`, `untranslated_lore`). Sources:
  `names`, `glossary`, `game_db` (official English, used only when the wiki text is the game
  text of that skill/effect with values filled in and all numbers agree; punctuation and doubled
  characters ignored, any other wording difference is not), `derived` (dates → ISO
  `2026-09-21` / `--04-08`, `500%法术强度的火焰伤害` → "Fire DMG equal to 500% of Spell Power"),
  `translated` (wiki text translated with the glossary; `translate/manual/texts/`), `lore`
  (story, deeds, affection, item flavour text — kept in Chinese). No source → `null`, listed in
  `i18n.missing`.
- `builds[].item_ids`, `unlinked`, `placeholders_nulled`, `parse_notes` and page titles stay in
  Chinese: they are ids / provenance, not text.
- 99 build items exist only in the game: appended to `data/en/gear.json` with `source:
  "game_db"`, id `gear-game-<game id>`, slot, quality (when fixed in the table), skill text
  from the item's skill affixes, `used_in`; builds link to them via `item_ids`.
- `translate/work/` (todo list, rejected game texts) is git-ignored: it quotes game texts that
  are not used.

## Step 4: the site (`web/`)

Static site, Vite + TypeScript, no server and no runtime requests: `web/scripts/prepare-data.ts` reads
`data/en` (+ `data/zh`, `names.json`, `glossary.json`, `translate/manual`) and writes
`web/src/generated/data.json`, which is bundled into the JS.

```bash
cd web
npm install
npm run build      # data + images (IMAGES=icons) + tsc + vite build -> web/dist
npm run preview    # http://localhost:4173
```

- Screens: characters (search EN/CN; filters element, rarity, front, PvE tier), character page («How to
  build»: main stat from skill scaling, affixes by priority, builds by level as tabs, 黑石, relic, runes;
  then skills and 血阶), references (gear, relics, runes, 黑石, 阵线), PvE tier list with its date.
  PvP is not shown (PvP tier list and builds labelled PVP).
- Every row has a source mark: **official** (English from the game files), **translated** (our
  translation), **wiki** (wiki data as written / rendered mechanically). Paths without a mark in the
  data step are `wiki`. `≠ game`: the game text has the same wording but other numbers
  (`data/en/discrepancies.json`, numbers only). Empty fields: «No data yet» (tooltip: Chinese + reason).
- Unofficial names: 59 names that had no official English and stayed in Chinese inside 102 English
  strings are translated in `translate/manual/unofficial_names.json` (people/places romanized, wiki
  typos translated as written, never corrected); the site marks them «unofficial name».
- Images (step 4b): `web/scripts/prepare-images.ts` reads (only reads) `data/raw/game_db/03.ui/image_ab/`
  (`heroicons`, `01.icon`; or the folder in `YOG_IMAGE_SRC`), matches them to the data — characters by
  `tpl_sc_hero` id (`icon_portrait` / id / `avatarID`), gear / relics / runes / 黑石 by game id → `iconID` —
  and writes WebP to `web/public/img/` (git-ignored, generated per build) + `src/generated/images.json`;
  unmatched records go to `docs/IMAGES_REPORT.md`.
  `npm run build` = `IMAGES=icons` (avatars 96 px, item icons 96 px); `npm run build:full` (+ portraits
  512 px on the character page — local builds only); `npm run build:none` (no game images). The `IMAGES`
  environment variable works too (PowerShell: `$env:IMAGES="full"; npm run build`).
  Missing image → placeholder: first letter of the name (characters) or the item's slot (items).
  Characters: avatar = `heroicons/square_<id>` (head crop, cut square from the centre); portrait =
  `portrait_<id>` or the largest (bytes) of its layer files `portrait_<id>_0..3` (the others are effect
  layers); `circular_<id>` is a framed card (avatar fallback only). Icons: exact `iconID`, else its largest
  size variant (`item_blackStone11` → `item_blackStone11_128.png`).
  Icon frames: the game's quality plate + border from `01.title` (`ui_common_物品品质底板.png`,
  `ui_common_物品品质边框.png`; strips in grade order — Epic 3, Legend 4, Mythic 6, Eternal 7, Archaic 8,
  Archaic placed by order only). Without a frame (IMAGES=none, items without a quality) a CSS frame is used.
- Builds are shown as a paper doll laid out like the wiki template 黑卫配装 (left: helmet, card, armour,
  belt, trousers, shoes, weapon; right: necklace, earrings, ring, relic, emblem, off-hand, handguard); hover
  or click a slot for the item card (effects, source marks, alternatives, extract). The build table is below,
  collapsed.

## Step 5: publishing and updates

```bash
python -m yog update            # fetch changed pages -> parse -> translate -> check -> tests -> site build
python -m yog update --deploy   # the same, then publish web/dist to GitHub Pages
```

- `yog/update.py` runs the steps above in order and stops at the first failure (number check, tests).
  Options: `--offline` (no network, use `data/raw` as it is), `--rebuild` (continue although no wiki page
  has a new revid), `--no-build`, `--deploy`. With no new revid and no option it changes nothing.
- Translation: `translate/manual/texts/*.json` is keyed by the Chinese text, so only new or changed wiki
  strings are left untranslated; they are listed in `translate/work/todo.json` and shown on the site as
  «No data yet». Add them to a new `translate/manual/texts/chunkN.json`, check it with
  `python translate/check_chunk.py`, then `python -m yog update --offline --rebuild`.
- New names without English (`en: null` in `data/names.json`) and Chinese names left inside English strings
  (missing from `translate/manual/unofficial_names.json`) are printed at the end.
- `data/CHANGELOG.md` gets an entry per finished update: records added / changed (top-level fields) /
  removed, PvE tier changes, records with only a new wiki revision. Until an update finishes, its starting
  state is kept in `translate/work/update_baseline.json`, so a re-run after a fix still compares with the
  last finished update.
- Deploy: `npm run deploy` (in `web/`, `web/scripts/deploy.ts`) copies `web/dist` into a fresh one-commit
  branch `gh-pages` and force-pushes it to `origin`. It refuses a `dist/` built with `IMAGES=full`. There is
  no GitHub Actions build: the site needs `data/raw/game_db`, which exists only locally.
- Not in git (`.gitignore`): `data/raw/game_db`, `web/public/img`, `web/dist`, `web/src/generated`,
  `translate/work`, `docs/screenshots` (they show game art), `node_modules`.
- Runes whose own icon (`item_RuneStone_secondary_02_<N>`) is not in the game files show the generic rune
  stone icon `item_RuneStone_secondary_02` with the rune's name as a caption (listed in `docs/IMAGES_REPORT.md`).

## Status

Steps 1–5 done: raw data downloaded, parsed into Chinese JSON (`data/zh`), English names, glossary and
translation in `data/en` (see `data/en/REPORT.md`), static site in `web/`, published to GitHub Pages and
refreshed with `python -m yog update`.
