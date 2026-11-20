# Step 3 report — names, glossary, translation (data/zh → data/en)

Wiki data: BWIKI 依盖之书 <https://wiki.biligame.com/bookofyog/> (CC BY-NC-SA 4.0). Official English: game files dated 2026-09-22 (`data/raw/game_db`, local, read-only, git-ignored). Only strings that are used are kept (`data/names.json`, `data/glossary.json`, `data/en`).

Regenerate: `python translate/build_names.py && python translate/build_glossary.py && python translate/build_en.py && python translate/check_numbers.py && python translate/write_report.py`.

## Names (`data/names.json`)

Rule: Chinese wiki name → game table row (`name_id` / `title_id`) → `totalLanguageDicText.json`. Names are never translated by us: not found → `en: null`, `status: unverified`.

| category | names | from the game | translated | empty (unverified) |
|---|---|---|---|---|
| characters | 76 | 75 (98.7%) | 0 | 1 (1.3%) |
| skills | 501 | 483 (96.4%) | 0 | 18 (3.6%) |
| items (gear) | 353 | 339 (96.0%) | 0 | 14 (4.0%) |
| relics | 60 | 58 (96.7%) | 0 | 2 (3.3%) |
| runes | 30 | 27 (90.0%) | 0 | 3 (10.0%) |
| 黑石 (black stones) | 18 | 18 (100.0%) | 0 | 0 (0.0%) |
| 阵线 (factions) | 45 | 45 (100.0%) | 0 | 0 (0.0%) |
| **all** | 1083 | 1045 (96.5%) | 0 | 38 (3.5%) |

Aliases: 璨然银龙 = 燦然银龙 (game spelling).

### Unverified names

| category | name | why | possible match (unverified) | bare dictionary entry (not used) |
|---|---|---|---|---|
| characters | 司正天座 | not in tpl_sc_hero (game files dated 2026-09-22; wiki release 2026年11月2日) | — | — |
| skills | 灿若自日 | no skill of this name in tpl_heroSkill / tpl_passive_skill | 灿若白日 | — |
| skills | 普通攻击 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | Normal Attack (58656) |
| skills | 刽子手 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | Coup De Grace (2243) |
| skills | 永续寒冬 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | Perpetual Winter (2301) |
| skills | 天罚 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 昭如日月 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 无垢之境 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 洄游天平 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 溯光 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 天光乍破 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 赤诚 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 呦呦鹿鸣 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | Inky Deer Sounds (73546) |
| skills | 笔底春花 | no skill of this name in tpl_heroSkill / tpl_passive_skill | 笔底春风 | — |
| skills | 法术延迟 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | — |
| skills | 缭乱雷荆 | no skill of this name in tpl_heroSkill / tpl_passive_skill | 缭乱雷棘 | — |
| skills | 飞星 | no skill of this name in tpl_heroSkill / tpl_passive_skill | — | Spunky Star (60121) |
| skills | 赤枕之心 | no skill of this name in tpl_heroSkill / tpl_passive_skill | 赤忱之心 | — |
| skills | 龙刃纳销 | no skill of this name in tpl_heroSkill / tpl_passive_skill | 龙刃纳鞘 | — |
| gear | 七杀分牌 | not in tpl_sc_equipment | 七杀令牌 | — |
| gear | 任意太古装备 | not an item name (wiki text) | — | — |
| gear | 宗室礼鞋 | probably a typo on the wiki; not corrected | 宗室礼靴 | — |
| gear | 怒焰微印 | probably a typo on the wiki; not corrected | 怒焰徽印 | — |
| gear | 清光昭雪 | not in tpl_sc_equipment | — | — |
| gear | 电闪魂面 | not in tpl_sc_equipment | 电闪魂衣, 电闪魂盔 | Roaring Lightning Mask (73486) |
| gear | 绝境増益翡影 | not in tpl_sc_equipment | 绝境增益翡影, 绝境增益翡手 | — |
| gear | 绝境増益翡手 | not in tpl_sc_equipment | 绝境增益翡手, 绝境增益翡影 | — |
| gear | 绝境増益青盾 | not in tpl_sc_equipment | 绝境增益青盾 | — |
| gear | 聚能铠甲 | probably a typo on the wiki; not corrected | 聚魔铠甲 | — |
| gear | 苍珀玄帽 | not in tpl_sc_equipment | 苍珀玄衣, 苍珀玄盔 | Peridot Black Hat (73483) |
| gear | 薄暮幽寂影手 | not in tpl_sc_equipment | — | — |
| gear | 逆厄辉焕光手 | not in tpl_sc_equipment | 逆厄辉焕光手（未投放）, 逆厄辉链 | Gloves of Doom Reversal (76819) |
| gear | 饮雪骨冠 | not in tpl_sc_equipment | 饮雪骨衣, 饮雪骨盔 | Sip Snow Crown (73485) |
| relics | 天律奥典 | not in tpl_sc_heirloom | — | — |
| relics | 灼华轻羽 | in the game table but the dictionary has no English text | — | — |
| runes | 逐日 | probably a typo on the wiki; not corrected | 逐日者 | — |
| runes | 铁荆 | probably a typo on the wiki; not corrected | 铁棘 | — |
| runes | 锻钢 | probably a typo on the wiki; not corrected | 断钢 | — |

