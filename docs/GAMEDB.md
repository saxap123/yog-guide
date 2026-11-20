# Game database (`data/raw/game_db/08.database`) — notes for step 3

Unpacked game files, supplied locally. **Read-only**: never modified, never committed
(`.gitignore`: `data/raw/GameDB/`, `data/raw/game_db/`). The folder on disk is
`data/raw/game_db/`; `parse_zh/gamedb.py` also accepts `data/raw/GameDB/`.
Only ids are copied into `data/zh`. File dates: 2026-09-22.

This file describes the structure only. **All examples below are synthetic** (made-up ids and
strings); nothing here is copied from the game files.

## Layout (749 files, ~272 MB)

| folder | content |
|---|---|
| `template/` | game tables (XML), Chinese only |
| `language/json/totalLanguageDicText.json` | the multilingual dictionary (Chinese, English and other languages per text id) |
| `language/json/en/` | English story / quest scripts (not used) |
| `language/xml/en/` | older partial English copies of some tables (not used) |
| `language/config/tpl_translate.xml` | which fields of which table are translated |
| `language/text/` | UI strings (not used) |
| `textasset/`, `stage/`, `battlepoint/`, `room/` | story config, battle stages, maps — not used |

## Format

**Tables** (`template/tpl_*.xml`): `<root><ROW><field>value</field>…</ROW>…</root>`, no DTD/entities.
Every translatable text field `X` has a sibling `X_id` pointing into the dictionary. Synthetic example:

```xml
<equip><id>10001</id><name>示例耳环</name><name_id>500001</name_id><type>14</type></equip>
```

**Dictionary**: a JSON array of objects `{"id", "zhcn", "en", …}` (one key per language).
The English name of a row is found as `table row → <field>_id → dictionary id → en`. Synthetic example:
row `10001` `name_id` 500001 → `{"id": 500001, "zhcn": "示例耳环", "en": "Sample Earring"}`.
Several dictionary entries can share one `zhcn`, so step 3 always goes through the table row, never
through a string search.

Placeholders like `{0}` in skill texts are filled from other tables (skill level and affix tables).

## Tables used by the guide

| table | used for |
|---|---|
| `tpl_sc_hero` | characters (matched by the wiki title); `icon_portrait` / `avatarID` name the image files |
| `tpl_heroSkill` | skill names and texts |
| `tpl_sc_equipment` | gear names, slot (`type`), quality, skill affixes of game-only build items, `iconID` |
| `tpl_sc_rune`, `tpl_sc_heirloom`, `tpl_sc_blackStone` | runes, relics, black stones (黑石); `iconID` |
| `tpl_sc_typeLevelTeam` | fronts (阵线) |
| `tpl_sc_equipment_affix` | affix texts |

Matching results (how many wiki names were found in the game tables, which were not, and why) are in
`data/zh/REPORT.md`, `data/en/REPORT.md` and `data/names.json` (`status: "unverified"` + reason).
Spellings that differ between the wiki and the game are listed in `translate/build_names.py`
(e.g. the wiki's 璨然银龙 is written with the traditional 燦 in the game).

`tpl_sc_equipment.type` ↔ wiki `部位` (observed on the matching items): 1 武器, 2 头盔, 3 衣服, 4 戒指,
5 圣物, 6 鞋子, 7 腰带, 8 护手, 9 项链, 10 副手, 11 裤子, 12 徽章, 13 卡牌, 14 耳坠
(two exceptions: one 徽章 with type 10, one 项链 with type 12).

## Used in step 3 (done)

`translate/` reads this folder (never writes). Kept in the repository: only the strings that
are used — official names (`data/names.json`), exact-match terms (`data/glossary.json`), the
official English texts placed into `data/en`, and the 99 game-only build items in
`data/en/gear.json` (`source: "game_db"`). Lore (hero descriptions, stories) is not used.
