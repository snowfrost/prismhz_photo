---
name: western-imperial-fantasy-prompts
description: Convert a simple scene idea into a coherent Western imperial high-fantasy visual style built from Gothic royal architecture, courtly power narratives, platinum-and-antique-gold materials, cinematic scale, and sacred dark tension. Produce a Chinese ImageGen prompt and a pasteable English Midjourney prompt ending in --v 8.2. Use for 西幻帝国、皇室宫廷、哥特王朝、王座、帝国城堡、假面舞会、皇家骑士、宫廷法师和皇室神兽. Do not use for generic fantasy adventures, Chinese celestial palaces, prompt-card rendering, or direct image generation.
---

# 西幻帝国皇室提示词

把用户的一句话场景编译为稳定、可变化的“西幻帝国皇室”视觉系统。只生成提示词，不调用图像生成工具。始终保留用户明确给出的主体、数量、身份、动作、关系、地点、时间、情绪和画幅。

## 工作流

1. 提取不可改动事实。用户只给一句话时直接工作；只有缺失信息会实质改变主体或事件时才追问。
2. 读取 [references/visual-grammar.md](references/visual-grammar.md)，选择一个主风格分支。除非用户明确要求混合，否则不叠加第二分支。
3. 人物或服装重要时读取 [references/character-costume-compiler.md](references/character-costume-compiler.md)。不得把任何示例人物变成默认角色。
4. 涉及登基、议政、阅兵、宣战、出征、舞会、歌剧、祭礼或神兽契约时读取 [references/scene-library.md](references/scene-library.md)，保护动作与空间关系。
5. 始终读取 [references/material-light-system.md](references/material-light-system.md)，建立古金、铂金、深黑负空间与单一主光系统。
6. 读取 [references/model-recipes.md](references/model-recipes.md)，分别编译 ImageGen 与 Midjourney 版本，不机械翻译同一段文字。
7. 读取 [references/failure-constraints.md](references/failure-constraints.md)，只加入与当前场景最相关的负面约束。
8. 输出前检查内容保真、分支纯度、空间逻辑、材质分工、运动物理、镜头一致性与模型格式。

## 默认决策

- 范围：只服务西欧哥特帝国、皇室宫廷与王朝权力叙事，不扩展成通用 D&D 或普通中世纪冒险。
- 主体：不固定女皇、国王或任何姓名。用户没有指定人物时，不擅自添加人物。
- 画幅：环境、仪式和动作场景默认 `16:9`；明确的单人肖像或立像默认 `3:4`；用户指定时严格服从。
- 构图：一个权力事件、一个视觉焦点、一个主镜头；前景框景、中景权力主体、远景帝国空间。
- 材质：冷铂金负责结构、边缘和权威；暖古金负责仪式、魔法或局部奢华；黑曜石、黑天鹅绒或镜水提供负空间。
- 光线：一个可解释的暖色主光，辅以克制的冷铂金轮廓光；不使用全屏黄色滤镜。
- 运动：头发、披风、旗帜、雨雪、金箔、液体或烟尘必须响应人物动作与风向。
- 人物表达：优先姿态、目光、手势和空间关系，不用身体夸张或裸露替代皇室权威。
- 文本：画面内默认无文字、标志、水印、字幕和界面元素。

## 输出格式

按以下顺序输出，不自动追加多套变体：

### 画面设计

不超过 4 行中文，说明主风格分支、权力事件、构图、主材质和光线。

### ImageGen 中文提示词

一段可直接使用的中文自然语言提示词。不得包含 Midjourney 参数。

### Midjourney 8.2 Prompt

一段可直接粘贴的英文提示词，参数放在正文后，并严格以 `--v 8.2` 结束。

### 负面约束

一行简洁中文，只列当前场景最可能出现的形态、空间、材质和风格漂移。

### 可调选项

最多 3 项，例如切换时段、画幅或主分支；用户只要求提示词时可以省略。

## 硬边界

- 不调用 ImageGen、图像生成或图像编辑工具；用户要求直接生图时，先说明本 Skill 只负责提示词，再由其他能力处理。
- 不制作提示词卡片、封面、排版或 ZIP；这些是下游卡片工作流。
- 不固定奥蕾莉亚或任何示例角色，不自动写入特定姓名、年龄、发色、身材、深 V、高开衩或裸露设计。
- 不把“西幻”泛化为精灵、矮人、冒险小队、酒馆任务或随机怪物，除非它们明确处于帝国皇室权力关系中。
- 不混入中式宫殿、汉服、和服、凤冠、仙侠、东方龙或现代都市，除非用户明确要求跨文化混合。
- 一张图只使用一个主要权力事件、一个主魔法材质机制和一个主镜头。
- 不自动添加相机品牌、艺术家、电影名、URL、`--sref`、`--oref`、`--seed`、个性化代码、`--profile` 或 `--hd`。
- 不用 `masterpiece`、`best quality`、`8K`、`hyperrealistic` 等空泛质量词替代构图与材质描述。
- Midjourney 主提示词必须完全以 `--v 8.2` 结束，后面不得有字符。

## 质量门槛

- 去掉角色姓名后，画面是否仍能识别为西幻帝国皇室，而不是普通奇幻人物。
- 用户给出的主体、数量、动作和关键关系是否完整保留。
- 是否有明确的哥特帝国空间、权力事件或皇室秩序，而不是装饰堆砌。
- 铂金与古金是否承担不同作用，暗部是否保留层次。
- 是否只有一个主光源、一个视觉焦点和一套一致透视。
- 服装、冠饰、铠甲和建筑是否符合西欧幻想语汇，没有东方冠服漂移。
- ImageGen 与 Midjourney 是否各自原生编写，Midjourney 是否严格以 `--v 8.2` 结束。

保存示例输出后可运行：

```powershell
python scripts/validate_outputs.py <output.md>
```
