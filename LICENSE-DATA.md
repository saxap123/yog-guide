# Data licence: CC BY-NC-SA 4.0

The data of yog-guide is an adaptation of the community wiki **BWIKI — 依盖之书**
(<https://wiki.biligame.com/bookofyog/>) by **赧然丶 and contributors**, licensed under
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/)
(legal code: <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode>).

These files are shared under the same licence, **CC BY-NC-SA 4.0**:

| path | what |
|---|---|
| `data/en/` | English version of the wiki data (translated, with official game names where they exist) |
| `data/names.json` | Chinese wiki names → English names |
| `data/glossary.json` | Chinese terms → English |
| `data/zh/` | the wiki data parsed into JSON (Chinese) |
| `data/raw/` (except `data/raw/game_db/`, which is not in the repository) | wiki pages and wiki data as downloaded |
| `data/CHANGELOG.md` | changes of the data |
| `translate/manual/` | our translations of wiki texts and names |

**Attribution.** When you reuse this data, credit: *“BWIKI 依盖之书 (赧然丶 and contributors),
CC BY-NC-SA 4.0; English adaptation: yog-guide”*, link the licence, and say if you changed it.
Every record keeps `source_url` and `permalink` (the exact wiki revision it comes from).

**Changes made.** Wiki pages were parsed into structured JSON; texts were translated into English;
names and terms were matched to the official English of the game where an exact match exists.
Wiki typos are kept as written.

**NonCommercial, ShareAlike.** No commercial use; adaptations must use the same licence.

**Not covered.** Official English names and game texts (marked `source: "game_db"` / “official”) are
© HangZhou QiHeShe Technology and are included only as short names and descriptions for reference.
Game imagery in the character and item icons and the guide screenshots is © HangZhou QiHeShe
Technology. The beginner screenshots under `web/public/guide-images/start-here/` are sourced from
[新手起号 by 夜月](https://wiki.biligame.com/bookofyog/index.php?oldid=8271). Each figure links to the
original image, and its English caption translates the author’s callouts.
