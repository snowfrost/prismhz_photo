# 09 · GPT Image 2 清洁渲染层（出图前必过的最后一道工序）

> 来源：MOKE SkillHub `im2-clean-image`（邪恶红猴子）+ `lira-image-prompts`（ke mo）方法论蒸馏 · 2026-09-27
> 定位：本 skill 输出提示词的**最后一层加工**。七段公式组装完成后、交付用户前，用本文件规则过一遍，专治 GPT Image 2 的脏纹理、塑料感、AI感。

## 核心认知

GPT Image 2 经济版的三大顽疾与病根：

1. **脏纹理**（ghost texture / 潜污 / 微图案噪声）← 病根是「细节均匀分布」+ 风险词诱导（ultra detailed 一类）
2. **塑料感**（蜡像皮肤 / 玻璃皮 / uniform gloss）← 病根是**没写材质物理行为**，只写了「真实」「高清」
3. **AI感** ← 病根是负面提示词被旧失败记忆污染，或否定词召唤了本不存在的概念

## 一、风险词替换表（写完提示词先扫这一遍）

| 病词（禁用） | 替换为 |
|---|---|
| ultra detailed / hyper detailed / 极致细节 | clear focal/support/quiet detail hierarchy（清晰的焦点-支撑-留白三层） |
| insanely detailed | realistic detail only |
| micro detail everywhere | detail concentrated only on meaningful surfaces |
| highly textured | controlled material rendering |
| wet glossy / 水润光泽 | subtle reflections with strict wet/dry boundaries |
| cinematic bokeh everywhere | organized low-frequency background with selectively softened depth layers |
| beautiful lighting / 精美打光 | motivated key light, controlled bounce, protected highlight texture（有动机的主光+受控反弹+高光有纹理） |
| realistic texture | physically distinct material response with natural texture only |
| 8K / ultra realistic / sharp details | 删除——用具体材质行为替代分辨率许愿 |

## 二、信息密度三区（构图层的隐形骨架）

把画面分三个区，**细节密度必须有层级**，均匀细节 = 结构性失败：

- **Focal zone（焦点区）**：脸和手。最高边缘对比、完整轮廓、毛孔级细节只给这里
- **Support zone（支撑区）**：服装主体。中等形状，织物纹理只到「解释材质」的程度
- **Quiet zone（留白区）**：背景。大色块，主动让细节「丢失」——远景低对比、边缘软化、局部融入光影

**缩略图自检**：把图缩到指甲盖大小——焦点区还清晰吗？至少一大块安静面积还在吗？背景边缘频率低于焦点区吗？三个都过才算合格。

## 三、材质句子骨架（塑料感的解药）

每张人像提示词里必须有一句「材质物理行为」，套这个骨架：

```
[主材质] 在 [光照条件] 下呈现 [物理行为]，[局部] 保持哑光而 [边缘] 呈现 [高光类型]
```

人像专用模块（按需取用，不堆砌）：

- **面孔**：natural facial planes, matte skin with soft specular highlights, subtle pores only where visible, clean eye highlights, no waxy gloss
- **织物/戏服**：geometry-aware weave structure, fibers following folds, grazing light revealing raised texture, no flat printed texture（戏装刺绣要写「线迹跟随褶皱」而不是「华丽刺绣」）
- **金属/兵器**：roughness variation, worn edges catching narrow highlights, oxidized flats absorbing light, no uniform chrome gloss
- **暗背景**：smooth dark tones, readable shadow floor, clean value separation, no noisy bokeh

## 四、负面提示词卫生学（AI感的解药）

**负面槽不是失败记忆**，只是当前风险约束槽。五条铁律：

1. **先正面锁**：写「no X」之前先问「我希望看到什么」，能正面写就不用负面
2. **只留大类**：artifact 类 / 多肢体类 / 文字水印类 / 材质假感类，每类一两个词
3. **不点名旧失败**：上一张图出现的具体道具/颜色/姿势，不写进负面——会污染新图
4. **不召唤不存在的名词**：画面本不会有宇航员，就别写「no astronaut」——描述它会把它召来
5. **紧凑一行**优于长列表：负面词越多，正向画面越稀

本 skill 场景的安全负面默认块（GPT Image 2 有负面槽时用）：

```
Avoid: dirty texture buildup, ghost texture, latent artifacts, repeated micro-pattern noise, muddy shadows, noisy bokeh, pasted-on texture, uniform plastic gloss, waxy skin, over-smoothed face, studio-photo feel, text, watermark
```

## 五、60/30/10 调色板（色彩层防脏）

用百分比写调色，三个色相 + 明确比例。本 skill 四风格线的默认配比：

- 日杂风：60% 米白/浅灰 + 30% 雾蓝/灰绿 + 10% 褪色暖橘
- 怀旧日常：60% 暖黄褪色 + 30% 棕褐 + 10% 泛绿阴影
- 电影剧照：60% 主色调（按原剧）+ 30% 对比冷色 + 10% 高光色
- 杂志企划：60% 留白底色 + 30% 服装主色 + 10% 点缀色

比例写法对 GPT Image 2 读取效果好（"a palette of 60% warm ivory, 30% muted blue-grey, 10% faded terracotta"）。

## 六、脏输出的处理纪律

出图已经脏了（鬼影纹理/暗水印感/低对比残留）：**不要反复图生图清理**——迭代清理会放大潜污。正确做法是回提示词层：补材质句 + 换风险词 + 压负面，**干净重写重新生成**。

图生图编辑时的外科手术纪律（改戏装/换场景时）：

```
CHANGE: 只写唯一一处改动
PRESERVE EXACTLY: 面部身份、五官、发型、姿势、构图、机位、现有阴影、色调节单列
其他 100% 不动
```

一次只改一处。用户说「改过头了」= 改多了，锁更多、改更少。

## 使用流程总结

```
① 七段公式组装完成
② 扫风险词替换表（§一）
③ 检查信息密度三区是否成立（§二）
④ 补一句材质骨架句（§三）
⑤ 负面块按卫生学压缩（§四）
⑥ 调色板核对 60/30/10（§五）
⑦ 交付（附改造说明时注明本次的材质锁与负面策略）
```
