# girlgroup-casting

韩系女团多人选角与面部资产出图技能。两张牌：**两层锁定法**写成员提示词（固定妆容母版 + 可变五官身份，四项差异化防撞型），**RunningHub G-2 批量出图**（2 并发 + PNG 完整性双校验 + 单成员返修迭代）。

## 实战案例：棱镜Hz

四人女团「棱镜Hz」（白光过棱镜分四束光），与抖音号同名：

| 成员 | 定位 | 气质 | 主题色 |
|---|---|---|---|
| Hz-01 | 主唱 VOCAL | 清冷优雅 | 月光银白 `#DDE0EA` |
| Hz-02 | 领舞 DANCE | 甜酷俏皮 | 琥珀金 `#F0A830` |
| Hz-03 | 门面 VISUAL | 温柔知性 | 蜜桃粉 `#F2A6A0` |
| Hz-04 | 忙内 RAP | 少年未来感 | 薰衣草紫 `#B4A0E5` |

- 完整选角提示词（4 人 × 16 区块）：`references/棱镜Hz-女团选角-面部资产提示词.md`
- 终版定妆照：`images/`（含迭代版本记录，Hz-02 经两轮返修定稿单马尾版）
- 批量出图脚本：`scripts/gen_prism_hz.py`

## 使用

把 `girlgroup-casting/` 整个拷进 `~/.workbuddy/skills/` 即可被 WorkBuddy 识别为技能。

出图需要 RunningHub API key：

```bash
export RUNNINGHUB_API_KEY=<你的key>
python scripts/gen_prism_hz.py
```

脚本默认解析 references 下的选角 md 出全员定妆照；换团时改脚本顶部的 SRC 路径与成员映射即可。

## 依赖

- Python 3.10+（仅标准库）
- RunningHub API key（环境变量传入，不落盘）
- 可选：OpenClaw_RH_Skills 的 `runninghub.py` CLI 封装（没有的话按 SKILL.md 中的直连流程自行实现）
