---
name: wx-cli-win
description: Windows 上读取本人微信本地数据库的完整链路：抓密钥、全库解密、聊天记录查询、群聊内容提取、图片从缓存解密导出。适用两类版本——路线A 走 jackwener/wx-cli（微信 4.0.x～4.1.9），路线B 走自研链路「硬件断点抓 passphrase + PBKDF2 派生 + SQLCipher 全库解密」（微信 4.1.10+，实测 4.1.15.13，28/28 库解密通过）。支持列出会话、按群/联系人导出可读聊天记录、活跃度统计、链接与文件分享清单、图片索引与图片还原、群成员与备注映射。当用户要求查看微信聊天记录、搜聊天关键词、了解某个群最近聊了什么、统计聊天数据、导出聊天档案、找出群里分享过的提示词/工具/链接/文件、或提取群里的图片时，使用本 skill。注意：路线B 首次取密钥需用户配合重新扫码登录一次；图片导出支持 V2/V1/V0 三代格式全解密（含 wxgf 转码），依赖本机已缓存的图片文件。仅限处理用户本人的微信本地数据，须遵守法律法规与微信用户协议。
license: Apache-2.0
metadata:
  author: snowfrost
  version: "2.2.0"
  display_name: 微信数据查询 CLI（Windows）
---

# wx-cli-win · 微信本地数据查询（Windows）

> 数据全程留在本机，不上传任何服务器。
> **仅限读取本人微信数据**，请遵守当地法律法规与微信用户协议。

## 我该走哪条路线？

| | 路线 A：wx-cli | 路线 B：自研解密链路 |
|---|---|---|
| 适用微信版本 | 4.0.x ～ 4.1.9 | **4.1.10+（实测 4.1.15.13 通过）** |
| 原理 | 进程内存扫描 raw key | 硬件断点抓 `setCipherKey` passphrase → PBKDF2 派生 |
| 前置操作 | 管理员终端跑 `wx init` | 需用户**重新扫码登录一次**（窗口约 1 分钟） |
| 初始化次数 | 每次微信重启都要重跑 | 抓一次，passphrase 长期复用 |
| 覆盖范围 | 上游 CLI 命令集 | 全库解密后可任意 SQL 查询 + 图片还原 |

**判断口诀**：先看微信版本号（`设置 → 关于`）。≥ 4.1.10 直接走路线 B，不要在路线 A 上耗时间。

## 路线 B · 全流程

### 第 0 步 · 环境准备

```bash
pip install zstandard        # 必须。缺它时压缩字段静默返回 None，表现为"图片/文件一条都查不到"
```

Python 3.10+。`zstandard` 是硬依赖，不是可选优化——没装会误判成"群里没人发图"。

### 第 1 步 · 抓密钥（只需做一次）

告诉用户「需要重新扫码登录一次」，然后：

```bash
cd <skill>/scripts
python capture_key.py --launch
```

脚本流程：杀掉微信 → 冷启动 → 等 `Weixin.dll` 加载 → 附着调试器 + 补 PEB →
在 `setCipherKey` 布硬件断点（DR0）→ 用户扫码登录时逐个抓 passphrase →
空闲 120 秒后自动 `DebugActiveProcessStop` 分离并落盘：

```
C:\Users\<用户名>\.workbuddy\wxkey_v4\captured_keys_v4.json
```

抓到的 32 字节是 **passphrase 原始二进制**，不是最终 enc_key，
必须交给 `key_tool.py` 再派生一次（用错会 0/28 命中）。

> 详细机制与踩坑见 `references/wechat4-crypto.md` 与 `references/pitfalls.md`。

### 第 2 步 · 解密全库

```bash
python key_tool.py set-passphrase <64位hex>
python key_tool.py extract --db-dir <db_storage> --output all_keys.json
python key_tool.py decrypt --db-dir <db_storage> --keys all_keys.json --output decrypted
```

`db_storage` 默认位置（自动定位失败时手动指定）：

```
<微信文件目录>\xwechat_files\<账号目录>\db_storage
```

成功标志：`结果: 28 成功, 0 失败`（库数量随使用情况浮动）。

### 第 3 步 · 查询

```bash
set WX_DECRYPTED=<path>\decrypted             # 或用 --dec 指定
python chat.py list                           # 列出全部会话（按消息量排序）
python chat.py list --days 30                 # 只看近 30 天有活动的
python chat.py dump  "群名或备注" --days 30    # 导出可读聊天记录
python chat.py dump  "张三" --days 7 --out a.txt
python chat.py stats "AI群" --days 30          # 类型分布/日活/发言人/发图榜
python chat.py shares "AI群" --days 30         # 群里分享的链接与文件清单
python chat.py pics  "AI群" --days 30          # 图片索引
python chat.py pics  "AI群" --days 30 --export --out pics   # 真正解密导出图片
```

