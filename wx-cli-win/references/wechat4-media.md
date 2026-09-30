# 微信 4.x 图片缓存与还原（实测 4.1.15.13）

> 2026-10-01 在 Windows + 微信 4.1.15.13 上实测通过。所有结论均来自本机真实
> 9984 条 `image_hardlink_info_v4` 索引的批量验证，非推测。

## 一、缓存目录布局

```
<xwechat_files>/<账号目录>/
  ├── db_storage/
  │   ├── hardlink/hardlink.db          ← 关键：图片索引
  │   └── message/message_0..4.db       ← 消息正文
  └── msg/
      ├── attach/<md5(会话名)>/<YYYY-MM>/Img/    ← 图片缓存
      ├── attach/<md5(会话名)>/<YYYY-MM>/Rec/    ← 语音缓存
      └── file/<YYYY-MM>/<真实文件名>            ← 文件（完全明文，含原扩展名）
```

要点：

- `attach/` 下的一级目录名 = `md5(username)`，与消息表后缀同一个值。
  群 `56249627446@chatroom` → `fedae05b793451df12f884b121931b99`。
- `file/` 下的文件**是明文的**，且保留真实文件名（如 `0. 民事起诉状260904.pdf`）。
  要拿群里分享的文件，直接读这个目录最快，不用解密。
- 图片缓存只保留**本机加载过的**缩略图。手机端看过、电脑端没点开的图不会落到本地。

## 二、磁盘文件名之谜

图片消息 XML 里有 `md5=` 和 `aeskey=` 两个 32 位 hex 字段，但**都不是**磁盘文件名。

实测：4618 个群内图片 md5 ∩ 3444 个缓存文件 stem = **0**；
4618 个 aeskey ∩ stem = **0**。又试了 `md5(md5)` / `md5(aeskey)` /
`md5(md5+aeskey)` / `md5(aeskey+md5)` / `md5(房间号+md5)` 等 8 种组合，全部 0 命中。

**正确解法：查 `db_storage/hardlink/hardlink.db`。**

```sql
CREATE TABLE dir2id(username TEXT PRIMARY KEY);           -- rowid -> 'YYYY-MM' 或会话hash
CREATE TABLE image_hardlink_info_v4(
    md5_hash INTEGER, md5 TEXT, type INTEGER, file_name TEXT,
    file_size INTEGER, modify_time INTEGER, dir1 INTEGER, dir2 INTEGER,
    _rowid_ INTEGER PRIMARY KEY ASC, extra_buffer BLOB);
```

还原路径：

```
路径 = <attach>/{dir2id[dir1]}/{dir2id[dir2]}/Img/{file_name}
```

**顺序是 `dir1` 在前、`dir2` 在后**。实测验证：`dir1,d2` 顺序 400/400 命中，
`d2,dir1` 顺序 0/400。写反了不会报错，只会全部 `missing`——
这是最容易卡住的一步。

`dir1` 指向会话 hash 目录，`dir2` 指向 `YYYY-MM` 月份目录（实测 319 条 dir2id）。

## 三、四种后缀与加密形态

有效索引 8771 张（另有 55 条索引指向已被清理的缓存文件，`load_index` 默认过滤）：

| 后缀 | 数量 | 占比 | 形态 | 处理 |
|---|---|---|---|---|
| `_t_W.dat` | 4650 | 53.0% | XOR | `bytes(b ^ 0xA0 for b in data)` |
| `_W.dat` | 1638 | 18.7% | XOR | 同上 |
| 无后缀 `{hash}.dat` | 1787 | 20.4% | V2 容器 | **未攻克** |
| `_h.dat` | 674 | 7.7% | V2 容器 | **未攻克** |
| `_NW.dat` | 22 | 0.3% | 明文 | 文件头已是 `ff d8 ff e0`（JPEG），直接复制 |

**可还原率 71.7%**（6288/8771），分层抽样各 60 张验证：`_W` / `_t_W` → 100% `xor`，
`_h` / 无后缀 → 100% `v2-unsolved`，`_NW` → 100% `plain`。后缀与形态严格一一对应。

### XOR 密钥是全局常量

对全部 9984 个历史索引文件逐个暴力 1..255 求解，命中结果**全部集中在 0xA0**（7052 次），
无第二个密钥。所以：

```
5f 78 5f 40 ...  ^ 0xA0  =  ff d8 ff e0 ...   → 标准 JPEG
```

解出的 JPEG 经 PIL 验证可正常 `load()`，尺寸/格式均正确（如 290×170、163×290、120×120）。

### V2 容器（未解出，含 `_h.dat` 与无后缀约 2852 张）

16 字节头结构：

```
07 08 56 32 | 08 07 00 04 | <per-file u32> | <per-file u32 or 常量>
   magic      恒定         随文件变化         _h 恒为 0xDB000010
```

- `_t` 与 `_h` 的 `[12:16]` 各自恒定，但两者不同 → 可能是 flag/类型
- `[4:8]` 在全部文件里恒为 0x04000708，跟内容无关，不是长度
- 无后缀与 `_h` 是**同一容器**（前缀 16 字节一致），不是两种格式

已排除的路径（勿重复）：

- 用 XML 的 `aeskey` 做 AES-ECB，offset 0…64 全试 → 无命中
- 同上但 CBC(zero IV / 文件头 IV / 自引用 IV) → 无命中
- 全文件 XOR 0xA0 → 无命中
- 文件头 12 字节 = AES-ECB(aeskey, counter) → 无命中

踩过的坑：一次性扫 offset 0…64 + 4662 个 aeskey 时曾报过一次
`offset=6 → 'BM'` 命中，验证发现明文 `filesize` 字段是 28 亿、
`width=636504492`，明显是假阳性（"BM" 只有 2 字节，随机碰撞概率约 1/65536，
在 30 万次尝试里必然出现）。**判 JPEG 要认 3 字节 `ff d8 ff`，别信 2 字节魔数。**

结论：V2 容器装的是高清原图，缩略图 `_W` / `_t_W` 已够内容识别。
想拿高清图需继续逆向第二层容器，收益/成本比低，暂不投入。

## 四、批量导出代码

`scripts/media.py` 已封装：

```python
import media, wxlib

dec = wxlib.find_dec_dir()
stat = media.export(dec, "out/pics", max_n=500)
# {'plain': 1, 'xor': 399, 'v2-unsolved': 2, 'missing': 0, 'exported': 400, 'indexed': 8822}
```

或走命令行：

```bash
python chat.py pics "群名" --days 30 --export --out pics
```

产出 `index.tsv`（time / who / md5 / thumbsize / local_file / form）+ 还原出的图片文件。

## 五、把图与发送人对应起来

`index.tsv` 里的 `who` 来自 `Name2Id` 映射。注意同人双身份问题：
`real_sender_id` 可能落在同一人的多个 rowid 上，需要按 wxid 合并，
否则会出现"某人一张图都没有"的假象。
