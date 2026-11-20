# Step 2 report — data/raw → data/zh (Chinese, not translated)

Source: BWIKI 依盖之书 <https://wiki.biligame.com/bookofyog/>, CC BY-NC-SA 4.0. Every record carries `source_url`, `revid` and `permalink` of the page it was read from.

Regenerate: `python parse_zh/build.py`; check: `python -m unittest discover -s tests -v`.

## Output

| file | records | built from |
|---|---|---|
| characters/*.json | 76 | wikitext of Category:黑卫 pages (mwparserfromhell) |
| gear.json | 241 | SMW `browsebysubject` of Category:装备 |
| relics.json | 60 | SMW of Category:遗物 (+ `介绍` from wikitext, the template does not store it) |
| runes.json | 27 | SMW of Category:符文 (+ colour names of `边` from wikitext) |
| black_stones.json | 18 | tabs of page 黑石 + texts of 模板:推荐黑石 |
| factions.json | 45 | Category:阵线 pages (name/type) + tabs of page 阵线 (thresholds) |
| tiers.json | 152 | PVE节奏榜, PVP节奏榜 (every character × 2 modes) |

## Conventions

- Missing data is `null`; nothing is filled in from elsewhere.
- Wiki placeholder text (`立绘1`, `事迹1`, `角色故事`, `2级好感度问题`, `10级好感度答案1` …) → `null`; the replaced fields are listed per character in `placeholders_nulled`.
- The values `无` (none) and `暂无` (not yet) → `null`.
- Markup is removed: `{{颜色|红|x}}` → `x`, links → their text, `<br>`/`<p>` → newline, file links dropped.
- Lists written with `、` become arrays; skill lists written with `；` become arrays.
- `builds[].slots[slot]` = first item of the slot (shown in the centre of the wiki table); the following ones are in `alternatives[slot]` (the wiki shows the second one beside it). `item_ids` maps every item name of the build to a `gear.json` id or `null`.
- `builds[].level_tier` is the tab label exactly as written on the page (it is not always a level, e.g. `蹲`, `血包`).
- `skills[].scaling` lists only «percent + stat» pairs literally present in the text (stats: 法术强度, 物理强度, 物理&法术强度, 攻击力, 最大生命值, 体质).
- Templates inside `<!-- -->` comments are not rendered by the wiki and are ignored (listed below).
- Tier `as_of` = date of the tier page revision.

## Characters → empty fields

`null` sections/fields per character. `placeholders` = fields whose only content was wiki placeholder text.

| character | rarity | empty | placeholders → null |
|---|---|---|---|
| 不熄曜日 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 不祥怨灵 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 传承之龙 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 冰封之心 | SS | profile.race, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 角色故事 |
| 凌空械羽 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 凛冬魔女 | A | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, factions.others, affix_recommendations.primary, affix_recommendations.secondary, note, skills, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore, affection | — |
| 北境公主 | S | runes, blood_ranks, divinity, relics, battle_grid, affection | 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 千宵月守 | SP | note, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 双子之盾 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 双鸣追猎 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 司正天座 | SP | battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 唤霜海灵 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 圣翼降临 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 地精妖术师 | B | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, factions.others, affix_recommendations.primary, affix_recommendations.secondary, note, skills, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore, affection | — |
| 墨凝清影 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 夜宴霆光 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 夜行暹罗 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 立绘2, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 天邪魅影 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 夺魂之镰 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits | 立绘1, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 妖刀 | SS | profile.race, builds, runes, black_stones, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 婆娑轮舞 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 审判使者 | SS | profile.race, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 密林之眼 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 封魔利爪 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 巡林游侠 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 帝国之剑 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 异国商人 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 御刃神锋 | SS | profile.race, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 战争之蹄 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 拂光破雪 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 月渊龙女 | SP | note, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 构装守卫 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 欢愉魔女 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 深庭玫瑰 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 渡鸦魁首 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 灰袍法师 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 灵刃之主 | SS | profile.race, note, builds, runes, black_stones, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 炙光之舞 | SS | profile.race, affix_recommendations.secondary, runes, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 炽焰降生 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 烈阳将军 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 爱恋花见 | SP | runes, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 玉尘灵仙 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 立绘2, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 玉面九尾 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 王国猎手 | S | affix_recommendations.primary, affix_recommendations.secondary, note, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 璨然银龙 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 白龙 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 百花旅者 | SS | profile.race, runes, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 神之嫡子 | SS | profile.race, note, builds, runes, black_stones, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 秘境仙灵 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 秘术导师 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 秽翼魔女 | SP | divinity, portraits, lore.story, lore.deeds | 立绘1, 立绘2, 立绘3, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 5Q, 5A1, 5A2, 10Q, 10A |
| 纯净史莱姆 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 纯白之羽 | SS | profile.race, affix_recommendations.primary, affix_recommendations.secondary, note, runes, blood_ranks, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 纵火妖精 | S | affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 绚彩星绘 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 绞刃流火 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 绮夜梦影 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 绯晶战影 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 绯红荆棘 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 5Q, 10Q |
| 绿森山灵 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 自由炮手 | SP | note, runes, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 蚀骨魂龙 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 裁决圣锤 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 诅咒之王 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 迷迭妖精 | SP | divinity, battle_grid, portraits | 立绘1 |
| 金蜂破茧 | SP | note, runes, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 银刃之誓 | SP | note, divinity, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 长夜之影 | S | profile.race, profile.birthday, profile.birthplace, profile.height_weight, profile.specialties, profile.likes, profile.dislikes, affix_recommendations.primary, affix_recommendations.secondary, note, builds, runes, black_stones, blood_ranks, divinity, relics, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A1, 10A2 |
| 长辉照夜 | SP | note, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 雪月公主 | SP | divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 雷鸣掠空 | SP | note, divinity, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事 |
| 霓裳若仙 | SP | note, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 青鸾巽羽 | SP | note, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 飞焰铃舞 | SP | note, runes, divinity, battle_grid, portraits, lore.story, lore.deeds, affection | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 5Q, 5A1, 5A2, 10Q, 10A |
| 魂棺语者 | SP | note, divinity, portraits, lore.story, lore.deeds | 立绘1, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 2A1, 2A2, 10Q, 10A |
| 黑衫刃影 | SP | note, divinity, portraits, lore.story, lore.deeds | 立绘1, 立绘2, 立绘3, 事迹一, 事迹二, 事迹三, 事迹四, 事迹五, 事迹六, 角色故事, 2Q, 5Q, 10Q, 10A |

Totals (characters with the field empty): portraits 75, divinity 70, affection 62, note 62, battle_grid 60, lore.story 56, lore.deeds 56, runes 38, blood_ranks 34, affix_recommendations.secondary 29, builds 29, affix_recommendations.primary 28, black_stones 28, relics 25, profile.race 17, profile.birthday 8, profile.birthplace 8, profile.height_weight 8, profile.specialties 8, profile.dislikes 8, profile.likes 7, factions.others 2, skills 2, lore 2

### Builds with no items at all

- 唤霜海灵 «蹲一个450配装，欢迎下方评论区留言»
- 雷鸣掠空 «蹲一个450配装，欢迎下方评论区留言»

### Builds with empty slots

- 不熄曜日 «450级»: 卡牌, 耳坠
- 传承之龙 «450级»: 卡牌, 耳坠
- 凌空械羽 «450级»: 卡牌, 耳坠
- 北境公主 «450级弹射流»: 耳坠
- 北境公主 «450工具人»: 耳坠
- 双鸣追猎 «450级»: 卡牌, 耳坠
- 司正天座 «蹲»: 头盔, 卡牌, 衣服, 戒指, 腰带, 鞋子, 副手, 护手
- 圣翼降临 «450级»: 卡牌, 耳坠
- 墨凝清影 «450级»: 卡牌, 耳坠
- 墨凝清影 «800级»: 卡牌
- 夜宴霆光 «450级»: 卡牌, 耳坠
- 夜行暹罗 «450级»: 卡牌, 耳坠
- 夜行暹罗 «帆船800级»: 卡牌
- 天邪魅影 «450级»: 卡牌, 耳坠, 戒指, 副手
- 婆娑轮舞 «450级»: 卡牌, 耳坠
- 拂光破雪 «450级»: 卡牌, 耳坠
- 月渊龙女 «450级»: 卡牌, 耳坠, 徽章
- 炽焰降生 «450级»: 卡牌, 耳坠
- 炽焰降生 «旅途800级»: 鞋子
- 爱恋花见 «＜3血阶»: 戒指
- 爱恋花见 «≥3血阶»: 卡牌
- 玉尘灵仙 «450级»: 卡牌, 耳坠, 徽章
- 玉面九尾 «450级CD装»: 卡牌, 耳坠
- 王国猎手 «帆船辅助»: 耳坠
- 璨然银龙 «450级»: 卡牌, 耳坠, 戒指, 鞋子, 副手
- 璨然银龙 «800级»: 卡牌, 鞋子
- 百花旅者 «血包»: 护手
- 秽翼魔女 «1000级PVP»: 卡牌
- 绚彩星绘 «450级»: 卡牌, 耳坠
- 绚彩星绘 «800级»: 卡牌
- 绞刃流火 «450级»: 卡牌, 耳坠
- 绮夜梦影 «蹲一个450配装，欢迎下方评论区留言»: 头盔, 项链, 卡牌, 耳坠, 衣服, 戒指, 腰带, 圣物, 裤子, 徽章, 鞋子, 副手, 护手
- 绯晶战影 «450配装»: 卡牌, 耳坠, 鞋子
- 绯红荆棘 «450级»: 卡牌, 耳坠
- 绿森山灵 «450级»: 卡牌, 耳坠
- 自由炮手 «450级»: 项链, 卡牌, 耳坠
- 蚀骨魂龙 «450级»: 卡牌, 耳坠
- 蚀骨魂龙 «1000级»: 卡牌, 耳坠
- 裁决圣锤 «蹲一个450配装，欢迎下方评论区留言»: 头盔, 项链, 卡牌, 耳坠, 衣服, 戒指, 腰带, 圣物, 裤子, 徽章, 鞋子, 副手, 护手
- 迷迭妖精 «450级CD流»: 卡牌, 耳坠
- 金蜂破茧 «蹲一个450配装，欢迎下方评论区留言»: 头盔, 项链, 卡牌, 耳坠, 衣服, 戒指, 腰带, 圣物, 裤子, 徽章, 鞋子, 副手, 护手
- 银刃之誓 «450级»: 卡牌, 耳坠, 护手
- 银刃之誓 «1000级»: 头盔, 卡牌, 衣服, 腰带, 鞋子, 武器
- 长辉照夜 «450级»: 项链, 卡牌, 耳坠, 徽章
- 雪月公主 «蹲一个450配装，欢迎下方评论区留言»: 头盔, 项链, 卡牌, 耳坠, 衣服, 戒指, 腰带, 圣物, 裤子, 徽章, 鞋子, 副手, 护手
- 霓裳若仙 «450»: 卡牌, 耳坠
- 青鸾巽羽 «450/700级»: 耳坠
- 飞焰铃舞 «蹲»: 头盔, 项链, 卡牌, 耳坠, 衣服, 戒指, 腰带, 圣物, 裤子, 徽章, 鞋子, 副手, 护手
- 魂棺语者 «450配装»: 卡牌, 耳坠
- 黑衫刃影 «450级»: 卡牌, 耳坠

### Per-character notes

- 不祥怨灵: no 黑卫配装 template on the page
- 不祥怨灵: no 推荐符文 template on the page
- 不祥怨灵: no 黑卫血阶 template on the page
- 不祥怨灵: no 黑卫遗物 template on the page
- 冰封之心: no 黑卫配装 template on the page
- 冰封之心: no 推荐符文 template on the page
- 冰封之心: no 黑卫血阶 template on the page
- 凛冬魔女: no 黑卫技能 template on the page
- 凛冬魔女: no 黑卫配装 template on the page
- 凛冬魔女: no 推荐符文 template on the page
- 凛冬魔女: no 推荐黑石 template on the page
- 凛冬魔女: no 黑卫血阶 template on the page
- 凛冬魔女: no 黑卫遗物 template on the page
- 北境公主: no 推荐符文 template on the page
- 北境公主: no 黑卫血阶 template on the page
- 北境公主: no 黑卫遗物 template on the page
- 双子之盾: no 黑卫配装 template on the page
- 双子之盾: no 推荐符文 template on the page
- 双子之盾: no 黑卫血阶 template on the page
- 双子之盾: no 黑卫遗物 template on the page
- 双鸣追猎: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 唤霜海灵: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 圣翼降临: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 地精妖术师: no 黑卫技能 template on the page
- 地精妖术师: no 黑卫配装 template on the page
- 地精妖术师: no 推荐符文 template on the page
- 地精妖术师: no 推荐黑石 template on the page
- 地精妖术师: no 黑卫血阶 template on the page
- 地精妖术师: no 黑卫遗物 template on the page
- 夺魂之镰: no 黑卫配装 template on the page
- 夺魂之镰: no 推荐符文 template on the page
- 夺魂之镰: no 黑卫血阶 template on the page
- 夺魂之镰: no 黑卫遗物 template on the page
- 妖刀: no 黑卫配装 template on the page
- 妖刀: no 推荐符文 template on the page
- 妖刀: no 推荐黑石 template on the page
- 妖刀: no 黑卫血阶 template on the page
- 婆娑轮舞: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 审判使者: no 黑卫配装 template on the page
- 审判使者: no 推荐符文 template on the page
- 审判使者: no 推荐黑石 template on the page
- 审判使者: no 黑卫血阶 template on the page
- 密林之眼: no 黑卫配装 template on the page
- 密林之眼: no 推荐符文 template on the page
- 密林之眼: no 黑卫血阶 template on the page
- 密林之眼: no 黑卫遗物 template on the page
- 封魔利爪: no 黑卫配装 template on the page
- 封魔利爪: no 推荐符文 template on the page
- 封魔利爪: no 黑卫血阶 template on the page
- 封魔利爪: no 黑卫遗物 template on the page
- 巡林游侠: no 黑卫配装 template on the page
- 巡林游侠: no 推荐符文 template on the page
- 巡林游侠: no 黑卫血阶 template on the page
- 巡林游侠: no 黑卫遗物 template on the page
- 帝国之剑: no 黑卫配装 template on the page
- 帝国之剑: no 推荐符文 template on the page
- 帝国之剑: no 黑卫血阶 template on the page
- 帝国之剑: no 黑卫遗物 template on the page
- 异国商人: no 黑卫配装 template on the page
- 异国商人: no 推荐符文 template on the page
- 异国商人: no 黑卫血阶 template on the page
- 异国商人: no 黑卫遗物 template on the page
- 御刃神锋: no 黑卫配装 template on the page
- 御刃神锋: no 推荐符文 template on the page
- 御刃神锋: no 推荐黑石 template on the page
- 御刃神锋: no 黑卫血阶 template on the page
- 构装守卫: no 黑卫配装 template on the page
- 构装守卫: no 推荐符文 template on the page
- 构装守卫: no 黑卫血阶 template on the page
- 构装守卫: no 黑卫遗物 template on the page
- 欢愉魔女: no 黑卫配装 template on the page
- 欢愉魔女: no 推荐符文 template on the page
- 欢愉魔女: no 黑卫血阶 template on the page
- 欢愉魔女: no 黑卫遗物 template on the page
- 深庭玫瑰: no 黑卫配装 template on the page
- 深庭玫瑰: no 推荐符文 template on the page
- 深庭玫瑰: no 黑卫血阶 template on the page
- 深庭玫瑰: no 黑卫遗物 template on the page
- 渡鸦魁首: no 黑卫配装 template on the page
- 渡鸦魁首: no 推荐符文 template on the page
- 渡鸦魁首: no 黑卫血阶 template on the page
- 渡鸦魁首: no 黑卫遗物 template on the page
- 灰袍法师: no 黑卫配装 template on the page
- 灰袍法师: no 推荐符文 template on the page
- 灰袍法师: no 黑卫血阶 template on the page
- 灰袍法师: no 黑卫遗物 template on the page
- 灵刃之主: no 黑卫配装 template on the page
- 灵刃之主: no 推荐符文 template on the page
- 灵刃之主: no 推荐黑石 template on the page
- 灵刃之主: no 黑卫血阶 template on the page
- 炙光之舞: no 黑卫血阶 template on the page
- 炽焰降生: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 烈阳将军: no 黑卫配装 template on the page
- 烈阳将军: no 推荐符文 template on the page
- 烈阳将军: no 黑卫血阶 template on the page
- 烈阳将军: no 黑卫遗物 template on the page
- 王国猎手: no 推荐符文 template on the page
- 王国猎手: no 黑卫血阶 template on the page
- 王国猎手: no 黑卫遗物 template on the page
- 白龙: no 黑卫配装 template on the page
- 白龙: no 推荐符文 template on the page
- 白龙: no 黑卫血阶 template on the page
- 白龙: no 黑卫遗物 template on the page
- 百花旅者: no 黑卫血阶 template on the page
- 神之嫡子: no 黑卫配装 template on the page
- 神之嫡子: no 推荐符文 template on the page
- 神之嫡子: no 推荐黑石 template on the page
- 神之嫡子: no 黑卫血阶 template on the page
- 秘境仙灵: no 黑卫配装 template on the page
- 秘境仙灵: no 推荐符文 template on the page
- 秘境仙灵: no 黑卫血阶 template on the page
- 秘境仙灵: no 黑卫遗物 template on the page
- 秘术导师: no 黑卫配装 template on the page
- 秘术导师: no 推荐符文 template on the page
- 秘术导师: no 黑卫血阶 template on the page
- 秘术导师: no 黑卫遗物 template on the page
- 秽翼魔女: 推荐符文: 主符文 is empty, so the wiki page shows «暂无» although 辅助符文 is set
- 纯净史莱姆: no 黑卫配装 template on the page
- 纯净史莱姆: no 推荐符文 template on the page
- 纯净史莱姆: no 黑卫血阶 template on the page
- 纯净史莱姆: no 黑卫遗物 template on the page
- 纯白之羽: no 推荐符文 template on the page
- 纯白之羽: no 黑卫血阶 template on the page
- 纵火妖精: no 黑卫配装 template on the page
- 纵火妖精: no 推荐符文 template on the page
- 纵火妖精: no 黑卫血阶 template on the page
- 纵火妖精: no 黑卫遗物 template on the page
- 自由炮手: no 推荐符文 template on the page
- 诅咒之王: no 黑卫配装 template on the page
- 诅咒之王: no 推荐符文 template on the page
- 诅咒之王: no 黑卫血阶 template on the page
- 诅咒之王: no 黑卫遗物 template on the page
- 长夜之影: no 黑卫配装 template on the page
- 长夜之影: no 推荐符文 template on the page
- 长夜之影: no 黑卫血阶 template on the page
- 长夜之影: no 黑卫遗物 template on the page

## Links of build items and recommended runes

Lookup order for a name not in the category downloads: wiki `action=query&titles=…&redirects` (50 per request) → wiki `list=search` → game DB (`template/*.xml`, `language/json`) by exact Chinese name → similar existing names (difflib, only as `possible_match`, status `unverified`, never linked). A full-width comma `，` inside a slot value is treated as a separator of variants. Raw answers: `data/raw/missing_lookup.json` (written by `scraper/resolve_missing.py`).

| | before (category pages only) | after (+ pages found by lookup) |
|---|---|---|
| build item names linked | 891 / 1108 | 895 / 1110 |
| distinct unlinked build item names | 105 | 103 |
| …of the unlinked build item names: found in the game DB (game_id recorded) | — | 99 |
| recommended rune names linked | 249 / 257 | 253 / 261 |

«before» = step 2: names exactly as written on the pages, only the category pages of step 1. «after» = names split on `，` + pages found by the lookup. Totals differ because a split name counts twice.

### Wiki pages found by the lookup and downloaded (`data/raw/extra_items`)

| page | used as | requested as |
|---|---|---|
| 扩散魔链 | empty page (no wikitext) — not linked | 扩散魔链 |
| 狩猎徽章 | already in Category (gear); was unlinked only because of a 「，」 in the build | 狩猎徽章 |
| 界卫魔面 | already in Category (gear); was unlinked only because of a 「，」 in the build | 界卫魔面 |
| 祭仪羽冠 | already in Category (gear); was unlinked only because of a 「，」 in the build | 祭仪羽冠 |
| 霆霓猩红血印 | already in Category (gear); was unlinked only because of a 「，」 in the build | 霆霓猩红血印 |

### Still unlinked, with reasons

| name | kind | reason | possible match (unverified) | game DB ids | wiki search hits | used in |
|---|---|---|---|---|---|---|
| 不死鸟耳坠 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90083 text 60195 | 忘却迷境, 绯红荆棘, 忘却迷境-凛风雪原 | 绯红荆棘 / «旅途800级» / 耳坠; 绯红荆棘 / «帆船800级» / 耳坠 |
| 云起春鸣 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90355 text 76606 | 墨凝清影 | 墨凝清影 / «800级» / 武器 |
| 光耀星华 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90360 text 78078 | 圣翼降临 | 圣翼降临 / «800级» / 武器 |
| 共生护腿 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90310 text 63592 | 迷雾山脉-深层幻境攻略, 炙光之舞 | 炙光之舞 / «800减抗装» / 裤子 |
| 共生耳环 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90307 text 63589 | 迷雾山脉-深层幻境攻略, 炙光之舞, 幸运装备 | 炙光之舞 / «800减抗装» / 耳坠 |
| 决斗大师的帽子 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#11022 text 3832 | 百花旅者, 璨然银龙, 分解装备 | 璨然银龙 / «450级» / 头盔; 璨然银龙 / «800级» / 头盔; 百花旅者 / «血包» / 头盔 |
| 凛冬 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13018 text 3942 | 凛冬祈雪, 凛冬魔女, 炙光之舞 | 炙光之舞 / «800减抗装» / 圣物 |
| 千印结牌 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95019 text 82512 | 长辉照夜, 青鸾巽羽 | 长辉照夜 / «1000级» / 卡牌; 青鸾巽羽 / «1000级» / 卡牌 |
| 古老魔盾 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#5020 text 53826 | 玉面九尾, 百花旅者, 墨凝清影 | 墨凝清影 / «450级» / 副手; 爱恋花见 / «＜3血阶» / 副手; 玉面九尾 / «450级CD装» / 副手; 百花旅者 / «血包» / 副手 (+1) |
| 咒法魔手 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90298 text 63580 | 迷雾山脉-深层幻境攻略, 北境公主 | 北境公主 / «450工具人» / 护手 |
| 噬魂血盔 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95021 text 82516 | 长辉照夜, 千宵月守 | 千宵月守 / «1000级» / 头盔; 长辉照夜 / «1000级» / 头盔 |
| 复苏徽识 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#7007 text 54995 | 玉面九尾, 百花旅者, 墨凝清影 | 墨凝清影 / «450级» / 徽章; 玉面九尾 / «450级CD装» / 徽章; 百花旅者 / «血包» / 徽章; 绚彩星绘 / «450级» / 徽章 (+1) |
| 天殛绝刃 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90388 text 90567 | 夜宴霆光 | 夜宴霆光 / «450级» / 武器 |
| 夺魂大盾 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90013 text 55964 | 炙光之舞 | 炙光之舞 / «800减抗装» / 副手 |
| 守护之利刃 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13050 text 55664 | 炙光之舞, 冷却装备, 幸运装备 | 炙光之舞 / «800减抗装» / 圣物 |
| 幽冥初水 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90323 text 69056 | 氪金攻略, 拂光破雪, 战争之蹄 | 不熄曜日 / «800级» / 护手; 传承之龙 / «800级» / 护手; 凌空械羽 / «800级» / 护手; 千宵月守 / «1000级» / 护手 (+10) |
| 怒焰圣戒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90292 text 63574 | 迷雾山脉-深层幻境攻略, 炙光之舞 | 炙光之舞 / «800减抗装» / 戒指 |
| 急速之牌 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90210 text 62167 | 忘却迷境, 北境公主, 百花旅者 | 北境公主 / «450级弹射流» / 卡牌; 北境公主 / «450工具人» / 卡牌; 百花旅者 / «血包» / 卡牌 |
| 恋血钩坠 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90046 text 58796 | 王国猎手 | 王国猎手 / «帆船辅助» / 项链 |
| 扩散魔链 | gear | wiki page exists but is empty; exists in the game DB | — | tpl_sc_equipment#90201 text 62158 | — | 炙光之舞 / «800减抗装» / 项链 |
| 星痕项链 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4003 text 4068 | 纯白之羽, 绚彩星绘, 幸运装备 | 纯白之羽 / «大招无敌流» / 项链; 绚彩星绘 / «450级» / 项链; 霓裳若仙 / «450» / 项链 |
| 智者足具 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#15016 text 3983; tpl_sc_equipment#15032 text 3983 | 玉面九尾, 新手起号, 墨凝清影 | 墨凝清影 / «450级» / 鞋子; 爱恋花见 / «＜3血阶» / 鞋子; 爱恋花见 / «≥3血阶» / 鞋子; 玉面九尾 / «450级CD装» / 鞋子 (+3) |
| 曜晶之戒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2034 text 56720 | 纯白之羽, 分解装备, 回怒装备 | 纯白之羽 / «大招无敌流» / 戒指 |
| 月辉·东方锦靴 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#15043 text 4004 | 炙光之舞 | 炙光之舞 / «800减抗装» / 鞋子 |
| 月辉·凝辉 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#10092 text 3800 | 锻造, 玉面九尾, 爱恋花见 | 爱恋花见 / «＜3血阶» / 武器; 爱恋花见 / «≥3血阶» / 武器; 玉面九尾 / «450级CD装» / 武器; 迷迭妖精 / «450级CD流» / 武器 |
| 月辉·疾雷之书 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#10087 text 3795 | 锻造, 纯白之羽, 冷却装备 | 纯白之羽 / «大招无敌流» / 武器 |
| 月辉·白羽橙晶 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13034 text 3958 | 圣翼降临, 冷却装备 | 圣翼降临 / «450级» / 圣物 |
| 月辉·达特穆尔酋长披风 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#12078 text 3914 | 锻造, 百花旅者, 璨然银龙 | 璨然银龙 / «450级» / 衣服; 百花旅者 / «血包» / 衣服 |
| 极寒御手 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90020 text 56456 | 北境公主 | 北境公主 / «450级弹射流» / 护手 |
| 极寒飞雪 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2016 text 4050 | 不熄曜日 | 不熄曜日 / «450级» / 戒指 |
| 死眠短裤 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95033 text 82540 | 司正天座 | 司正天座 / «蹲» / 裤子 |
| 沧澜天剑 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90387 text 89458 | 月渊龙女 | 月渊龙女 / «450级» / 武器; 月渊龙女 / «1000级» / 专武 |
| 法师长靴 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#15011 text 3978; tpl_sc_equipment#15027 text 3978 | 炙光之舞 | 炙光之舞 / «800减抗装» / 鞋子 |
| 法球大师 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90097 text 60205 | 雪月公主, 不熄曜日, 王室剑徽 | 不熄曜日 / «800级» / 鞋子 |
| 海晶项链 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4011 text 8333 | 分解装备, 炽焰降生, 幸运装备 | 千宵月守 / «450/700级» / 项链; 炽焰降生 / «450级» / 项链 |
| 淬羽霜刃 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90370 text 80639 | 拂光破雪 | 拂光破雪 / «800级» / 武器 |
| 游猎之心 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2037 text 55096 | 蚀骨魂龙 | 蚀骨魂龙 / «450级» / 戒指 |
| 湛蓝护盾 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#5022 text 53828 | 北境公主, 怒气装备 | 北境公主 / «450级弹射流» / 副手; 北境公主 / «450工具人» / 副手 |
| 火妖怒焰 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2017 text 4051 | 圣翼降临 | 圣翼降临 / «450级» / 戒指 |
| 灵龙契约 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95050 text 85342 | 月渊龙女 | 月渊龙女 / «1000级» / 卡牌 |
| 炎护腰带 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#1009 text 4025 | 分解装备, 自由炮手, 璨然银龙 | 璨然银龙 / «450级» / 腰带; 自由炮手 / «450级» / 腰带 |
| 炽链斩魂 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90358 text 77352 | 秽翼魔女 | 秽翼魔女 / «1000级PVP» / 专武 |
| 焰刃焚心 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90386 text 88592 | 天邪魅影 | 天邪魅影 / «450级» / 武器 |
| 牛皮护手 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#3006 text 4061 | 玉尘灵仙, 分解装备, 长辉照夜 | 月渊龙女 / «450级» / 护手; 玉尘灵仙 / «450级» / 护手; 玉尘灵仙 / «1000级» / 护手; 蚀骨魂龙 / «450级» / 护手 (+2) |
| 狂法者 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90012 text 55963 | 蚀骨魂龙, 北境公主, 凌空械羽 | 凌空械羽 / «450级» / 头盔; 北境公主 / «450级弹射流» / 头盔; 北境公主 / «450工具人» / 头盔; 蚀骨魂龙 / «450级» / 头盔 (+1) |
| 狂猎之腰 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#1023 text 54203 | 玉尘灵仙, 长辉照夜, 蚀骨魂龙 | 月渊龙女 / «450级» / 腰带; 玉尘灵仙 / «450级» / 腰带; 王国猎手 / «帆船辅助» / 腰带; 蚀骨魂龙 / «450级» / 腰带 (+2) |
| 狂铁驭手 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#3033 text 55196 | 婆娑轮舞 | 婆娑轮舞 / «450级» / 护手 |
| 猎杀时刻 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2031 text 54368 | 迷雾山脉, 迷雾山脉-迷雾幻境, 魂棺语者 | 月渊龙女 / «450级» / 戒指; 绯晶战影 / «450配装» / 戒指; 蚀骨魂龙 / «450级» / 戒指; 魂棺语者 / «450配装» / 戒指 |
| 猎猫之戒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90177 text 61835 | 传承之龙 | 传承之龙 / «450级» / 戒指 |
| 盾形徽章 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13009 text 3933 | 怒气装备, 司正天座 | 司正天座 / «蹲» / 圣物 |
| 碎星项链 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4013 text 8335 | 百花旅者, 怒气装备 | 百花旅者 / «血包» / 项链 |
| 祈祷系带 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#1029 text 54209 | 分解装备, 魂棺语者, 绯晶战影 | 绯晶战影 / «450配装» / 腰带; 魂棺语者 / «450配装» / 腰带 |
| 神圣守护 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#11020 text 3830 | 纯白之羽 | 纯白之羽 / «大招无敌流» / 头盔 |
| 穿杨圣裁 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90318 text 64403 | 战争之蹄 | 战争之蹄 / «800级» / 武器 |
| 精灵飞羽 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13003 text 3927 | 北境公主, 百花旅者, 分解装备 | 北境公主 / «450级弹射流» / 圣物; 北境公主 / «450工具人» / 圣物; 夜行暹罗 / «450级» / 圣物; 天邪魅影 / «450级» / 圣物 (+1) |
| 紫怒之盾 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90263 text 63093 | 炙光之舞, 传承之龙 | 传承之龙 / «450级» / 副手; 炙光之舞 / «800减抗装» / 副手 |
| 纯净涤魂 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90272 text 63102 | 纯白之羽 | 纯白之羽 / «大招无敌流» / 武器 |
| 纯净炙金 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#1020 text 53821 | 炙光之舞 | 炙光之舞 / «800减抗装» / 腰带 |
| 纯白澄晶 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90005 text 55872 | 纯白之羽 | 纯白之羽 / «大招无敌流» / 项链 |
| 结灯焕彩 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90384 text 86470 | 霓裳若仙 | 霓裳若仙 / «450» / 武器; 霓裳若仙 / «700/1000级» / 专武 |
| 绝对冰霜 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95010 text 82494 | 千宵月守, 月渊龙女 | 千宵月守 / «1000级» / 衣服; 月渊龙女 / «1000级» / 衣服 |
| 绯炎绮瑰 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90368 text 79408 | 不熄曜日 | 不熄曜日 / «800级» / 武器 |
| 聚灵腰带 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95028 text 82530 | 月渊龙女 | 月渊龙女 / «1000级» / 腰带 |
| 舍身狂袭 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90087 text 60196 | 绯红荆棘, 北境公主, 千宵月守 | 北境公主 / «450工具人» / 腰带; 千宵月守 / «1000级» / 腰带; 绯红荆棘 / «旅途800级» / 腰带; 绯红荆棘 / «帆船800级» / 腰带 |
| 花间圣戒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90053 text 59200 | 百花旅者 | 百花旅者 / «血包» / 戒指 |
| 苍狼骑士带 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95057 text 85347 | 爱恋花见 | 爱恋花见 / «＜3血阶» / 腰带; 爱恋花见 / «≥3血阶» / 腰带 |
| 萧瑟鸣锋 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90372 text 81485 | 玉尘灵仙 | 玉尘灵仙 / «1000级» / 专武 |
| 蛇灵之怒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90022 text 56452 | 炽焰降生 | 炽焰降生 / «450级» / 项链 |
| 血钩吊坠 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4004 text 4069 | 辉耀之链, 幽影绝链, 蚀骨魂龙 | 月渊龙女 / «450级» / 项链; 蚀骨魂龙 / «450级» / 项链 |
| 贵族手套 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#3011 text 8325 | 纯白之羽, 绚彩星绘, 回怒装备 | 纯白之羽 / «大招无敌流» / 护手; 绚彩星绘 / «450级» / 护手; 霓裳若仙 / «450» / 护手 |
| 蹁跹蝶翼 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90034 text 57360 | 炙光之舞 | 炙光之舞 / «800减抗装» / 武器 |
| 辅助之勇气 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#13051 text 55666 | 纯白之羽, 幸运装备 | 纯白之羽 / «大招无敌流» / 圣物 |
| 辅助之愿 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90286 text 63325 | 墨凝清影, 绚彩星绘, 霓裳若仙 | 墨凝清影 / «800级» / 圣物; 绚彩星绘 / «800级» / 圣物; 霓裳若仙 / «700/1000级» / 徽章 |
| 连锁雷帽 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90101 text 60209 | 夜行暹罗, 忘却迷境-凛风雪原 | 夜行暹罗 / «旅途800级» / 头盔 |
| 鏖战金锋 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90383 text 86151 | 绯晶战影 | 绯晶战影 / «450配装» / 武器 |
| 铁卫魔手 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90300 text 63582 | 迷雾山脉-深层幻境攻略, 炙光之舞 | 炙光之舞 / «800减抗装» / 护手 |
| 铁铸束腰 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#1014 text 4030 | 玉尘灵仙, 长辉照夜, 青鸾巽羽 | 月渊龙女 / «450级» / 腰带; 玉尘灵仙 / «450级» / 腰带; 王国猎手 / «帆船辅助» / 腰带; 长辉照夜 / «450级» / 腰带 (+1) |
| 雪月 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2033 text 54705 | 雪月公主, 传承之龙, 旅途故事-吾心如火攻略 | 北境公主 / «450级弹射流» / 戒指 |
| 雷光庇护 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95053 text 85345 | 月渊龙女 | 月渊龙女 / «1000级» / 头盔 |
| 霜之徽印 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90301 text 63583 | 迷雾山脉-深层幻境攻略, 北境公主 | 北境公主 / «450工具人» / 徽章 |
| 霜之秘戒 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90291 text 63573 | 迷雾山脉-深层幻境攻略, 北境公主 | 北境公主 / «450工具人» / 戒指 |
| 霜雨 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#10037 text 3754 | 忘却迷境攻略, 王国猎手 | 王国猎手 / «帆船辅助» / 武器 |
| 静默之盔 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90102 text 60210 | 炽焰降生, 忘却迷境-凛风雪原 | 炽焰降生 / «旅途800级» / 头盔 |
| 飞星如焰 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90389 text 91620 | 飞焰铃舞 | 飞焰铃舞 / «蹲» / 武器 |
| 骸装蔷薇 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90316 text 64399 | 绯红荆棘 | 绯红荆棘 / «旅途800级» / 武器; 绯红荆棘 / «帆船800级» / 武器 |
| 魔人之指 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#2012 text 4046 | 百花旅者, 怒气装备 | 百花旅者 / «血包» / 戒指 |
| 魔弦护腿 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90309 text 63591 | 迷雾山脉-深层幻境攻略, 纯白之羽, 炙光之舞 | 炙光之舞 / «800减抗装» / 裤子; 爱恋花见 / «＜3血阶» / 裤子; 爱恋花见 / «≥3血阶» / 裤子; 百花旅者 / «血包» / 裤子 (+2) |
| 魔弦耳环 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90306 text 63588 | 迷雾山脉-深层幻境攻略, 纯白之羽, 炙光之舞 | 千宵月守 / «450/700级» / 耳坠; 千宵月守 / «1000级» / 耳坠; 炙光之舞 / «800减抗装» / 耳坠; 百花旅者 / «血包» / 耳坠 (+2) |
| 魔弹亡语 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90222 text 62179 | 传承之龙 | 传承之龙 / «800级» / 衣服 |
| 魔弹咆哮 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90223 text 62180 | 传承之龙, 冷却装备 | 传承之龙 / «800级» / 腰带 |
| 魔弹尖啸 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90225 text 62182 | 传承之龙 | 传承之龙 / «800级» / 鞋子 |
| 魔弹鹰鸣 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90221 text 62178 | 传承之龙 | 传承之龙 / «800级» / 头盔 |
| 魔法师之链 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4017 text 8339 | 青鸾巽羽, 回怒装备 | 青鸾巽羽 / «450/700级» / 项链 |
| 魔球卡牌 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90212 text 62169 | 忘却迷境, 战争之蹄, 不熄曜日 | 不熄曜日 / «800级» / 卡牌; 千宵月守 / «450/700级» / 卡牌; 夜行暹罗 / «旅途800级» / 卡牌; 战争之蹄 / «800级» / 卡牌 |
| 魔眼吊坠 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#4006 text 4071 | 千宵月守 | 千宵月守 / «450/700级» / 项链 |
| 黑色汪洋 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90324 text 69057 | 拂光破雪, 不熄曜日, 绞刃流火 | 不熄曜日 / «800级» / 项链; 千宵月守 / «1000级» / 项链; 拂光破雪 / «800级» / 项链; 月渊龙女 / «1000级» / 项链 (+4) |
| 黑金护甲 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#95012 text 82498 | 青鸾巽羽, 千宵月守, 月渊龙女 | 千宵月守 / «1000级» / 衣服; 月渊龙女 / «1000级» / 衣服; 青鸾巽羽 / «1000级» / 衣服 |
| 龙猎大盾 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#5026 text 54127 | 秽翼魔女, 怒气装备 | 秽翼魔女 / «1000级PVP» / 副手 |
| 龙脊寒枪 | gear | no wiki page; exists in the game DB | — | tpl_sc_equipment#90385 text 87822 | 璨然银龙 | 璨然银龙 / «450级» / 武器; 璨然银龙 / «800级» / 武器 |
| 任意太古装备 | gear | not an item name | — | — | 霓裳若仙, 爱恋花见, 千宵月守 | 千宵月守 / «1000级» / 卡牌; 爱恋花见 / «＜3血阶» / 卡牌; 霓裳若仙 / «700/1000级» / 头盔; 霓裳若仙 / «700/1000级» / 卡牌 (+3) |
| 宗室礼鞋 | gear | probably a typo — candidate below (unverified) | 宗室礼靴 (gear-1282; similar name in gear.json) | — | 绯红荆棘 | 绯红荆棘 / «帆船800级» / 鞋子 |
| 怒焰微印 | gear | probably a typo — candidate below (unverified) | 怒焰徽印 (no id; similar name in game DB) | — | 炙光之舞 | 炙光之舞 / «800减抗装» / 徽章 |
| 聚能铠甲 | gear | probably a typo — candidate below (unverified) | 聚魔铠甲 (gear-1284; similar name in gear.json) | — | 夜行暹罗 | 夜行暹罗 / «帆船800级» / 衣服 |
| 逐日 | runes | probably a typo — candidate below (unverified) | 逐日者 (rune-1409; similar name in runes.json) | — | 逐日者, 异常状态, 战争之蹄 | 战争之蹄 / 主符文 (option of «断钢/逐日») |
| 铁荆 | runes | probably a typo — candidate below (unverified) | 铁棘 (rune-1420; similar name in runes.json) | — | 战争之蹄, 长辉照夜, 玉尘灵仙 | 婆娑轮舞 / 辅助符文; 战争之蹄 / 辅助符文; 玉尘灵仙 / 辅助符文; 长辉照夜 / 辅助符文 |
| 锻钢 | runes | probably a typo — candidate below (unverified) | 断钢 (rune-1997; similar name in runes.json) | — | 长辉照夜, 玉尘灵仙, 蚀骨魂龙 | 玉尘灵仙 / 主符文 (option of «锻钢/绝刃»); 蚀骨魂龙 / 主符文 (option of «锻钢/绝刃»); 长辉照夜 / 主符文 (option of «锻钢/绝刃») |

Totals: no wiki page; exists in the game DB: 99, probably a typo — candidate below (unverified): 6, not an item name: 1

Game DB used: `data/raw/game_db/08.database` (45283 text entries, 1226 item names in equipment/rune/heirloom/blackStone tables). Only ids are written to data/zh; see `docs/GAMEDB.md`.

## Build tab labels (`tier_kind`)

- level: 61, special: 13
- special «≥3血阶» ×1: for blood rank 3 or higher
- special «大招无敌流» ×1: playstyle: ultimate + invincibility
- special «帆船辅助» ×1: support build for 帆船 (sailing mode)
- special «血包» ×1: 'blood pack' build (healing / HP support role)
- special «蹲» ×2: placeholder ('waiting'): build not filled in yet
- special «蹲一个450配装，欢迎下方评论区留言» ×6: placeholder: editors ask for a 450 build in the comments
- special «＜3血阶» ×1: for blood rank below 3

Linked item whose `部位` differs from the build slot:

- 爱恋花见 / «＜3血阶» / 副手: 源辉石盾 has 部位=徽章
- 绚彩星绘 / «450级» / 副手: 源辉石盾 has 部位=徽章
- 迷迭妖精 / «450级CD流» / 副手: 源辉石盾 has 部位=徽章
- 银刃之誓 / «450级» / 徽章: 陷阵徽章 has 部位=项链
- 霓裳若仙 / «450» / 副手: 源辉石盾 has 部位=徽章

## Other unresolved links

- Character factions not in factions.json: none
- Factions without threshold effects on page 阵线 (`thresholds: null`): 咒印回响, 圣盾, 天人, 影之使魔, 死战, 洞穿, 灵术叠咏, 磐石, 血契制约, 铁血, 铁骨, 锐意
- Black stones in character pages not in black_stones.json: none
- Relics whose `黑卫名称` is not a downloaded character: none

## Pages / parts that did not parse cleanly

- none

### Unknown templates left as raw text inside values

- none

### Templates ignored because they are commented out

- 冰封之心: 推荐符文
- 冰封之心: 黑卫羁绊好感度
- 唤霜海灵: 秘术战格
- 审判使者: 推荐符文, 推荐黑石
- 御刃神锋: 推荐符文, 推荐黑石
- 纯白之羽: 推荐符文
- 自由炮手: 推荐符文

## Source discrepancies and remarks

- 黑石 雷影狼 (8): page «刺杀职业黑卫拥有【闪电之剑：攻击向敌方射出一支闪电箭，对其造成造成408+(50%-60%)*物理&法术强度的闪电伤害，随后这支闪电箭会继续攻击它周围最近的敌人。闪电箭每跳跃一次，伤害就减少30%，最多可攻击6个自标。】» vs 模板:推荐黑石 «刺杀职业黑卫拥有【闪电之剑：攻击向敌方射出一支闪电箭，对其造成造成408+(50%-60%)*物理&法术强度的闪电伤害，随后这支闪电箭会继续攻击它周围最近的敌人。闪电箭每跳跃一次，伤害就减少30%，最多可攻击6个自标。】效果»
- 黑石 雪甲虫 (8): page «开启冰霜护盾并获得3个冰霜之球，抵御3次伤害，并对其伤害来源施加冰缓效果，持续4秒，冷却30秒» vs 模板:推荐黑石 «开启冰霜护盾并获得3个冰霜之球，抵御3次伤害，并对其伤害来源施加冰缓效果，持续4秒，冷却30秒示穿戴中的道具»
- 黑石 诅咒灵 (8): page «物理伤害暴击时有3%几率时目标处于虚弱状态，持续4秒» vs 模板:推荐黑石 «物理伤害暴击时有3%几率时目标处于虚弱状态，持续4秒。»
- 黑石 金乌 (8): page «治疗目标同时恢复目标等同治疗值10%的护盾» vs 模板:推荐黑石 «治疗目标同时恢复目标等同治疗值10%的护盾。»
- 夜行暹罗 build «帆船800级» 头盔: «祭仪羽冠，界卫魔面» split on the full-width comma into ['祭仪羽冠', '界卫魔面']
- 夜行暹罗 build «帆船800级» 徽章: «霆霓猩红血印，狩猎徽章» split on the full-width comma into ['霆霓猩红血印', '狩猎徽章']

## Tier lists

- PVE: ranked 44, not_ranked 32
- PVP: ranked 45, not_ranked 31