会话名支持群名、备注名、昵称、wxid 的部分匹配；重名用 `--pick N` 指定。

### 第 4 步 · 二次加工（交付给用户）

| 用户想要 | 做法 |
|---|---|
| 「这一个月群里聊了啥」 | `stats` 看结构 → `dump` 全量 → 提炼主线/争议/结论 |
| 「群里推荐了什么好东西」 | `shares` 拿链接+文件清单 → 分类标注 → 补标题/时间/分享人 |
| 「谁谁发了什么图」 | `pics --export` 还原图片 → 按时间/发送人归档 |

## 图片还原（V2 已完整攻克，可还原率 100%）

链路：

```
消息 XML 的 md5="..."  →  磁盘 .dat（三种质量档）  →  decrypt()  →  sniff()  →  (wxgf? 转码)  →  JPEG
```

### V2 格式与密钥（关键突破）

3.x/4.x 有三代加密，按文件头 6 字节签名区分：

| 版本 | 头签名 | 方案 | 密钥 |
|---|---|---|---|
| V0 | 无 | 整文件单字节 XOR | 首字节 ^ 0xFF |
| V1 | `07 08 56 31 08 07` | AES-128-ECB 头 + XOR 尾 | 固定 `cfcd208495d565ef` |
| **V2** | `07 08 56 32 08 07` | AES-128-ECB 头 + XOR 尾 | **账号级，离线派生** |

V2 文件结构（**不是"16 字节头"**，这是早期踩过的误判）：

```
偏移  长度  内容
0     6     魔数 07 08 56 32 08 07
6     4     aes_size (u32 LE)   实测恒 0x400 = 1024
10    4     xor_size (u32 LE)
14    1     标志字节（恒 0x01）
15    N     AES-128-ECB 密文，N = (aes_size // 16 + 1) * 16
15+N  M     中间明文（缩略图为 0，高清图为一大段）
末尾  xor_size  单字节 XOR 段
```

总长公式精确成立：`file_size == 15 + (aes_size//16+1)*16 + raw + xor_size`

**密钥完全离线派生，不需要碰微信进程**：

```python
code    = MMKV 统计文件名里的数字     # %APPDATA%\Tencent\xwechat\net\kvcomm\key_<code>_*.statistic
wxid    = 数据目录名去掉 _xxxx 后缀   # snowfrostsky_da31 -> snowfrostsky
aes_key = md5(f"{code}{wxid}").hexdigest()[:16].encode()   # 16 个 ASCII 字符
xor_key = code & 0xFF                 # 本机实测 0xA0
```

`v2dec.auto_key(数据根目录)` 会自动扫 MMKV → 遍历 code×wxid → 用真实 V2 文件做 oracle 验证，
一次 AES 单块运算即可确认，微秒级。

### 三种质量档（同一张图最多三份）

| 文件名 | 质量 | 什么时候存在 |
|---|---|---|
| `{md5}.dat` | 显示版（聊天窗里看到的） | 收到消息即下载 |
| `{md5}_h.dat` | **高清原图**（2MB 级） | **只有你点开过大图才有** |
| `{md5}_t.dat` | 小缩略图（120×180 级） | 始终有 |

实测某群 4728 张：仅缩略图 4166 / 显示版 329 / 高清原图 237。
**"图片很糊"多数不是解密问题，而是微信压根没下载过高清原图**——
`msg/attach`、hardlink 索引、`cache/*/Message/*/Thumb` 三个地方都查过才能下这个结论。

### wxgf 转码（显示版/高清图常是这个格式）

V2 解出来的显示版与高清图，很大比例是微信自研的 **wxgf**（头 `wxgf`），不是 JPEG。
社区没有纯 Python 解码器，但微信自带：**主程序安装目录**下的 `VoipEngine.dll`，
导出函数 `wxam_dec_wxam2pic_5`，ctypes 直接调（见 `scripts/wxam.py`）。

⚠ 三个坑：
1. 第 5 个参数 cfg **必须是有效指针**，传 NULL 直接 access violation；
   缓冲区至少 32 字节，首 4 字节 int 填格式：`0=jpeg 1/2=png 3=gif`
2. 必须用**主程序安装目录**那个约 20MB 的 DLL；
   `Roaming\Tencent\WeChat\XPlugin\...\RadiumWMPF\runtime\VoipEngine.dll` 是小程序运行时版本，别用错
3. 并发调用要加锁 + DLL 单例，否则 LoadLibrary 互相踩崩（表现为"图片全部 404"）

### 其它要点

- 缓存位置 `<xwechat_files>/<账号>/msg/attach/<md5(会话名)>/<YYYY-MM>/Img/`
- **会话目录名 = md5(会话 username)**，知道群名就能直接算出目录，不必查 hardlink
- 磁盘文件名就是消息 XML 里的 `md5`（CDN md5），**可以直接拼文件名**；
  hardlink 库只是兜底（`dir1` 是会话 hash 目录、`dir2` 是月份，**顺序写反 100% 找不到且不报错**）
