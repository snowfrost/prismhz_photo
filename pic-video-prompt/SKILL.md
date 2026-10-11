---
name: pic-video-prompt
description: 图像×视频提示词总导演（原rizafeng-mingzhu-portrait升级重组）。一条路由覆盖两条大线：①图像线——四风格名著人像（日杂/怀旧日常/电影剧照/杂志企划×86西游/87红楼/94三国/金庸TVB等）+东方巨物巨构天宫+鎏金水墨+镜花水月+簪花女郎+港风武侠+邵氏武侠+岩井俊二青春+西幻帝国皇室+超现实电影关键帧；②视频线——强剧情分镜导演、韩系女团资产与MV、光感小清新短片、中式美学短片、复古DV日常、手机Vlog。当用户要任何"写提示词/出图提示词/视频分镜/图生视频提示词"且涉及上述风格时使用。只写提示词，不直接生成。
agent_created: true
---

# pic-video-prompt 图像×视频提示词总导演

三层结构：本文件做总路由 → 名著人像体系走 `references/` → 19个子模块走 `modules/`（各自有独立SKILL.md与references，路由命中后**进入对应模块按其规则执行**）。

## 第一步 总路由（先于一切）

先判两件事：**媒介**（图 / 视频 / 图转视频）→ **风格域**。用户没指明就按关键词判，拿不准再问。

### A. 视频线（6个视频导演模块）

| 用户需求关键词 | 模块 | 一句话定位 |
|---|---|---|
| 剧情短片、分镜脚本、人物资产、连续性检查、生成偏差修复 | `modules/story-director` | 一句话构想→人物选项→可确认分镜→强剧情视频提示词 |
| 韩系女团、面部资产、三视图、舞蹈MV、逐镜时间线 | `modules/korean-girlgroup-casting-cn` | 韩系女团真人资产+MV提示词（Image 2/Seedream 5 Pro） |
| 5-30秒小清新短片、清透冷调、自然光感 | `modules/light-fresh-short-film` | 光感小清新短片，固定输出分镜时间轴+环境音+负面词 |
| 中式园林、东方情绪短片、含蓄人物表演、软光大光圈 | `modules/chinese-aesthetic-video-director` | 中式东方美学视频提示词编写/续写/修复 |
| 复古DV日常、生活记录、单人日常片段 | `modules/retro-dv-daily-director` | 复古DV日常短片分镜+小云雀节点配置 |
| 手机自拍Vlog、生活碎片、现场收音 | `modules/phone-vlog` | 30秒内真实手机Vlog提示词，资产一致性 |

### B. 图像线·名著人像体系（本skill原创核心，走references/）

用户点名著/经典剧角色（孙悟空、林黛玉、貂蝉、乔峰……）或明确要"日杂风/怀旧日常照/电影剧照感/杂志企划感"时，走本文件下方的**四风格名著人像流程**（风格线选择→角色锚点→七段公式→清洁渲染层），资料在 `references/01-09`。

### C. 图像线·风格美学模块（9个）

| 用户需求关键词 | 模块 | 一句话定位 |
|---|---|---|
| 东方巨构、白玉京、天宫仙境、云海宫殿 | `modules/eastern-megastructure-director` | 东方巨构MJ V8.2设计+图生视频 |
| 巨型花卉植物器物、东方巨物、人物共景 | `modules/eastern-colossal-wonder-director` | 东方巨物编译+单变量返修+批量发散 |
| 东方古典奇幻、仙侠、志怪、雾林水岸 | `modules/eastern-dream-director` | 仙侠志怪画面+图生视频 |
| 巨物天宫、中式仙宫、仙山神殿、天门月宫 | `modules/giant-celestial-palace-prompts` | 天宫巨物美学（ImageGen+MJ双输出） |
| 鎏金、液态金、金箔水墨、湿漆矿彩 | `modules/gilded-ink-fantasy-prompts` | 鎏金水墨幻想图像系统 |
| 镜花水月、中式梦核摄影、暗青白花、雾玻璃人像 | `modules/mirror-flower-water-moon-prompts` | 镜花水月梦核摄影（带/不带Moodboard双版） |
| 簪花女郎、珠光华服、牡丹花冠、金线织锦 | `modules/zanhua-lady-aesthetics-prompts` | 簪花女郎珠光宫廷风 |
| 港风复古武侠、红伞斗笠侠客、江湖风云 | `modules/hong-kong-retro-wuxia-prompts` | 港风武侠真人电影剧照 |
| 邵氏武侠、七十年代棚拍、孤独剑客、人工山水 | `modules/shaw-wuxia-image-prompts` | 邵氏电影风格（与港风武侠区分：邵氏=棚拍布景腔） |
| 岩井俊二、他眼中的她、日式校园恋爱、自然光青春 | `modules/iwai-youth-film-prompts` | 岩井俊二青春情愫系列 |
| 西幻帝国皇室、哥特皇家建筑、白金古金 | `modules/western-imperial-fantasy-prompts` | 西方帝国高奇幻视觉系统 |
| 超现实图像、电影叙事感关键帧、梦核 | `modules/surreal-cinematic-keyframe-director` | 超现实电影关键帧+图生视频 |
| 通用画面设计、电影镜头感、参考图风格迁移、2.39:1 | `modules/image-prompt-director` | 通用单幅画面设计兜底（参考图任务默认风格迁移） |

