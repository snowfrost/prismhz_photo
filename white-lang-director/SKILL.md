---
name: white-lang-director
description: White Lang 系列影像提示词总路由（整合 11 个导演型子技能）。根据用户意图自动分发：剧情短片分镜与视频节点（story-director）、韩系女团选角与舞蹈MV（korean-girlgroup-casting-cn）、光感小清新短片（light-fresh-short-film）、中式园林影像美学（chinese-aesthetic-video-director）、复古DV日常（retro-dv-daily-director）、真实手机自拍Vlog（phone-vlog）、东方巨物奇境（eastern-colossal-wonder-director）、东方梦境胶片（eastern-dream-director）、东方天宫巨构（eastern-megastructure-director）、单幅画面视觉（image-prompt-director）、超现实电影画面（surreal-cinematic-keyframe-director）。覆盖 AI 视频提示词（Seedance 2.5/可灵/即梦）、图片提示词（Midjourney V8.2/Image 2/Seedream 5 Pro）、人物资产与三视图、成图转图生视频、生成失败诊断修复。触发词：视频提示词、分镜、女团、选角、小清新、园林、DV、Vlog、巨物、天宫、仙侠、古风、超现实、单幅画面、风格迁移、图生视频、修提示词、提示词不对。
metadata:
  source: 飞书文档《White Lang技能分享》(docx/WFI8dki2so5aHhxUXMmc6j8Ynlf)
  integrated: "20261006"
  audit: P2 安全（20261006，60 文件零脚本零网络请求）
---

# White Lang Director｜影像提示词总路由

## 1. 这是什么

一个路由 + 11 个导演型子模块。用户的任何影像提示词需求先在这里判断意图，再分发到对应模块**完整执行**。子模块全部来自 White Lang 技能包，各自有独立的 SKILL.md 和 references，方法论互不重复。

**铁律：本文件只做路由，不做创作。** 路由判定后必须完整读取对应模块的 SKILL.md 并严格按其执行；模块内声明的 references 相对路径继续生效，一个都不能跳读。

## 2. 路由表

按「用户意图」匹配。多行命中时，以**更具体的一行**为准（例："韩系女团舞蹈MV" 走女团模块而非 story-director）。

### 视频类（产出：视频提示词 / 分镜 / 视频节点）

| 用户意图特征 | 分发模块 | 模块路径 | 主推模型 |
|---|---|---|---|
| 完整剧情、故事因果、标准横向分镜、视频节点配置、连续性检查、剧情片 | story-director | modules/story-director | Seedance 2.5 |
| 韩系女团、面部资产、人物三视图、多人差异化、舞蹈MV、动作参考迁移 | korean-girlgroup-casting-cn | modules/korean-girlgroup-casting-cn | 图片 Seedream 5 Pro / Image 2，视频 Seedance 2.5 |
| 小清新、夏日、自然光感、清透冷调、5–30秒、轻叙事 | light-fresh-short-film | modules/light-fresh-short-film | Seedance 2.5 |
| 中式园林、东方意境、含蓄表演、软光大光圈、镜头续写 | chinese-aesthetic-video-director | modules/chinese-aesthetic-video-director | Seedance 2.5 |
| 复古DV、日常记录、生活碎片、季节穿搭、手持呼吸感 | retro-dv-daily-director | modules/retro-dv-daily-director | Seedance 2.5 |
| 手机自拍、Vlog、竖版、生活记录、30秒以内、设备不穿帮 | phone-vlog | modules/phone-vlog | Seedance 2.5 |

### 图片类（产出：图片提示词，多数支持成图后转约5秒图生视频）

| 用户意图特征 | 分发模块 | 模块路径 | 主推模型 |
|---|---|---|---|
| 巨型花卉植物、东方奇境、尺度感、巨物与人物共景 | eastern-colossal-wonder-director | modules/eastern-colossal-wonder-director | Midjourney V8.2 |
| 仙侠、志怪、古风梦境、东方胶片质感 | eastern-dream-director | modules/eastern-dream-director | Midjourney V8.2 |
| 白玉京、云上天宫、东方巨构建筑、建筑丰富度与尺度 | eastern-megastructure-director | modules/eastern-megastructure-director | Midjourney V8.2 |
| 单幅电影画面、风格迁移、参考图分析、摄影系统设计 | image-prompt-director | modules/image-prompt-director | ChatGPT / 平台中立 |
| 超现实、视觉隐喻、巨大生物、电影叙事感底图 | surreal-cinematic-keyframe-director | modules/surreal-cinematic-keyframe-director | Midjourney V8.2 |