## Glossary (`data/glossary.json`)

312 terms: from the game dictionary (exact Chinese match) 241 (77.2%), translated by us 65 (20.8%), unverified (wiki typos / garbled values, `en: null`) 6.

| category | game_db | translated | unverified |
|---|---|---|---|
| in_text | 85 | 7 | 0 |
| stat | 71 | 11 | 4 |
| source | 33 | 13 | 2 |
| slot | 14 | 0 | 0 |
| damage | 5 | 9 | 0 |
| skill_slot | 4 | 9 | 0 |
| profile | 10 | 3 | 0 |
| element | 6 | 0 | 0 |
| item_flag | 0 | 5 | 0 |
| quality | 4 | 0 | 0 |
| resource | 1 | 2 | 0 |
| rune_colour | 0 | 3 | 0 |
| battle_grid | 0 | 3 | 0 |
| material | 2 | 0 | 0 |
| relic_type | 2 | 0 | 0 |
| faction_type | 2 | 0 | 0 |
| rune_type | 2 | 0 | 0 |

Unverified terms: 冰霜传统 (probably a typo on the wiki; not corrected, possible match 冰霜穿透); 全伤害伤害增幅 (probably a typo on the wiki; not corrected, possible match 全伤害类型增幅); 主线-困难度 (probably a typo on the wiki; not corrected, possible match 主线-困难难度); 冰霜理伤害增幅 (garbled value on the wiki; not corrected, possible match 冰霜伤害增幅); 类型增幅 (truncated value on the wiki; not completed, possible match 全伤害类型增幅); 黑市-长城被狼血提红的乳牙。长大，总是悄然而至圣殿 (garbled wiki value (an unrelated sentence inside 黑市-长城圣殿); not translated, possible match 黑市-长城圣殿).

## Strings of data/en by source

| source | strings | share |
|---|---|---|
| official English text of the game (values filled from the wiki, numbers checked) | 1772 | 7.8% |
| names.json (official names) | 3683 | 16.3% |
| glossary.json (terms, stat lines) | 14865 | 65.7% |
| mechanical (dates, scaling parts) | 392 | 1.7% |
| our translation of the wiki text | 1508 | 6.7% |
| lore — kept in Chinese, not translated | 214 | 0.9% |
| empty (`null`, listed in `i18n.missing`) | 185 | 0.8% |

English strings that still contain a Chinese name: 0.

Unofficial names (step 4): names that have no official English and used to stay in Chinese inside English strings are translated by meaning in `translate/manual/unofficial_names.json` (people and places romanized, wiki typos translated as written) and listed per record in `i18n.unofficial_names`: 135 replacements of 59 distinct names in 102 strings.

Empty strings by reason: names.json/skills 78, not translatable (see translate/manual/texts) 67, names.json/gear 22, names.json/runes 8, names.json/relics 4, names.json/characters 4, glossary 2.

## Items that exist only in the game