### D. 路由判定细则

1. **图带视频续接**（先出图、回传成品图再要5秒视频提示词）：eastern-* 四模块、surreal-cinematic-keyframe、giant-celestial-palace 都内置图生视频续接，直接用对应模块。
2. **港风武侠 vs 邵氏**：用户说"港风江湖/红伞斗笠/冷暖老武侠"→ `hong-kong-retro-wuxia-prompts`；说"邵氏/七十年代棚拍/人工山水"→ `shaw-wuxia-image-prompts`。混说时就近选并说明差异。
3. **名著角色 vs 风格人像**：角色锚点在 `references/02-名著角色锚点库.md` 里（或属86西游/87红楼/94三国/98水浒经典剧宇宙）→ 走B线；无角色锚点的纯风格人像（簪花女郎等）→ 走C线对应模块。
4. **跨模块组合**：先定主模块出主结构，再借次模块的风格参数（如"名著角色×鎏金水墨"= B线七段公式的[1摄影质感底座]换成鎏金水墨模块的材质语言）。组合时在输出里注明借了哪个模块的哪一层。
5. **通用兜底**：都不命中但确实是"写图像提示词"需求 → `modules/image-prompt-director`；确实是"写视频提示词" → `modules/story-director`。

## 第二步 名著人像体系（B线详细流程）

### 风格线选择（先于一切）

- **风格A 日系杂志感（日杂风）**：Kodak Portra 400 胶片感、柔和漫射光、高调低饱和、大留白、人物「慢」而静。适合情绪片、杂志内页、写真企划。
- **风格B 怀旧复古日常照**：90s/2000s 家用胶片快照（Kodak Gold/傻瓜相机/机顶直闪/影楼BTS）、暖黄褪色、高光溢出、生活流随意构图、人物「真」而鲜活。适合头像、表情包、群像。隐藏变体：50年代黑白中画幅纪实。
- **风格C 电影剧照感**：80-90年代电视剧剧照质感、35mm颗粒、柔光镜、戏中戏名场面复刻。适合 CP 叙事、章回体连载。
- **风格D 时尚杂志企划感**：刊名/页码/栏线排版、影棚大片或外拍 editorial、经典海报版式致敬、摩登混搭。适合封面、整期企划。

**风格线可混合**（爆款常见）。完整参数表、13个爆款案例拆解、识图反推法见 `references/07-双风格体系与识图反推法.md`（必读）。

### 铁律

0. **【最高优先级 · API 调用红线】本 skill 只有「生图」可以自动调 RunningHub，其余一律先问用户。**
   - ✅ 可自动调用：`rhart-image-g-2/text-to-image`、`rhart-image-g-2/image-to-image`
   - ❌ **禁止自动调用**：识图/理解端点、视频、音频、3D及一切其它外部 API，必须经用户明确同意。识图/反推/筛脸/复核一律用本机自带模型直接读图。
   - 2026-09-19 违规记录：误调173次识图端点（约¥1.73），反面教材不得再犯。
1. **只出提示词，不直接生图。** 提示词整段输出、可复制、不拆散。
1.5 **要「像」就必须图生图。** 文生图只能保证妆造对，保证不了脸像原版演员。用户强调相似度时，默认图生图+原版剧照参考脸。
2. **角色锚点必须来自原版剧集。** 先从 `references/02-名著角色锚点库.md` 取造型特征。**戏装100%保留原版**——悟空金冠铠甲、黛玉蓝白襦裙一件都不能换；风格化只落在「场景年代反差、怀旧胶片色调、海报杂志排版、荒诞记忆道具」四点。详见 `references/06-真实案例纠偏.md`。
3. **不自造示意图。** 参考图一律引用真实存在的原版剧照（`references/03-原版剧照素材索引.md`）。
3.5 **参考脸只认经典版本**：94三国/86西游/87红楼/98水浒。取图流程见 `references/08-参考脸素材获取方法.md`。下载后务必本机模型逐张读图确认身份再用于图生图。
4. 画幅默认竖版 2:3 或 3:4（小红书调性），用户点名 9:16 或 1:1 按用户的来。

### 工作流程