### 特殊入口

| 场景 | 处理 |
|---|---|
| 生成结果不对、要修提示词、诊断失败原因 | 分发到**产出该提示词的原模块**，走其诊断/修复章节（多数模块有 failure-repair / diagnostics / 实测案例与失败修正） |
| 用户上传成图，要图生视频提示词（约5秒单镜头） | 东方巨物 / 东方梦境 / 东方巨构 / 超现实 四个模块均支持二阶段；按成图风格回原模块 |
| 人物资产、三视图、定妆 | 韩系女团（韩系审美）或 story-director（剧情角色五段式），按风格定 |
| 一次需求跨多模块（如"女团MV的分镜+小清新外景"） | 主任务定模块，次风格作为该模块内的风格输入，不并联两套输出结构 |
| 用户只说"随便来""随机生成" | 图片类模块多数有随机池/灵感库机制，直接进对应模块执行 |

## 3. 路由判定规则

1. 先判**产出类型**：视频提示词 / 图片提示词 / 人物资产。
2. 再判**风格语境**：东方古典（园林/巨物/天宫/仙侠）→ 图片类四模块细分；现代生活（小清新/DV/Vlog）→ 视频类细分；剧情叙事强 → story-director；韩系偶像工业 → 女团模块。
3. 后判**交付形态**：要分镜确认流程 → story-director / retro-dv-daily-director（有前置问答）；要直接出提示词不打扰 → light-fresh-short-film / phone-vlog（明确禁止前期询问）。
4. 拿不准时按用户提到的**具体名词**匹配模块触发词；仍然模糊就问一句，不猜。

## 4. 全模块共同铁律（11 个 skill 的公共基因，冲突时以子模块为准）

1. **唯一选择**：人物、道具、动作、场景、光线全部直接做出一种明确选择，禁止"某个、一种、或者、类似、可能出现"。
2. **每镜一个主要动作 + 一种主要运镜**：动作拆镜，不塞满。
3. **正向描述优先**：正文写清唯一正确结果，不靠负面提示词挽救含糊正文；负面约束只保留会毁掉当前结果的高风险项。
4. **时间线硬算术**：所有时间段相加必须等于总时长，连续时间码，不机械平均分配。
5. **光线连续性**：光源方向、曝光、肤色、背景明暗同场次连续；光线变化必须有物理原因。
6. **表演可见化**：抽象情绪转成当前机位看得见的动作（视线、手指、重心、停顿）；遮挡或背影不描写不可见面部。
7. **中英一致**：双语言输出时人物数量、动作、道具、场景、情绪必须完全一致。
8. **不擅自加料**：不主动加对白、BGM、空镜、字幕、水印、转圈摆拍；用户锁定项原样保留，已否决项不复活。
9. **只交付提示词**：默认不调用生成工具、不虚构"已生成"；用户明确要求生成时再动手。
10. **局部修改最小化**：只改受影响镜头，不重写全文，不复活已否决内容。

## 5. 组合流参考

**图 → 视频二阶段**（东方巨物 / 梦境 / 巨构 / 超现实）：
提示词出图 → 用户回传最终成图 → 严格以实际画面为依据 → 约5秒、单镜头、不切镜、一种运镜 → 环境动态 > 人物微动作 > 生物微动。

**资产 → MV**（女团）：
面部资产提示词（确认门）→ 三视图 → 30秒逐镜时间线 MV 提示词；可挂动作参考迁移。

**一句话 → 成片**（story-director）：
七项信息确认（剧情来源/时长镜头数/画幅/资产范围/风格/声音）→ 人物风格选择 → 16:9 三视图 → 视觉规范 → 横向分镜表确认 → 五板块 final_video_prompt → 视频节点。

## 6. 本地链路适配备注（王老师环境）

- 子模块写的"2.5模型/Seedance 2.5" → 即梦 seedance2.5 vip CLI。
- "可灵 / 快乐马" → 备选视频链路。
- Midjourney 提示词 → 也可投喂 Soullens gpt-image-2 或 RunningHub gpt-image-2 econ 测试英文提示词效果。
- 卡审敏感场景（真人脸多参）优先走提示词交付，让王老师自行测试；严格禁止直接批量生成角色图片。

## 7. 来源与审计

- 来源：飞书文档《White Lang技能分享》，11 个 zip 均已下载解压并原样保留在 modules/。
- 原始 zip 备份：F:/workbuddy/2026-10-06-18-24-10/02_assets/white-lang/zips/
- 安全审计：2026-10-06，P2 安全（纯 Markdown 文档，无脚本、无网络请求、无敏感路径）。
