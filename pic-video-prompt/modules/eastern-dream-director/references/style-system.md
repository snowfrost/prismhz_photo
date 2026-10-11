# 风格、光线与构图系统

本文件用于图片提示词阶段。将场景内容与风格母版分成两个自然段，中间空一行。

## 固定成像母版

### 中文

```text
35mm电影胶片，潮湿的青绿色薄雾，低反差柔焦，合焦人物与环境边缘依然柔软，高光轻微晕染扩散，黑位轻抬，柔和青色调与克制的暖色层次，柔和浅景深，细腻胶片颗粒，照片级写实，空灵神秘的东方幻想氛围。
```

### MJ 英文

```text
35mm cinematic film, humid cyan-green haze, low-contrast soft focus, gently softened in-focus subjects and environmental edges, subtle highlight bloom and halation, slightly lifted blacks, soft cyan tones with restrained warm accents, soft shallow depth of field, fine film grain, photorealistic, ethereal and mysterious Eastern fantasy atmosphere
```

“潮湿”指空气、水汽与柔和反光，不自动代表下雨、湿发、湿衣或积水。

## 时段光线

每条只选一个模块，并与场景时间保持一致。

- 清晨或白天  
  中文：`柔和自然光侧逆光，清透青色与温和日光色调，空气中少量散射光粒子。`  
  MJ：`soft natural rim backlighting, clear cyan tones with gentle daylight warmth, sparse scattered light particles in the air`

- 黄昏  
  中文：`柔和暮光侧逆光，青绿色暗部与低饱和暖金天光，空气中少量散射光粒子。`  
  MJ：`soft twilight rim backlighting, cyan-green shadows with muted warm golden sky light, sparse scattered light particles in the air`

- 夜晚  
  中文：`柔和月光侧逆光，柔和青色与清冷月光色调，克制的灯笼或烛火暖光，空气中少量散射光粒子。`  
  MJ：`soft moonlight rim backlighting, soft cyan and cool moonlight tones, restrained lantern or candle warmth, sparse scattered light particles in the air`

夜景不默认加入萤火虫。用户明确要求萤火虫时才加入。

## 天气与空间

- 未指定天气时默认无雨。
- 潮湿空气与薄雾优先来自湖面水汽、山林晨雾、植物露珠、瀑布水雾或香炉烟气。
- 只有用户明确要求雨景时才写雨丝、湿发、湿衣和积水。
- 不主动使用破败、废弃、荒凉、残损、腐朽、坍塌、褪色、杂乱或无人遗弃感。
- 古建筑保持结构完整、整洁、有人维护并具有生活气息。

## 材质控制

- 服装优先使用柔软薄纱、棉麻、暗纹织物、低光泽丝织物与自然垂坠宽袖。
- 半透明衣料呈现柔软透光，不写高光泽金属感丝绸。
- 金色发饰与首饰只作克制点缀，不让整张画面被金色补光覆盖。
- 暖色主要落在肤色、灯火、嘴唇与局部饰品；暗部保持青绿色层次。
- 不堆叠 8K、超级细节、Arri Alexa、超现实主义、欢乐夜景、网络武术、电影感与幻想美学等重复词。

## 构图选择

每幅画面只选择一个主要构图逻辑，并明确人物位置、朝向、镜头位置、前景、中景、背景和视觉重心。

- 框中框：木窗、门洞、帘幕、亭柱。
- 前景遮挡：竹叶、芦苇、纱帘、人物肩影。
- 对角线：长剑、桥栏、道路、衣袖。
- 中央对称：亭中对弈、戏台、宫门。
- 三角构图：多人互动、人物与动物。
- 三分构图：人物位于一侧，在视线或行动方向保留空间。
- 大面积留白：雾林、水面、庭院、山体。

不要只写“电影构图”。提示词必须说明构图如何形成。

### 竖图转 16:9

不得横向拉伸原图。根据人物朝向重新组织画面：

- 人物朝右时，优先放在左侧三分之一，右侧保留视线或行动空间。
- 人物朝左时，优先放在右侧三分之一，左侧保留视线或行动空间。
- 原图依赖门窗时，用横向扩展后的门框、窗格与环境继续形成框中框。
- 原图依赖近景武器时，保持剑身、扇面或伞沿构成的主要线条，不因扩图缩小人物。

## 批量去重

随机生成一批画面时：

- 默认覆盖至少两个时段：一组清晨或白天、一组黄昏，最多一组夜景。
- 不连续默认双人，不连续使用单人站立，不连续穿白衣。
- 轮换单人与环境事件、多人关系、人物与动物、骑行、追逐、对弈、表演、练剑和安静人物近景。
- 每张画面必须有一个明确视觉事件，但不限制为一个人物、一个动作或一个道具。
- 多个动作与道具必须属于同一事件，并保持清晰主次与可生成性。

## MJ 参数

默认尾缀：

```text
--chaos 25 --ar 16:9 --raw --stylize 400
```

- 参数只出现在【MJ提示词】末尾。
- 中文提示词不携带 MJ 参数。
- 用户指定画幅时只替换 `--ar`。
- 默认不添加 `--sref` 与 `--sv`。
- 只有用户提供新的 SREF 并明确要求使用时才添加；SV 只随有效 SREF 使用。

