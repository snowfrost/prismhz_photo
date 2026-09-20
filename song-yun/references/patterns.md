# 成功模式胶囊（patterns）

> 只收录经用户确认满意的成功模式。格式：模式名 / pattern（怎么做）/ when（何时适用）/ why（为何有效）/ 示例。每日学习迭代时更新。

## P1｜MJ 提示词密度基准（2026-08-31，来源：王老师纠偏）
- **when**: 任何 MJ 图片提示词输出
- **what**: 每幅 ≥90 词（对齐原帖例1-5），五件套不缺：
  ①分层服装详写（beizi 直领对襟+gauze texture → ivory cross-collar inner blouse → waist-tied long skirt + naturally falling silk folds）+ 发型锚定（low Song-style bun + one plain silver hairpin + loose strands framing her face）
  ②动作微细节（mid-step、sleeves just gently touching、drifting strands）
  ③主光+补光逻辑（主光方向 + "soft reflected glow from below fills the shadows" 类补光句）
  ④皮肤/材质（natural luminous skin texture, realistic silk/linen/cotton-linen fabric）
  ⑤色板支撑关系（主色板 + cool indigo shadows support the warmer skin tones 类支撑句）
- **why**: 短提示词丢掉光线逻辑与材质后，AI 会自行补全 → 出"AI塑料感"；密度是宋韵质感的载体
- **cross-scene**: 系列图人物描述必须逐字一致（锚定句复用），只变景别/构图/光位
- confidence: 0.9（用户直接纠偏确认）

## P2｜多景别组输出（2026-08-31）
- **pattern**：同一句输入默认给 3 个变体——半身近景｜环境远景｜侧脸特写，三变体人物服装描述完全一致，只变景别、构图重心与虚化程度，各配一句中文构图说明。
- **when**：单句诗、单个画面思路的图片需求（L2 量级）。
- **why**：一次交付覆盖"神态/空间/线条"三种审美取向，省去来回改景别的迭代成本。
- 范例见 examples.md 第六节。

## P3｜单动作 + 器物克制（2026-08-31）
- **pattern**：一张图只保留一个主要动作；器物服务动作、够用即停（一把剪、一只篮、一盏茶）。
- **when**：所有田园/生活场景画面。
- **why**：复合动作打乱肢体关系导致四手六指，器物堆砌破坏宋韵疏密留白。
- 范例见 examples.md 田园 15 卡速查表。
