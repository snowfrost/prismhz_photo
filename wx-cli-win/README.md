# wx-cli-win

在 Windows 上读取**本人**微信本地数据库的完整链路：抓密钥、全库解密、
聊天记录查询、群聊内容提取、图片从缓存还原导出。

数据全程留在本机，不上传任何服务器。

## 两条路线

| | 路线 A：wx-cli | 路线 B：自研解密链路 |
|---|---|---|
| 适用微信版本 | 4.0.x ～ 4.1.9 | **4.1.10+（实测 4.1.15.13）** |
| 原理 | 进程内存扫描 raw key | 硬件断点抓 `setCipherKey` passphrase → PBKDF2 派生 |
| 前置 | 管理员跑 `wx init` | 用户重新扫码登录一次 |
| 覆盖 | 上游 CLI 命令集 | 全库解密 + 任意 SQL + 图片还原 |

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

图片还原也打通了，这是多数同类方案没做到的部分：

- **磁盘文件名解谜**：既不是 XML 里的 `md5=` 也不是 `aeskey=`，得查
  `hardlink.db` 的 `image_hardlink_info_v4` 表，再按 `dir1 → dir2` 顺序拼路径
  （顺序写反会 100% 找不到文件，且不报错）
- **XOR 密钥**：7052 张缩略图统一用 `0xA0` 单字节异或，解出即标准 JPEG
- 9984 张索引里 7074 张可还原，剩余 2852 张属未攻克的 `_h.dat` V2 容器

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
│   ├── install.ps1             # 路线 A 安装
│   └── doctor.ps1              # 路线 A 自检
└── references/
    ├── wechat4-crypto.md       # 加密体系与断点定位法
    ├── message-schema.md       # 消息表结构
    ├── wechat4-media.md        # 图片缓存与还原
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