- 只能导出**本机已缓存**的图。手机端看过、电脑端没点开过的，本地无缓存
- 按发送人归档时注意 `Name2Id` 的**同人双身份**（微信号一个 rowid、wxid 另一个），需合并；
  群名片用 `room_map()`，但解析结果可能夹带控制字符，**入库/建目录前必须过滤不可打印字符**
  （否则 `os.makedirs` 报 `WinError 123`）

细节见 `references/wechat4-media.md`。

## 路线 A · wx-cli 原路线（微信 ≤ 4.1.9）

安装：`install.ps1`（管理员权限，从 npm registry 拉 `wx.exe`）
自检：`doctor.ps1`
初始化：`wx init`（管理员权限 + 微信正在运行）

```bash
wx sessions                          # 最近会话
wx unread                            # 未读
wx history "张三" -n 2000             # 聊天记录
wx history "AI群" --since 2026-09-01
wx search "关键词"                    # 全库搜索
wx contacts | wx members "群名"       # 联系人 / 群成员
wx favorites --type image            # 收藏
wx stats                             # 统计报告
wx export "张三" -o out.json          # 导出
wx sns-feed | wx biz-articles        # 朋友圈 / 公众号缓存
```

默认 YAML 输出（省 token），加 `--json` 输出 JSON。

## 故障排查

| 症状 | 原因与处理 |
|---|---|
| `capture_key.py` 抓不到 key | 用户没在窗口内扫码；重跑 `--launch` 并务必扫码 |
| 微信被顺带关掉了 | 旧版异常退出导致连坐，v4 已加 `try/finally` 保护；重开微信即可 |
| 抓到的 key `extract` 报 0 命中 | 十有八九是把 passphrase 当 enc_key 直用了，须再派生一次 |
| `unable to open database file` | 库带残余 `-wal`，非路径错。`wxlib.connect_ro()` 已用 `immutable=1` 兜底 |
| `chat.py list` 找不到某会话 | 该会话无 `Msg_` 表（已清理）或被分到 `biz_message_*` |
| 明明有图却一张都查不到 | ① 没装 zstandard ② 会话的 `Msg_` 表跨多个 `message_N.db`，用 `locate_table` 跨库找 |
| 某人的发言/图片少了一半 | `Name2Id` 同人双身份（微信号一个 rowid、wxid 另一个），需合并 |
| 图片导出 0 张 | 该图本地未缓存（仅手机端看过），或属于未攻克的 `_h.dat` 容器 |
| 中文乱码 | 字段为 zstd / UTF-16-LE，`wxlib.decode_raw` 自动处理；仍乱码请装 zstandard |
| `wx init` 提取 0 密钥 | 微信 ≥ 4.1.10，改用路线 B |

## 合规与免责

- 默认只操作**当前登录用户本机**的微信数据目录。
- 请勿用于读取、导出或传播他人聊天数据。
- 上游 `jackwener/wx-cli` 曾因 DMCA 下线；本 skill 代码为本地数据处理用途，
  公开发布前请自行评估所在司法辖区的合规风险。
- 解密产物（`decrypted/`、`all_keys.json`）含敏感内容，**请勿上传公网**、勿提交进 git。

## Bundled Resources

`scripts/`

- `capture_key.py` — 硬件断点密钥捕获器（`--launch` 冷启动 / 附着两种模式）
- `key_tool.py` — SQLCipher 密钥派生与全库解密（第三方，见 README 致谢）
- `chat.py` — 统一查询入口（list / dump / stats / shares / pics）
- `wxlib.py` — 公共库：目录定位、内容解码、跨库定位消息表、群成员映射
- `media.py` — 图片缓存解密与导出（XOR 0xA0 + hardlink 索引还原路径）
- **`v2dec.py`** — V2/V1/V0 解密器 + 密钥离线派生（`auto_key()` 一条龙）
- **`wxam.py`** — wxgf(WxAM) → JPEG/PNG/GIF 转码（调微信自带 `VoipEngine.dll`）
- `install.ps1` / `doctor.ps1` — 路线 A 安装与环境自检

`references/`

- `wechat4-crypto.md` — 加密体系：三层密钥派生、HMAC 校验、断点 RVA 定位法
- `message-schema.md` — 消息表结构、`local_type` 复合值、`Name2Id` 陷阱、字段解码
- `wechat4-media.md` — 图片缓存目录布局、三种质量档、V2 格式与密钥派生全解
- `pitfalls.md` — 完整踩坑录（**必读**，能省几小时）
- `agent-skill.md` — 上游 wx-cli 自带 Agent 参考
