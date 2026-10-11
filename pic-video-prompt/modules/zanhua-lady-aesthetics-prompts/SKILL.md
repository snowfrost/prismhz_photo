---
name: zanhua-lady-aesthetics-prompts
description: Compile a short Chinese or English portrait idea or supplied reference into the established Zanhua Lady pearlescent court-dress aesthetic, with a Moodboard-assisted Midjourney V8.2 prompt and an explicitly labeled ImageGen textual reconstruction. Use for 簪花女郎、珠光华服、牡丹花冠、金线织锦、透明披帛、古风女性横版肖像、同风格组图与生成跑偏修复. Do not use for ordinary historical reconstruction, prompt-card layout, video prompts, or image generation unless the user explicitly asks to generate.
---

# 簪花女郎·珠光华服美学提示词

把用户的一句话画面编译成“簪花女郎”系列，而不是把固定人物、固定花冠和固定袖子复制到所有场景。默认生产路线是 **用户的 Midjourney 情绪版 + 结构化提示词**；九张现有成果只证明这一组合有效，不证明文字提示词单独可复现同样效果。

## 先选择执行模式

根据已有信息自动选择，不要求用户重复回答已经说明过的内容：

1. **情绪版协同模式（默认）**：用户说已在 Midjourney 开启该情绪版，但没有提供代码。生成完整提示词，不添加 `--p`，并在“情绪版状态”中提示保持该情绪版启用。
2. **固定版本模式**：用户明确提供成功任务中的具体 `--p code`。原样写入参数区，作为可复现性最高的路线；不得修改或猜测代码。
3. **最新版模式**：用户明确提供 Moodboard ID。原样使用 `--p mID`；说明它会随情绪版内容变化，不能冒充固定版本。
4. **无情绪版降级模式**：用户明确没有情绪版，或要求纯文字版本。补足更多人物、材质、光影与成像描述，并标记为“文本近似重建，未获得等效视觉验证”。
5. **具体构图复刻模式**：用户提供某张原图并要求构图接近时，将该图分配为 Image Prompt 的构图/内容参考；情绪版仍只负责宽泛审美。先排除截图状态栏、进度条、播放器控件、文字和水印。

情绪版、代码、Image Prompt URL、seed 或其他账号参数均不得臆造。需要锁定版本而用户没有代码时，告诉用户从一张成功任务的完整参数中复制 `--p code`；不要用占位符污染可粘贴提示词。

## 工作流

1. 提取不可改动事实：人物数量、姿态、视角、目光、动作/道具、环境、主体位置、画幅和用户指定的颜色。
2. 读取 [references/visual-grammar.md](references/visual-grammar.md)，冻结本风格的视觉 DNA，并挑选与当前画面匹配的构图母题。涉及明确构图时再读 [references/composition-presets.md](references/composition-presets.md)。
3. 读取 [references/lighting-material-grade.md](references/lighting-material-grade.md)，分别写出光线地图、材料分层和颜色角色；不得只写 `cinematic lighting`、`luxury` 或颜色清单。
4. 涉及情绪版代码、强度、Image Prompt 或模式切换时，读取 [references/moodboard-workflow.md](references/moodboard-workflow.md)。
5. 读取 [references/model-recipes.md](references/model-recipes.md)，分别编译 Midjourney 与 ImageGen；ImageGen 版本不是英文提示词的直译。
6. 用户给出失败图或说“跑偏”时，读取 [references/drift-repair-matrix.md](references/drift-repair-matrix.md)，只修复最小责任项，不重写已经通过的构图。
7. 只有在用户询问来源、验证范围或案例映射时才读取 [references/evidence-map.json](references/evidence-map.json)。

## 风格职责边界

- **情绪版负责**：人物审美分布、华服繁复度、珠光倾向、簪花密度、柔焦与综合色彩趣味。
- **文字负责**：镜头、人物位置、姿态、目光、手和道具关系、袖/披帛运动路径、光源方向、材料分离、背景层次、局部高光以及防漂移条件。
- **Image Prompt 负责**：需要严格继承时的内容、构图和颜色关系。它不是情绪版的替代品。
- **ImageGen 负责**：用明确中文自然语言重建可见机制；它无法调用 Midjourney 情绪版，因此默认属于未视觉验证的近似路线。

