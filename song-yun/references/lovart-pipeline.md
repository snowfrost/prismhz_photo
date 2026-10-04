# Lovart 批量出图流水线备忘（2026-10-04 实战）

> 来源：秦观《满庭芳·红蓼花繁》40 张双套成图项目，踩坑与解法全部实测。
> 技能位置：`~/.workbuddy/skills/lovart-skill__skillhub/scripts/agent_skill.py`

## 一、命令与参数

```bash
# 全局参数必须放在子命令【前面】
python3 scripts/agent_skill.py --timeout 900 chat --prompt "..." \
  --attachments URL1 URL2 \
  --prefer-models '{"IMAGE":["generate_image_midjourney"]}' \
  --json --download --output-dir OUT
```

| 参数 | 要点 |
|---|---|
| `--timeout` | **必须写在子命令前**。写在后面会 argparse 报错 → 无 JSON → 批量脚本误判"提交失败"（症状：几秒内全部失败） |
| 默认 timeout | 仅 **180 秒**，超时返回 `final_status=timeout` 但**图还在生成** |
| `--attachments` | `nargs="*"`，空格分隔多图。**锁人物只传一张定妆图**，混两张会职责混淆 |
| `--prefer-models` | 是"偏好"非强制；MJ 工具名 `generate_image_midjourney`，版本由服务端路由 |
| `--include-tools` | 硬约束，需要强制某工具时用 |

## 二、必踩的坑与解法

| 坑 | 症状 | 解法 |
|---|---|---|
| **提示词超长** | 连报 `UPSTREAM_ERROR`、零产物 | **≤1024 字符（含参数）**。中文信息密度约英文 2–3 倍，**优先写中文** |
| **中文提示词被画成字** | 画面出现"宋佳代感""光影｜意境"等水印 | **MJ 会把提示词里的中文词当画面文字渲染**。`--no 文字` 与自然语言排除**都无效**。→ 改**英文提示词** |
| **同线程改词重跑** | 返回缓存旧图（`new:false`，URL 相同） | 换新线程（省略 `--thread-id`） |
| **`nohup &` 起后台** | shell 退出即被杀 | 用工具的 background 模式 |
| **轮询超时误判** | 报"无产物"，其实图还在生成 | 记下 `thread_id`，稍后 `result --thread-id X --json --download` 补取。**"无产物"≠失败** |
| **并发过高** | 全接口 429 `Rate limit exceeded` | **安全并发 4 分片**；单轮 ≤28 张；冷却约 2 分钟 |
| **限流被吞** | 报 `Project 'xxx' does not exist`（假象） | 限流时 `validate_project` 吞掉错误。用 `query-mode` 判连通：返回 JSON = 未限流 |
| **project 接口抽风** | 报"项目不存在" + `SSL: UNEXPECTED_EOF` | 等 2 分钟自愈，**别急着重建议新项目** |
| **代理隧道 502** | 任意命令报 `Tunnel connection failed: 502` | `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` 走直连 |
| **AK/SK 跨账户** | `Invalid signature` / 项目不存在 | **AK 与 SK 必须整套换**；项目绑在 AK 上，换 AK 等于换账户 |
| **服务端拥堵** | 单张从 9 分钟拉长到 >20 分钟，线程长期 `running` | 起**守望进程**：记 thread_id，每 100s 轮询补取，不阻塞主流程 |

## 三、锁人物（实测有效方案）

```
① 只传一张定妆图作 --attachments（不混色调图）
② 锁脸句放到提示词【最前面】，不放末尾
③ 明确写"画面内不得出现任何文字、水印、logo"（自然语言）
```

**反例 vs 正例**（同题材实测）：
- ❌ 双图附件 + 锁脸句放末尾 → 人物服装全丢（青瓷绿袍变白衣）、出网红脸、带水印
- ✅ 单图 + 锁脸句前置 → 服装与人物特征保住、无水印

**英文锁脸句模板**（约 215 字符，务必精简）：
```
Image 1 is the character reference: same face, half-up black hair with one dark-wood hairpin, same [服装描述]; she must be the same person.
```

## 四、画幅与曝光控制

- **画幅**：写 `--ar 16:9`（或 2:3）；同时正文写 `16:9 full-bleed, edge-to-edge, no black bars, no letterbox`
  —— 否则可能**在画面内烧进电影黑边**（文件尺寸仍是 16:9，但内容区被压）
- **曝光词敏感度实测**：
  - `very dark / heavy underexposed` → **压到全黑**（亮度可低至 8）
  - `late dusk / soft even light` → **反而更亮**（亮度可飙到 178）
  - **大面积天空+水面的空镜特别容易被推亮** → 用**画面内可见的月亮当光源**做锚点最稳：
    `a clearly visible moon low in the frame is the light source, so the frame reads as deep blue night with readable mid-tones, never as a black picture`
- **夜景正常亮度区间**：灰度均值 **50–85**。低于 22 判过暗，高于 150 判偏亮

## 五、成图质检四步（PIL 可全自动）

```python
# ① 尺寸/宽高比
im.size
# ② 黑边检测 —— 用行亮度突变法（不要用"上下条带亮度<26"，暗夜景会大量误报）
rows = [行均值...]; med = median(rows)
# 找相邻行亮度跳变 >10 的边界线
# ③ 曝光：ImageStat.Stat(im.convert('L')).mean[0]
# ④ 水印：把每张底部 14% 裁条拼成一张长图，一次读完定位
```

## 六、批量脚本骨架

```
提交 → 记 thread_id → 轮询 result（每 45s，最多 28 次）
     → 拿不到就记"待补取"，不要当失败
分片：RERUN_SHARD=k/m（按 index % m == k-1），每片独立 _state_<tag>.json
断点续跑：已完成的序号写入 state，重跑自动跳过
```