1. **确认角色与流派**：角色（林黛玉/孙悟空/貂蝉……）+ 流派（少女款元气软嫩 / 偶像款温柔干练 / 胶片款复古疏离，见 `references/01-日杂风核心法则.md`）。
2. **取角色锚点**：读 `references/02-名著角色锚点库.md` 摘脸型五官、标志性妆造、神态名场面。没收录的角色先让用户描述或提供剧照，提炼后补录。
3. **套七段公式**（顺序即权重）：

```
[1 摄影质感底座] 怀旧剧照/复古胶片质感、暖调逆光、浅景深、细腻颗粒；保留戏装本色
[2 角色锚点] 原版角色的脸型/五官/发型/神韵（写具体）
[3 戏装保留] 原版神装整件保留写具体 + 一件荒诞记忆道具做反差记忆点
[4 场景] 生活化场景，背景干净有留白
[5 光线时刻] 清晨侧光或傍晚逆光发丝光，避开正午顶光
[6 姿势情绪] 自然抓拍感、不直视镜头或浅笑望远方
[7 画幅与负面] 竖版 2:3；避免浓妆、影楼感、高饱和红金撞色、僵硬正面照
```

3.5 **CP/双人场景**加三行：CP反差锚定（两人气质体态拉开反差）+ CP意象对位（补天石×绛珠仙草式）+ 互动关系（一高一低有空间高低的动作）。完整案例见 `references/04-圣黛CP与名著日杂案例库.md`。
4. **输出规范**：中英双版本各一段（英文给GPT Image 2/MJ，中文给即梦类）；整段连续文本不换行不JSON；每段后附「改造说明」。锁脸图生图写法见 `references/07` 第六点八节；参考图路径 `02_assets/人物脸参考/` 与 `02_assets/{西游记,红楼梦,三国演义}/`。
5. **出图前过清洁渲染层**：按 `references/09-GPT-Image-2清洁渲染层.md` —— 风险词替换→信息密度三区自检→材质骨架句→负面块卫生压缩→60/30/10调色板核对。专治GPT Image 2脏纹理、塑料感。
6. **批量任务先立变量主权**：出N张同设定图（系列肖像/海报/封面）时，第一步按 `references/10-批量生图变量主权与验收.md` 出 I/C/E 表（不变量/条件变量/探索变量分桶）+ MUST/MAY/EXPLORE 契约，验收按「先过不变量门再评惊喜」顺序，一轮只放开1-2个E变量。

### 避坑清单（负面提示词依据）

浓妆+假睫毛+高饱和唇色→影楼风；角色戏装换现代穿搭→完全跑偏（已废弃）；大红大金撞色→破坏低饱和；正面僵硬直视镜头；过度磨皮→丢失皮肤质感。

> 宋韵/古风方向已迁出至独立skill `song-yun`（含宋式田园+宋韵身份矩阵），用户要宋韵时路由过去。

## 参考（B线）

- `references/01-日杂风核心法则.md` — 光线/构图/色调/妆造/姿势完整技法
- `references/02-名著角色锚点库.md` — 三部原版剧角色造型特征与流派适配
- `references/03-原版剧照素材索引.md` — 已下载剧照的本地路径与来源链接
- `references/04-圣黛CP与名著日杂案例库.md` — CP反差萌手法、名场面模板、逐角色速查、杂志内页排版
- `references/05-小红书真实案例采集.md` — 登录态抓真案例的完整命令流（进阶可选）
- `references/06-真实案例纠偏.md` — 【必读】三条爆款案例正确范式
- `references/07-双风格体系与识图反推法.md` — 【必读】四风格体系、13案例拆解、识图反推、锁脸写法
- `references/08-参考脸素材获取方法.md` — 豆瓣取图通道、subject ID表、选脸四条标准
- `references/09-GPT-Image-2清洁渲染层.md` — 【出图前必过】风险词替换、三区自检、负面卫生学
- `references/10-批量生图变量主权与验收.md` — 【批量任务必读】I/C/E变量主权表、MUST/MAY/EXPLORE契约、验收顺序铁律、失败形态路由

## 模块清单（modules/）

White Lang 合集（11）：story-director、korean-girlgroup-casting-cn、light-fresh-short-film、chinese-aesthetic-video-director、retro-dv-daily-director、phone-vlog、eastern-colossal-wonder-director、eastern-dream-director、eastern-megastructure-director、image-prompt-director、surreal-cinematic-keyframe-director

美学扩展包（8）：giant-celestial-palace-prompts、gilded-ink-fantasy-prompts、mirror-flower-water-moon-prompts、zanhua-lady-aesthetics-prompts、hong-kong-retro-wuxia-prompts、shaw-wuxia-image-prompts、iwai-youth-film-prompts、western-imperial-fantasy-prompts

各模块内部规则以其自身SKILL.md为准；公共铁律（只写提示词、不编造参考、不直接生成）全模块通用。