## 默认决策

用户没有指定时：

- 一位原创、非特定真人的古风女子；安静、克制、有明确目光状态，珊瑚色嘴唇自然闭合。
- 横向 `16:9`；人物靠近一侧三分区，另一侧用衣袖、花枝、云层、建筑或柔焦花团展开横向纵深，而不是把竖图机械裁宽。
- 黑发形成结构清楚的宫廷发髻，发饰必须写明固定位置与垂挂关系；不默认复制某一张样本的完整花冠。
- 珠光象牙、雾蓝、水青为主，淡粉、珊瑚、玉绿和香槟金作为分区明确的辅色。
- 上方一侧的暖白方向光，中等柔度；中性或冷色补光保留下颌和衣褶阴影。
- 珠光晕只落在金线、珠宝、水晶和欧根纱边缘，皮肤不做全局过曝柔光。
- Midjourney 基准参数：`--ar 16:9 --s 100 --c 0 --v 8.2`。用户指定画幅时替换 `--ar`，不要无理由提高 `--s` 或 `--c`。

## Midjourney 硬规则

- 正文使用英文，先写镜头和空间关系，再写人物、材料、光色和成像。
- 情绪版协同版以 170–210 个英文词为目标；道具关系复杂时也不得超过 230 词。优先删去次要环境名词，不删构图、手部关系、材料分层和光线地图。
- 每条主提示词严格以 `--v 8.2` 结束，后面不得再有字符。
- 默认不使用 `--raw`；这套风格依赖情绪版与具体材质语言共同激活。
- 只有用户明确提供代码时才写 `--p code` 或 `--p mID`。
- 情绪版模式下不添加 `--sw` 或 `--sv`。不要把 Style Reference 权重当作情绪版强度。
- 可以保留少量可见的风格激活描述；不能因为启用情绪版就删掉构图、光线和材料条款。
- 不添加 `8K`、`masterpiece`、`best quality`、相机型号、镜头型号、胶片、艺术家、seed 或通用缺陷词表。

## 输出格式

用户只要提示词时依次输出：

1. `画面设计`：2–4 行中文，说明构图、主关系、光线和主材质。
2. `情绪版状态`：协同/固定版本/最新版/无情绪版，以及代码是否由用户提供。
3. `Midjourney 8.2 Prompt`：一条可直接粘贴的英文提示词。
4. `Midjourney 使用方式`：仅在需要提醒用户启用情绪版、附加 Image Prompt 或说明版本可变性时出现。
5. `ImageGen 中文重建提示词`：一段中文自然语言；明确写“近似重建”，除非确有生成验证。
6. `验证边界`：用一句话说明是情绪版协同验证、纯文本未验证还是新构图未验证。
7. `可调选项`：最多 3 项，不自动生成大批变体。

## 内容与风格优先级

发生冲突时按以下顺序处理：

1. 用户明确的人物、数量、姿态、动作、目光与道具
2. 镜头、主体位置、负空间和袖/披帛/花枝的主要路径
3. 发冠与头发、道具与手的连接关系
4. 材料分层、光线地图和色彩角色
5. 花朵、珠宝、散景和氛围装饰

## 质量门槛

- 去除通用“美人、古风、奢华”后，提示词仍能识别出珠光织锦、透明披帛、附着式簪花、克制人物和局部珠光晕。
- 人物没有被自动推成极近脸部特写；横版保留可读的环境或衣料横向运动。
- 织锦/缎面与欧根纱保持不同的厚度、透明度和反射；刺绣不是平面印花。
- 面部保留连续渐变与下颌阴影，不是白棚磨皮或塑料蜡面。
- 背景不整体泛黄、泛绿、棕褐或纯白；服装颜色仍可辨。
- 用户提供的情绪版代码完全原样，未提供时提示词中没有伪造代码或占位符。
- Midjourney 提示词末尾严格为 `--v 8.2`。

保存结果后可执行：

```powershell
python scripts/validate_outputs.py <output.md>
```

本 Skill 只生成分析与提示词。只有用户明确要求“直接生图”时才调用图像生成工具。
