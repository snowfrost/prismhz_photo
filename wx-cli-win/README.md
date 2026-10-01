# wx-cli-win

在 Windows 上读取**本人**微信本地数据库的完整链路：抓密钥、全库解密、
聊天记录查询、群聊内容提取、图片全格式解密导出（V0/V1/V2 + wxgf）。

数据全程留在本机，不上传任何服务器。

## 两条路线

| | 路线 A：wx-cli | 路线 B：自研解密链路 |
|---|---|---|
| 适用微信版本 | 4.0.x ～ 4.1.9 | **4.1.10+（实测 4.1.15.13）** |
| 原理 | 进程内存扫描 raw key | 硬件断点抓 `setCipherKey` passphrase → PBKDF2 派生 |
| 前置 | 管理员跑 `wx init` | 用户重新扫码登录一次 |
| 覆盖 | 上游 CLI 命令集 | 全库解密 + 任意 SQL + 图片全解密 |

微信 ≥ 4.1.10 后不再在内存中缓存明文 raw key，路线 A 必然失败，请直接走路线 B。

## 安装

```bash
pip install zstandard        # 必须
```

把整个文件夹拷进 `~/.workbuddy/skills/` 即被 WorkBuddy 识别为技能。

## 快速开始（路线 B）

```bash
cd scripts

# 1. 抓密钥（只需一次，会提示用户重新扫码登录）
python capture_key.py --launch

# 2. 派生并解密全库
python key_tool.py set-passphrase <64位hex>
python key_tool.py extract --db-dir <db_storage> --output all_keys.json
python key_tool.py decrypt --db-dir <db_storage> --keys all_keys.json --output decrypted

# 3. 查询
python chat.py list
python chat.py dump  "群名" --days 30
python chat.py stats "群名" --days 30
python chat.py shares "群名" --days 30
python chat.py pics  "群名" --days 30 --export --out pics
```

## 这条路走通了什么

微信 4.1.15.13 上，上游 `jackwener/wx-cli` 完全失效（提取 0 密钥）。
本包用硬件断点在 `setCipherKey` 处截获 passphrase，再按 SQLCipher 4 规则派生，
`28/28` 个库全部解密通过、HMAC 校验全绿。

图片**全格式**解密也打通了，四块拼图：

- **V2 格式**：`07 08 56 32 08 07` 签名 + `aes_size`/`xor_size` 双长度字段，
  密文从 **offset 15** 起（`(aes_size//16+1)*16` 字节），中间明文，
  尾部 `xor_size` 字节单字节 XOR。总长公式逐字节验证成立。
- **AES 密钥离线派生**：`code` 藏在 MMKV 统计文件名里，
  `aes_key = md5(f"{code}{wxid}").hexdigest()[:16]`，`xor_key = code & 0xFF`。
  **不碰微信进程、不扫内存**，微秒级验证。
- **wxgf 转码**：V2 解出的显示版/高清图多为微信自研 `wxgf` 格式，
  调主程序目录下的 `VoipEngine.dll` 的 `wxam_dec_wxam2pic_5` 转 JPEG。
- **三种质量档**：`{md5}.dat` 显示版 / `_h` 高清原图 / `_t` 缩略图。
  「图很糊」多半是微信压根没下载过高清原图，不是解密问题。

实测某群 **4728 张图 100% 解密成功、0 张损坏**。

## 目录

```
├── SKILL.md                    # 技能主文件（Agent 读这个）
├── README.md                   # 本文件
├── LICENSE                     # Apache-2.0
├── config.example.json
├── scripts/
│   ├── capture_key.py          # 硬件断点密钥捕获器
│   ├── key_tool.py             # SQLCipher 密钥派生与全库解密
│   ├── chat.py                 # 统一查询入口
│   ├── wxlib.py                # 公共库
│   ├── media.py                # 图片缓存解密与导出
│   ├── v2dec.py                # V2/V1/V0 解密 + 密钥离线派生
│   ├── wxam.py                 # wxgf → JPEG/PNG/GIF 转码
│   ├── install.ps1             # 路线 A 安装
│   └── doctor.ps1              # 路线 A 自检
└── references/
    ├── wechat4-crypto.md       # 加密体系与断点定位法
    ├── message-schema.md       # 消息表结构
    ├── wechat4-media.md        # 图片体系全解（V2 格式/密钥派生/wxgf）
    ├── pitfalls.md             # 踩坑录
    └── agent-skill.md          # 上游 wx-cli 参考
```

## 致谢

- 路线 A 封装自 [jackwener/wx-cli](https://github.com/jackwener/wx-cli)（原项目曾因 DMCA 下线）。
- `scripts/key_tool.py` 的 SQLCipher 解密实现参考自第三方开源工具，遵循其上游许可。
- 加密参数推导参考 SQLCipher 4 官方文档与多个微信 4.x 逆向分析成果。

## 合规与免责

- 本工具默认只操作**当前登录用户本机**的微信数据目录。
- 请勿用于读取、导出或传播他人聊天数据。
- 解密产物（`decrypted/`、`all_keys.json`）含敏感内容，请勿上传公网、勿提交进 git。
- 请在所在司法辖区内自行评估合规风险后使用。

## License

Apache-2.0
