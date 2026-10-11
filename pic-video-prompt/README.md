# pic-video-prompt 图像×视频提示词总导演

> 前身 `rizafeng-mingzhu-portrait`（四风格×名著人像提示词生成器），2026-10 大重组升级：并入 White Lang 技能合集 11 个模块与 8 个风格美学安装包，改名并扩展为图像+视频双线总路由 skill。宋韵/古风方向整体迁出至独立 skill `song-yun`。

## 这是什么

一条入口路由所有「写提示词」需求：

- **图像线**：四风格名著人像（日杂/怀旧日常/电影剧照/杂志企划 × 86西游/87红楼/94三国/金庸TVB）+ 东方巨构/巨物/仙侠志怪 + 鎏金水墨 + 镜花水月 + 簪花女郎 + 港风武侠/邵氏武侠 + 岩井俊二青春 + 西幻帝国皇室 + 超现实电影关键帧 + 通用画面设计
- **视频线**：强剧情分镜导演、韩系女团资产与MV、光感小清新短片、中式美学短片、复古DV日常、手机Vlog

## 结构

```
pic-video-prompt/
├── SKILL.md              # 总路由：媒介→风格域→模块/references
├── references/           # 名著人像体系（01-09，本skill原创核心）
│   ├── 01-日杂风核心法则
│   ├── 02-名著角色锚点库
│   ├── 03-原版剧照素材索引
│   ├── 04-圣黛CP与名著日杂案例库
│   ├── 05-小红书真实案例采集
│   ├── 06-真实案例纠偏
│   ├── 07-双风格体系与识图反推法
│   ├── 08-参考脸素材获取方法
│   └── 09-GPT-Image-2清洁渲染层
└── modules/              # 19个子模块（各有独立SKILL.md）
    ├── White Lang 合集（11）：
    │   story-director / korean-girlgroup-casting-cn / light-fresh-short-film
    │   chinese-aesthetic-video-director / retro-dv-daily-director / phone-vlog
    │   eastern-colossal-wonder-director / eastern-dream-director
    │   eastern-megastructure-director / image-prompt-director
    │   surreal-cinematic-keyframe-director
    └── 美学扩展包（8）：
        giant-celestial-palace-prompts（天宫巨物）/ gilded-ink-fantasy-prompts（鎏金水墨）
        mirror-flower-water-moon-prompts（镜花水月）/ zanhua-lady-aesthetics-prompts（簪花女郎）
        hong-kong-retro-wuxia-prompts（港风武侠）/ shaw-wuxia-image-prompts（邵氏武侠）
        iwai-youth-film-prompts（岩井俊二青春）/ western-imperial-fantasy-prompts（西幻皇室）
```

## 核心纪律（全模块通用）

1. 只写提示词，不直接生成（用户明确要求出图时走 RunningHub GPT Image 2）
2. API 红线：除生图端点外，任何外部 API 调用必须先经用户同意；识图一律本机模型读图
3. 名著角色戏装 100% 保留原版，风格化只落在场景/色调/排版/道具
4. 不自造示意图，参考图只引用真实剧照
5. 出图前必过 GPT Image 2 清洁渲染层（references/09）

## 更新日志

- 2026-10-11 大重组：rizafeng-mingzhu-portrait 改名 pic-video-prompt；并入 White Lang 11 模块（来源：飞书《White Lang技能分享》，已随 white-lang-director 收录于本仓库）与 C:\提示词 8 个美学安装包；宋韵部分（原 references/10-宋韵古风身份矩阵）迁出至 song-yun。
- 2026-09-27 新增 references/09 GPT Image 2 清洁渲染层（吸收自 MOKE SkillHub 研究）。
- 2026-09-19 新增 references/08 参考脸素材获取方法。
- 2026-09-18 四风格体系定版（日杂/怀旧/剧照/杂志企划）。