99 items named in wiki builds have no wiki page; they are in `data/en/gear.json` with `source: "game_db"` (id `gear-game-<game id>`), linked from 205 build entries (`builds[].item_ids`). With slot: 99, with a fixed quality in the game table: 23, with a skill text: 75 (skill English withheld because the game's English has other numbers than its Chinese: 12).

items with source game_db are named in wiki builds but have no wiki page; data from the game files dated 2026-09-22 (no source_url/revid). Their skill value ranges use the wiki format, which equals the wiki text for 75 of 159 wiki items checked (the others differ in wording, typos or fixed values on the wiki).

## Number check (`translate/check_numbers.py`, also `tests/test_translate.py`)

String pairs compared: 23842. Number/percent mismatches zh ↔ en: **0**. (English `null` is not compared: 197.)

### Wiki vs game: texts of the same skill/effect that differ

The game has a text for this very skill / blood rank / item / relic / faction, but it is not the wiki text with values filled in, so the wiki text was translated. Stricter than «numbers equal»: a different wording also counts (e.g. wiki 提升 *increase* vs game 下降 *decrease* with the same 10%). Punctuation and doubled characters are ignored.

| kind | numbers differ | wording differs |
|---|---|---|
| blood_rank | 26 | 28 |
| faction | 5 | 5 |
| gear_skill | 15 | 42 |
| relic_skill | 1 | 14 |
| skill | 55 | 144 |

Same wording, different numbers (102) — numbers as written; the game's `{n}` values are filled per level and not shown:

| record | field | wiki numbers | game literal numbers |
|---|---|---|---|
| 不熄曜日 | blood_ranks.ranks[3] | 6 25 0.5 | 6 25 0.5 |
| 传承之龙 | skills[5].description | 30 | — |
| 冰封之心 | skills[3].description | 6 0.1 15 0.2 3 | 0.1 15 0.2 3 |
| 凌空械羽 | skills[3].description | 60 | — |
| 双鸣追猎 | skills[1].description | 0.2 2 12 2 | 0.2 4 2 |
| 双鸣追猎 | skills[4].description | 20 10 3 1000 | 20 10 3 |
| 双鸣追猎 | blood_ranks.ranks[0] | 1 | 1 |
| 双鸣追猎 | blood_ranks.ranks[1] | 3 1 1 | 3 1 1 |
| 双鸣追猎 | blood_ranks.ranks[3] | 1 0.2 1 400 | 1 0.2 1 500 |
| 唤霜海灵 | skills[0].description | 250 10 15 25 | 10 15 25 |
| 唤霜海灵 | skills[2].description | 50 370 | 50 |
| 唤霜海灵 | skills[4].description | 2 5 1 10 100 | 2 5 1 100 |
| 唤霜海灵 | skills[5].description | 2 200 20 | 2 20 |
| 唤霜海灵 | skills[6].description | 30 | — |
| 唤霜海灵 | blood_ranks.ranks[0] | 50 1 | 50 1 |
| 圣翼降临 | skills[1].description | 1 5 3000 | 1 5 |
| 圣翼降临 | blood_ranks.ranks[2] | 1 5 | 1 5 |
| 墨凝清影 | skills[3].description | 6000 10 2 | 10 2 |
| 夜宴霆光 | skills[3].description | 3 1.5 0.5 16000 | 3 1.5 0.5 |
| 夜行暹罗 | skills[4].description | 1 50 50 | 1 50 |
| 天邪魅影 | skills[2].description | 10 3 6 3500 1.5 | 10 3 6 1.5 |
| 天邪魅影 | blood_ranks.ranks[1] | 50 | 50 |
| 天邪魅影 | blood_ranks.ranks[2] | 2 3 1 0.5 | 2 3 1 0.5 |
| 婆娑轮舞 | skills[3].description | 100 15 | 15 |
| 婆娑轮舞 | skills[6].description | 30 | — |
| 审判使者 | skills[2].description | 8 300 30 0.5 60 2 | 8 30 0.5 60 2 |
| 审判使者 | skills[6].description | 5 30 | 30 |
| 御刃神锋 | skills[3].description | 10 1 3 30 | 1 3 |
| 御刃神锋 | skills[5].description | 1 1 3 5 16 | 1 1 3 5 |
| 战争之蹄 | skills[0].description | 400 | — |
| 战争之蹄 | skills[2].description | 1 6 50 50 15 | 1 50 50 15 |
| 战争之蹄 | skills[5].description | 7 | — |
| 战争之蹄 | skills[6].description | 30 | — |
| 战争之蹄 | blood_ranks.ranks[0] | 1 0.5 15 35 | 1 0.5 15 35 |
| 战争之蹄 | blood_ranks.ranks[2] | 50 50 | 50 50 |
| 战争之蹄 | blood_ranks.ranks[4] |  | — |
| 拂光破雪 | blood_ranks.ranks[2] | 100 10 1 25 | 100 10 1 25 |
| 月渊龙女 | skills[2].description | 5 3000 0.5 | 5 1 |
| 月渊龙女 | blood_ranks.ranks[0] | 200 35 | 20 35 |
| 灵刃之主 | skills[1].description | 10 5 200 225 | 10 5 |
| 炙光之舞 | skills[3].description | 2 5 500 50 10 0.25 | 2 5 50 10 0.25 |
| 炽焰降生 | skills[5].description | 4000 25 1 | 25 1 |
| 炽焰降生 | blood_ranks.ranks[4] | 10 | 10 |
| 爱恋花见 | skills[0].description | 1 1000 6 | 1 6 |
| 爱恋花见 | blood_ranks.ranks[1] | 1 2 | 1 2 |
| 玉尘灵仙 | skills[3].description | 3 3500 1 1 5 15 50 | 3 1 1 5 15 50 |
| 玉尘灵仙 | skills[5].description | 10 2 1500 3 | 10 2 3 |
| 玉尘灵仙 | skills[6].description | 30 | — |
| 玉尘灵仙 | blood_ranks.ranks[3] | 1 1000 75 | 1 1000 75 |
| 玉面九尾 | skills[3].description | 1 3 30 2 1 1 10000 | 1 3 30 2 1 1 |
| 百花旅者 | skills[1].description | 500 100 | 100 |
| 神之嫡子 | skills[2].description | 1 3 10 36.8 | 1 3 10 |
| 秽翼魔女 | skills[0].description | 600 | — |
| 秽翼魔女 | skills[2].description | 1 800 | 1 |
| 秽翼魔女 | skills[6].description | 30 | — |
| 秽翼魔女 | blood_ranks.ranks[0] | 50 | 50 |
| 绚彩星绘 | blood_ranks.ranks[3] | 20 1 150 | 20 1 150 |
| 绮夜梦影 | blood_ranks.ranks[1] | 1 0.5 50 | 1 0.75 50 |
| 绯晶战影 | skills[2].description | 30000 1 25 4 | 1 25 3 |
| 绯晶战影 | blood_ranks.ranks[0] | 1 0.1 | 1 0.1 |
| 绿森山灵 | blood_ranks.ranks[3] | 60 | 60 |
| 自由炮手 | skills[2].description | 3 4000 | 3 |
| 自由炮手 | blood_ranks.ranks[1] | 10 5 | 10 5 |
| 裁决圣锤 | skills[3].description | 1.5 5 5 5 1 1 | 1.5 5 1 1 |
| 诅咒之王 | skills[4].description | 10 0.5 5 0.5 | 0.5 5 0.5 |
| 迷迭妖精 | skills[1].description | 1 2500 2 | 1 2 |
| 迷迭妖精 | skills[2].description | 100 1000 | 1000 |
| 金蜂破茧 | skills[1].description | 0.3 1000 0.1 300 0 | 0.3 0.1 300 0 |
| 金蜂破茧 | blood_ranks.ranks[0] | 1 50 | 1 50 |
| 雪月公主 | skills[3].description | 2 30 1 | 2 1 |
| 霓裳若仙 | skills[1].description | 1 5 0.5 5 9000 3 | 1 5 0.5 5 3 |
| 霓裳若仙 | skills[5].description | 6000 8 1 10 | 8 1 10 |
| 青鸾巽羽 | skills[0].description | 1 2000 | 1 |
| 青鸾巽羽 | skills[4].description | 100 | — |
| 青鸾巽羽 | skills[6].description | 1 12 1 10 | 1 12 1 |
| 飞焰铃舞 | blood_ranks.ranks[3] | 1000 100 20 | 1000 100 20 |
| 魂棺语者 | skills[5].description | 10 5 5 1 1 | 10 1 1 |
| 黑衫刃影 | skills[0].description | 3 250 1 2 3 | 3 1 2 3 |
| 黑衫刃影 | skills[6].description | 30 | — |
| 黑衫刃影 | blood_ranks.ranks[0] | 6 | 6 |
| 黑衫刃影 | blood_ranks.ranks[2] | 100 7.5 10 | 100 7.5 10 |
| 云图点睛 | skill | 1 1 1 6 10 | 1 1 1 |
| 咒石项链 | skill | 15 10 | 15 10 |
| 圣战辉牌 | skill | 6 9 11 50 6 100 200 | 6 9 11 50 100 200 |
| 夜幕暗盔 | skill | 0.3 | 0.3 |
| 寒刃霜天 | skill | 15 6 10 | 15 |
| 巫毒咒牌 | skill | 10 20 4 0.5 | 4 0.5 |
| 染血狼牙 | skill | 1 2 | 1 2 |
| 烈刃炎上 | skill | 1 0.5 6 10 | 1 0.5 |
| 电涌蚀心裤 | skill | 35 1 0.5 3 | 35 1 0.5 3 |
| 界卫魔面 | skill | 10 11 15 30 6 3 | 10 11 15 30 3 |
| 紫傀异面 | skill | 1 1 20 1 400 6 566 8 | 1 1 20 1 8 |
| 蔚蓝魅影 | skill | 75 45 15 30 2.5 | 75 45 15 30 2.5 |
| 虚灵腰环 | skill | 5 1 0.8 3 30 5 | 5 1 30 5 |
| 血火荣耀 | skill | 5 1 | 5 1 |
| 飓风凛甲 | skill | 1 3 4 1 50 100 | 1 3 4 1 50 100 |
| 霜冻之灾 | skills[0] | 15 30 | 15 |
| 咒蚀 | thresholds[0] | 2 3 4 1 3 1.5 0.5 | 1 |
| 回能 | thresholds[0] | 2 3 4 50 75 100 5 1 | 5 1 |
| 暴怒 | thresholds[0] | 2 3 4 5 6 1 1.5 2 3 3 5 30 0 0 0 0 100 100 30 | 5 30 100 30 |
| 超导 | thresholds[0] | 2 3 4 5 3 6 10 10 5 0 0 0 1 4 30 5 140 | 5 4 30 5 140 |
| 魔导 | thresholds[0] | 2 3 4 5 6 50 1 1.5 2 3 4 4 14 14 14 14 8 | 50 1 |

## Empty English strings

Per record in `i18n.missing`. Summary by field:

| field | reason | count |
|---|---|---|
| skills | names.json/skills | 78 |
| profile | not translatable (see translate/manual/texts) | 38 |
| suffixes | not translatable (see translate/manual/texts) | 28 |
| builds | names.json/gear | 12 |
| name | names.json/gear | 10 |
| runes | names.json/runes | 8 |
| character | names.json/characters | 3 |
| relics | names.json/relics | 2 |
| obtain | glossary | 2 |
| name | names.json/relics | 2 |
| name | names.json/characters | 1 |
| exclusive | not translatable (see translate/manual/texts) | 1 |

## Examples for review

### 飞焰铃舞 → Flamebell Dance

Real name: 呜喵 → Nyanko. Element: 火焰 → Fire. Factions: 辅助 → Support Front, 召唤 → Summoners Front, 通灵 → Spiritmasters Front, 坚韧 → Vanguards Front, 妖精 → Fairies Front, 力场 → Field Front, 流星 → Meteor Front, 回馈 → Return Front, 灭法 → Spell Breaker front.

| skill | zh | en | source |
|---|---|---|---|
| 飞焰流矢 → Blazing Bolt | 发射箭矢对单个敌人造成500%法术强度的火焰伤害(本技能不会受攻速影响，造成的伤害视为技能伤害。) | Fires an arrow at a single enemy, dealing Fire Damage equal to 500% of Spell Power. (This skill is unaffected by Attack Speed, and its damage is considered Skill Damage.) | game_db #91667 loose |
| 八方火舞 → Eightfold Flame Dance | 释放结界，结界内敌方每秒受到10000%法术强度的火焰伤害，且结界内所有友方单位全伤害减免+20%，结界持续8秒。 | Creates a barrier. Enemies within take Fire Damage equal to 10000% of Spell Power every second, while all allied units within gain +20% All Damage Reduction. The barrier lasts 8 sec. | game_db #91669 exact |
| 流火天羽 → Heavenly Flamefeathers | 朝最近的敌人发射箭雨，每波箭雨对范围内的敌人造成5000%法术强度的火焰伤害，共5波。 | Fires a rain of arrows at the nearest enemy in 5 waves. Each wave deals Fire Damage equal to 5000% of Spell Power to enemies within the area. | game_db #91668 exact |
| 火灵双生 → Twin Flame Spirits | 绑定一个友方黑卫，当自己释放结界时，召唤一个该单位的傀儡，傀儡拥有本体25%的伤害和50%生命值如果是火属性黑卫，则效果翻倍，傀儡持续8秒。(所有傀儡的存在上限最多为4个) | Binds to an allied Blackguard. When casting a barrier, summons a puppet of that unit. The puppet has 25% of the original's damage and 50% HP. If the bound Blackguard is Fire-attribute, the effects are doubled. The puppet lasts 8 sec. (A maximum of 4 puppets can exist at once.) | game_db #91670 loose |
| 散为云烟 → Into Smoke | 每波箭雨都有15%削弱目标当前50怒气值，自身感知高于目标时，每高出5点感知，增加1%触发几率。 | Each wave of arrow rain has a 15% chance to reduce the target's current Rage by 50. If own Perception is higher than the target's, the trigger chance increases by 1% for every 5 additional Perception. | game_db #91671 exact |
| 赤瞳 → Crimson Eye | 【八方火舞】持续期间，友方单位的普攻暴击和技能暴击几率增加20%。 | During [Eightfold Flame Dance], allied units' Normal Attack Crit Chance and Skill Crit Chance increase by 20%. | game_db #91672 exact |
| 灵犀 → Heartlink | 飞焰铃舞的感知+10。 | Flamebell Dance's Perception +10. | game_db #91673 exact |
| 振奋光环 → Motivating Aura | 振奋鼓舞战友，所有友方单位初始怒气增加25点 | Uplifts and encourages comrades, all friendly units have their initial rage values increasd by 25 points | game_db #4302 exact |
| 气定神闲 → Flow | 能够轻松快速的释放法术，主动技能冷却时间降低10% | Ability to release spells easier and quicker, reduces cooldown of active skills by 10% | game_db #4303 exact |
| 法术延迟 → *null* | 法术强度提升6% | Spell Power increased by 6% | translated |
| 星辰之躯 → Astral Form | 全抗性提升8点，伤害减免8% | All resistance increased by 8 points, damage reduction by 8% | game_db #2994 exact |

| blood rank | zh | en | source |
|---|---|---|---|
| 1 | 【赤瞳】提供的暴击几率+10%。 | Crit Chance granted by [Crimson Eye] +10%. | game_db #91675 |
| 2 | 【八方火舞】持续期间，场上所有己方召唤物受到 / 的伤害减少20%。 | During [Eightfold Flame Dance], all allied summons on the field take 20% less damage. | game_db #91676 |
| 3 | 【八方火舞】提供的全伤害减免额外+10%。 | [Eightfold Flame Dance] grants an additional +10% All Damage Reduction. | game_db #91677 |
| 4 | 释放【八方火舞】时，如果自身怒气大于1000，每超出100，都会清除掉场上所有敌方单位20%的护盾值。 | When casting [Eightfold Flame Dance], if own Rage is above 1000, every 100 above it removes 20% of the Shield value of all enemy units on the field. | translated |
| 5 | 【八方火舞】持续期间，场上敌方角色有15%几率无法触发复活效果，自身感知高于目标时，每高出5点，增加1%触发几率。 | During [Eightfold Flame Dance], enemy characters on the field have a 15% chance to fail to trigger Revival effects. If own Perception is higher than the target's, the trigger chance increases by 1% for every 5 additional Perception. | game_db #91679 |
| 6 | 飞焰铃舞造成的所有伤害+10%。 | All damage dealt by Flamebell Dance +10%. | game_db #91680 |

Build «蹲» → «Waiting (not filled in yet)»: 武器: 飞星如焰 → Blazing Shooting Stars

Affix recommendations: 全伤害类型减免（PVE要95%）、体质、最大生命值、怒气、怒气恢复 → All Damage Reduction (PVE needs 95%); Constitution; Max HP; Rage; Rage Restore

### 千宵月守 → Nightmoon Warden

Real name: 纱夜 → Sasaya. Element: 黑暗 → Dark. Factions: 秘术 → Mystic Front, 智慧 → Sages Front, 魔导 → Invokers Front, 超导 → Occultists Front, 流星 → Meteor Front, 暴怒 → Rage Front, 咒蚀 → Cursed Erosion Front, 雷暴 → Thunderstorm Front, 共鸣 → Resonance Front.

| skill | zh | en | source |
|---|---|---|---|
| 黑焰冲袭 → Blackflame Rush | 对最近的一名敌人发射法球造成2500%法术强度的黑暗伤害。(本技能不会受攻速影响，造成的伤害视为技能伤害。) | Fires an orb at the nearest enemy, dealing 2500% Spell Power as Dark damage. (This skill is not affected by Attack Speed, and the damage is treated as skill damage.) | game_db #85684 exact |
| 暗渊咒杀 → Abyssal Curse | 在上空凝聚10枚暗影长矛，朝随机敌方单位发射，并对其造成5000%法术强度的黑暗伤害。 | Summon 10 Shadow Spears in the air and launch them at random enemies. Each spear deals Dark damage equal to 5000% Spell Power. | game_db #85688 exact |
| 邪影追猎 → Umbral Pursuit | 每当场上有敌方单位被施加异常状态时，都有几率对场上最多6名敌方单位释放暗影飞刃，造成3500%法术强度的黑暗伤害。发动几率：20%。(该技能的最小触发间隔为1秒) | Whenever an enemy unit on the field is inflicted with special debuffs such as Numb, Decay, Daze, Slow, Judgment, or Blind, there is a chance to launch Shadow Blades at up to 6 enemies, dealing 3500% Magic Power as Dark Damage. Trigger Chance: 20% (Minimum trigger interval: 1 second) | game_db #85687 exact |
| 今宵月圆 → Moonlit Night | 指定一个友方黑卫，使其在释放必杀技之后，有一定几率再次释放(千霄月守的感知属性越高，触发几率越高，且再次释放的必杀技不消耗怒气值)，该效果有6秒的触发间隔。(部位黑卫如花信风、布兰妮等长时间持续释放效果的必杀技无法受该技能影响。) | Designates one allied Blackguard; after casting an Ultimate Skill, it has a certain chance to cast it again (the higher Skymoon Warden's Perception, the higher the trigger chance, and the repeated Ultimate Skill costs no Rage). This effect has a 6 sec trigger interval. (Ultimate Skills of some Blackguards with long-lasting effects, such as Kashinfuu and Brittany, cannot be affected by this skill.) | translated |
| 月祝之舞 → Dance of Moon's Blessing | 敌方被【暗渊咒杀】击中时，有几率恢复千霄月守2点源力值。且【暗渊咒杀】造成的伤害提升100%。 | When an enemy is hit by Abyssal Curse, there is a chance to restore 2 Force Power to Sasaya, and the damage dealt by Abyssal Curse is increased by 100%. | game_db #85690 exact |
| 叹月无瑕 → Moon's Flawless Lament | 【邪影追猎】造成的伤害提升100%。 | Damage dealt by Umbral Pursuit increased by 100%. | game_db #85691 exact |
| 洞悉 → Insight | 千霄月守的感知+10。 | Perception of Sasaya +10. | game_db #85671 exact |
| 玻璃大炮 → Glass Cannon | 放弃防护，专心攻击，造成的伤害提高15%，但是自身受到的伤害也提高10% | The best defense is to kill every enemy, increases damage caused by 15%, but also increase the damage received by 10% | game_db #4295 exact |
| 体质增强 → Constitution enhancement | 最大生命值提升2300点 | Max HP increased by 2300 points | game_db #2993 exact |
| 元素充能 → Spirit Charge | 造成非物理伤害时，恢复造成伤害10%的生命值 | When dealing non-Physical DMG, restores HP equal to 10% of the DMG dealt | translated |
| 星辰之躯 → Astral Form | 全抗性提升8点，伤害减免8% | All resistance increased by 8 points, damage reduction by 8% | game_db #2994 exact |

| blood rank | zh | en | source |
|---|---|---|---|
| 1 | 【暗渊咒杀】可以额外穿透3个目标。 | Abyssal Curse can pierce 3 additional targets. | game_db #85711 |
| 2 | 【暗渊咒杀】有几率使目标致盲，持续5秒，千霄月守的感知越高，触发的几率越大。 | Abyssal Curse has a chance to Blind the target for 5 seconds. The higher Sasaya's Perception, the higher the trigger chance. | game_db #85712 |
| 3 | 【黑焰冲袭】会优先攻击最大生命值最低的敌方目标，且自身受到致命伤害时，会触发不死，持续5秒；且自身强韧值超过50时，每额外拥有10点，将延长不死的持续时间1秒。最多延长5秒。（该效果有120秒触发间隔。） | [Blackflame Rush] prioritizes attacking the enemy with the lowest Max HP. When receiving fatal damage, grants Undying for 5s. / If Tenacity exceeds 50, every additional 10 Tenacity extends the Undying duration by 1s, up to a maximum of 5s. / (This effect has a 120s cooldown.) | game_db #85713 |
| 4 | 光环：全体友方黑卫追击技能发动率+12%。 | Aura: Increases follow-up attack activation rate of all allied Blackguards by 12%. | game_db #85714 |
| 5 | 千霄月守的感知超过120时，每多拥有60点感知，都会使【邪影追猎】的发射数量+1。 | When Sasaya's Perception exceeds 120, every additional 60 Perception increases the number of shots of 【Umbral Pursuit】 by +1. | game_db #85715 |
| 6 | 千宵月守造成的所有伤害+10%。 | All DMG dealt by Nightmoon Warden +10%. | translated |

Build «450/700级» → «Level 450/700»: 头盔: 月辉·烁金荧紫 → Moonlight · Regal Amethyst; 项链: 魔眼吊坠 → Eye of Agamemnon; 卡牌: 龙力魔牌 → Devil Card of Impasse; 耳坠: 魔弦耳环 → Earring of Magic String; 衣服: 聚能之铠 → Raging Armor; 戒指: 猩红秘戒 → Crimson Band; 腰带: 嗜战者束腰 → Warmonger's Warbelt; 圣物: 月辉·紫晶鸦首 → Moonlight · Amethyst Ravenhead; 裤子: 戏谑者裤腿 → Joker's Pantaloons; 徽章: 魔涌之徽 → Runes of the Surge; 鞋子: 月辉·王室金靴 → Moonlight · Royal Walkers; 副手: 死灵法盾 → Necromancer's Deliverance; 武器: 宵暗刃舞 → Nightblade Dance; 护手: 妖精秘手 → Sprite's Spite

Build «1000级» → «Level 1000»: 头盔: 噬魂血盔 → Soulfeast Helm; 项链: 黑色汪洋 → Black Ocean; 卡牌: 任意太古装备 → null; 耳坠: 魔弦耳环 → Earring of Magic String; 衣服: 黑金护甲 → Blackgold Armor; 戒指: 冥蚀渊薮咒戒 → Abyss Hex Ring; 腰带: 感电者 → Belt of Electrify; 圣物: 冥蚀渊薮咒符 → Abyss Hex Amulet; 裤子: 炎铸胫甲 → Flame-Forged Greaves; 徽章: 冥蚀渊薮咒徽 → Abyss Hex Emblem; 鞋子: 宗室礼靴 → Royal Family Boots; 副手: 冥蚀渊薮咒盾 → Abyss Hex Shield; 武器: 血隐长刃 → Bloodveil Longblade; 护手: 幽冥初水 → Netherworld First Water

Affix recommendations: 全伤害类型减免（PVE要95%）、技能暴击、%法术强度、暴击倍率、魔力、全伤害类型增幅、法术伤害增幅、冰霜/火焰/闪电伤害增幅（取最高值）、冰霜/火焰/闪电穿透（取最高值） → All Damage Reduction (PVE needs 95%); Skill Crit; Spell Power %; Crit Damage Boost; Intelligence; All Damage Boost; Spell Damage Boost; Frost/Fire/Lightning Damage Boost (Take the highest value); Frost/Fire/Lightning Penetration (Take the highest value)

### 璨然银龙 → Radiant Dragon

Real name: 维娜 → Vina. Element: 冰霜 → Frost. Factions: 刺杀 → Assassin Front, 游侠 → Rangers Front, 强袭 → Avengers Front, 敌法 → Nullifiers Front, 噬魂 → Souleaters Front, 坚韧 → Vanguards Front, 统帅 → Leaders Front, 灭法 → Spell Breaker front, 咒蚀 → Cursed Erosion Front.

| skill | zh | en | source |
|---|---|---|---|
| 一线霜寒 → Rimed Edge | 对前方小范围敌人造成500%法术强度的冰霜伤害。(本技能会受攻速影响，造成的伤害视为普攻伤害。) | Deals 500% Spell Power as Frost damage to enemies in a small area ahead. (This skill is affected by Attack Speed, and its damage is treated as Normal Attack damage.) | game_db #88271 exact |
| 无息绝杀 → Silent Finisher | 快速在敌方目标之间闪现突刺，对目标以及路径上的敌方单位造成4500%法术强度的冰霜伤害，闪现突刺的释放速度会受自身攻速影响。 | Rapidly blinks between enemy targets, dealing 4500% Spell Power as Frost damage to the target and enemies in the path. The blink strike's speed is affected by Attack Speed. | game_db #88273 exact |
| 若风回雪 → Windborne Snow | 造成普攻伤害时，有几率触发一次强力的额外攻击，对小范围目标造成4500%法术强度的冰霜伤害。(该技能造成的伤害视为普攻伤害)发动率：25% | Dealing Normal Attack damage has a chance to trigger a powerful bonus attack, dealing 4500% Spell Power as Frost damage to enemies in a small area. (Damage from this skill is treated as Normal Attack damage.) Trigger Rate: 25% | game_db #88272 exact |
| 不朽之骨 → Immortal Bones | 自身在1.5秒内受到的伤害不会超过最大生命值的49%，但是自身也无法受到护盾恢复、治疗效果的影响(魔法盾吸收的伤害不记录在伤害限制范围内) | For 1.5 sec, damage taken cannot exceed 49% of Max HP, but you cannot benefit from Shield Recovery or healing effects. (Damage absorbed by Magic Shield is not counted toward the damage limit.) | game_db #88274 loose |
| 龙契啼鸣 → Dragonpact Cry | 【若风回雪】触发时，累积充能，充能达到100时下次【若风回雪】造成的伤害提升300%。触发时，在PVP场景中，有1%几率使目标立刻死亡。如果是其他战斗场景，则改为将【龙契啼鸣】的伤害提升5000%。(自身的感知超越目标越多，触发的概率越大） | When [Windborne Snow] triggers, it accumulates Charge. When Charge reaches 100, the next [Windborne Snow] deals 300% increased damage. Additionally, when [Windborne Snow] triggers in PvP, there is a 1% chance to instantly kill the target. In other battle scenarios, [Dragonpact Cry] damage is increased by 5000% instead. (The more your Perception exceeds the target's, the greater the trigger chance.) | game_db #88275 loose |
| 寒鳞锋锐 → Frostscale Edge | 普攻暴击几率+30。 | Normal Attack CRIT Chance +30. | game_db #88276 exact |
| 不摧 → Unyielding | 感知和强韧+5。 | Perception and Tenacity +5. | game_db #88277 exact |
| 恃强凌弱 → Bully | 对法术强度或物理强度低于自身的敌人造成伤害提高12% | Increases damage dealt to enemies with lower spell power or physical power by 12% | game_db #4305 exact |
| 致命伏击 → Lethal Ambush | 对生命值为满的敌人造成伤害提高15% | Increases damage dealt to enemies with full health by 15% | game_db #4306 exact |
| 暗影斗篷 → Cloak of Shadows | 受到减益效果的持续时间减少30% | Debuff duration reduced by 30% | game_db #4308 exact |
| 影遁 → Shadowmeld | 受到伤害时，有10%几率触发影遁，免疫该次伤害，并在接下来0.2秒内免疫所有伤害，触发间隔10秒 | When taking damage, there is a 10% chance to trigger Shadowmeld, immune to the damage, and immune to all damage for the next 0.2 sec. (Trigger interval 10 sec). | game_db #54718 exact |

| blood rank | zh | en | source |
|---|---|---|---|
| 1 | 每当造成普攻伤害时，有20%几率使自身的法术护甲穿透+150 | When dealing Normal Attack damage, 20% chance to gain +150 Spell Armor Penetration. | game_db #88281 |
| 2 | 进入战斗后第20秒，立刻获得【龙契啼鸣】的全部充能，并且该次效果必定会触发即死效果；之后每隔60秒触发一次。自身感知超过150时，每有1点感知可以减少0.1秒初始以及后续的触发间隔。 | 20s after entering battle, immediately gain full Charge for [Dragonpact Cry], and this activation is guaranteed to trigger the instant kill effect. Thereafter, this effect triggers once every 60s. If your Perception exceeds 150, every 1 point of Perception reduces the initial and subsequent trigger intervals by 0.1s. | game_db #88282 |
| 3 | 【无息绝杀】造成的伤害也将视为普攻伤害，并能够触发【若风回雪】效果；且【无息绝杀】的攻击次数+2。 | DMG dealt by [Silent Finisher] is also treated as Normal Attack DMG and can trigger [Windborne Snow] effects; additionally, the number of attacks of [Silent Finisher] +2. | translated |
| 4 | 【不朽之骨】的锁定受伤时间延长1.5秒。 | [Immortal Bones] damage lock duration +1.5 sec. | game_db #88284 |
| 5 | 提高强韧可降低【不朽之骨】受伤限制的比率，强韧超过50时，每4点降低1%，受伤限制的比率最低不会低于20%。且战斗开始时，立刻获得持续15秒的清醒效果。 | Increasing Tenacity reduces the damage limit ratio of [Immortal Bones]. When Tenacity exceeds 50, every 4 points reduces it by 1%, down to a minimum of 20%. Additionally, at the start of battle, immediately gain Clarity for 15s. | game_db #88285 |
| 6 | 璨然银龙造成的所有伤害+10%。 | All DMG dealt by Radiant Dragon +10%. | translated |

Build «450级» → «Level 450»: 头盔: 阿萨辛之首 → Head of Asasin; 项链: 时间守护者 → Time Keeper; 衣服: 聚能之铠 → Raging Armor; 腰带: 炎护腰带 → Flame Infused Sash; 圣物: 始祖之血 → Primordial Blood; 裤子: 戏谑者裤腿 → Joker's Pantaloons; 徽章: 秘影徽识 → Nox Emblem; 武器: 龙脊寒枪 → Dragonspine Frost Lance; 护手: 深渊之握 → Abyssal Grasps

Build «800级» → «Level 800»: 头盔: 夜幕暗盔 → Nightfall Helmet; 项链: 时间守护者 → Time Keeper; 耳坠: 辉耀之环 → Ring of Radiance; 衣服: 刺影锁甲 → Shadowthorn Lock Armor; 戒指: 雪影冰戒 → Ring of Snow Shadow; 腰带: 感电者 → Belt of Electrify; 圣物: 雪影之遗 → Legacy of Snow Shadow; 裤子: 霜凝咒裤 → Frost-Condensed Trousers; 徽章: 雪影白徽 → Emblem of Snow Shadow; 副手: 雪影守护 → Guard of Snow Shadow; 武器: 龙脊寒枪 → Dragonspine Frost Lance; 护手: 幽冥初水 → Netherworld First Water

Affix recommendations: 全伤害类型减免（PVE要95%）、%法术强度、攻击速度、暴击概率、冰霜穿透、暴击倍率、魔力、全伤害类型增幅、法术伤害增幅、冰霜伤害增幅 → All Damage Reduction (PVE needs 95%); Spell Power %; Attack Speed; Critical Chance (Attack); Frost Penetration; Crit Damage Boost; Intelligence; All Damage Boost; Spell Damage Boost; Frost Damage Boost

