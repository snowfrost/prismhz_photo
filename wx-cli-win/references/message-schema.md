# 微信 4.x 本地库结构速查（实测 4.1.15.13）

> 数据来源：本机 `D:\SynologyDrive\Office\xwechat_files\snowfrostsky_da31\db_storage`
> 解密后 28 个库，含 `contact / message / sns / favorite / emoticon / session / hardlink` 等。
> 所有字段名均取自 `sqlite_master` 的真实 DDL，非推测。

## 一、顶层目录清单

解密产出目录 `decrypted/` 下的子目录与内容：

| 子目录 | 说明 | 关键库 |
|---|---|---|
| `contact/` | 联系人、群、标签、陌生人票据 | `contact.db`（17 张表） |
| `message/` | 会话消息正文 | `message_0..4.db`（单库 ~60MB，316 张 Msg 表）、`biz_message_*`、`media_0.db` |
| `session/` | 会话列表（最近联系人、置顶、免打扰） | `session.db` |
| `sns/` | 朋友圈时间线、点赞评论 | `sns.db` |
| `favorite/` | 收藏 | `favorite.db` |
| `emoticon/` | 表情包 | `emoticon.db` |
| `hardlink/` | 头像与资源硬链接索引 | — |
| `head_image/` `third_app_icon/` | 头像、小程序图标缓存 | — |

`message_N.db` 为何有多个：按会话 hash 分片，一个会话的表只存在于其中一个库。
**必须跨库搜索表名**，只查 `message_0.db` 会漏掉大量会话 —— 这正是 `wxlib.locate_table()` 存在的理由。

## 二、消息表 `Msg_<md5(username)>`

表名后缀 = `md5(username)` 的 32 位小写十六进制。
群 `56249627446@chatroom` → `Msg_fedae05b793451df12f884b121931b99`。

```sql
CREATE TABLE Msg_XXXX(local_id INTEGER PRIMARY KEY AUTOINCREMENT,
  server_id INTEGER, local_type INTEGER, sort_seq INTEGER,
  real_sender_id INTEGER, create_time INTEGER,
  status INTEGER, upload_status INTEGER, download_status INTEGER,
  server_seq INTEGER, origin_source INTEGER,
  source TEXT, message_content TEXT, compress_content TEXT,
  packed_info_data BLOB,
  WCDB_CT_message_content INTEGER DEFAULT NULL,
  WCDB_CT_source INTEGER DEFAULT NULL)
```

| 字段 | 用途 | 坑点 |
|---|---|---|
| `create_time` | Unix 秒 | 直接 `datetime.fromtimestamp` |
| `local_type` | 消息类型，**可能是 64 位复合值** | 必须 `base = local_type & 0xFFFFFFFF` |
| `real_sender_id` | 发信人在 `Name2Id` 中的 rowid | 同一人可能有**多个 rowid**，见下 |
| `message_content` | 正文（明文 UTF-8 或 zstd 压缩） | 短文本通常明文，长 XML 常压缩 |
| `compress_content` | 压缩副本 | `message_content` 解不出时兜底 |
| `packed_info_data` | protobuf blob | 一般不用 |
| `WCDB_CT_*` | WCDB 的"压缩标记"列（SQLiteCipher 特性） | 不是业务字段，忽略 |

### `local_type` 复合值（重点）

实测目标群的取值分布：

```
local_type          count    base(=&0xFFFFFFFF)  high(=>>32)
1                    2857        1                0
3                     411        3                0
244813135921          365       49               57
47                    303       47                0
10000                 110    10000                0
219043332145           39       49               51
266287972401           18       49               62
8594229559345           4       49             2001
```

**没有任何一条 type=49 是以纯 `49` 出现**，全部带高位。写 `WHERE local_type=49` 会查出 0 行。
正确写法：`WHERE (local_type & 0xFFFFFFFF) = 49`。
高 32 位的含义是 49 类消息的子业务标记（57=引用回复、51=不支持内容/视频卡片、62=拍一拍、2001=特殊），
与 `<appmsg><type>` 里的值常常一致，但**不要依赖它**，以 XML 内 `<type>` 为准。

### 消息类型对照（base type）

| base | 含义 | 正文形态 |
|---|---|---|
| 1 | 文本 | `wxid_xxx:\n内容` |
| 3 | 图片 | XML `<msg><img .../>` |
| 34 | 语音 | XML + `media_*.db` 的 `VoiceInfo` |
| 43 | 视频 | XML `<videomsg>` |
| 47 | 表情/动图 | XML `<emoji>` |
| 48 | 位置 | XML `<location>` |
| 49 | App 消息（文件/链接/小程序/接龙/拍一拍/引用） | XML `<appmsg><type>N` |
| 10000 | 系统提示（撤回、进群、红包领取） | XML `<sysmsg>` 或纯文本 |

`<appmsg><type>` 子类型实测分布：

| appmsg type | 含义 | 关键字段 |
|---|---|---|
| 5 | 网页链接/公众号卡片 | `<title>` `<url>` |
| 6 | 文件 | `<appattach><totallen>` `<fileext>` `<aeskey>` `<cdnattachurl>` |
| 19 | 合并转发的聊天记录 | `<title>群聊的聊天记录`、`<recorditem>` 嵌套 |
| 51 | 当前版本不支持展示（多为视频/音乐卡片） | `<url>` 指向 support.weixin.qq.com |
| 53 | 接龙 | `<title>#接龙\n…` |
| 57 | 引用回复 | `<title>` 是被引原文，`<refermsg>` 里是原消息 |
| 62 | 拍一拍 | `<title>"A" 拍了拍 "B" 脑袋` |

## 三、`Name2Id`：发信人映射（最大陷阱）

```sql
CREATE TABLE Name2Id(user_name TEXT PRIMARY KEY, is_session INTEGER)
```

主键是 `user_name` **而不是 rowid**，所以 rowid 是 SQLite 隐式分配的插入序号。
`real_sender_id` 存的就是这个隐式 rowid。查询方式：

```python
# 错：SELECT rowid, user_name ... 拿到的是隐式 rowid，可用但不可靠排序
# 对：一次性载入 dict 再查，且要处理同人双身份
senders = dict(conn.execute("SELECT rowid, user_name FROM Name2Id"))
```

**同人双身份**：同一自然人可以在同一库里占两个 rowid。
本次实测 `rowid 8 = XUbb___`（微信号）与 `rowid 31 = wxid_2duka72gnph842`（wxid）是同一个人，
消息里 `real_sender_id` 混用两者。按单个 id 过滤会**丢掉一半内容**（曾导致某人的图片提取结果为 0）。
稳妥做法：先把候选人都找出来，用 `IN (8, 31)` 或先在 Python 侧归一化为 wxid。

`contact.db` 里还有一张 `name2id`（小写，无下划线）和 `encrypt_name2id`，那是联系人侧的另一套映射，与本表同名不同物，别混用。

## 四、`contact.db`

```sql
CREATE TABLE contact(id INTEGER PRIMARY KEY, username TEXT, local_type INTEGER,
  alias TEXT, encrypt_username TEXT, flag INTEGER, delete_flag INTEGER, verify_flag INTEGER,
  remark TEXT, nick_name TEXT, pin_yin_initial TEXT, quan_pin TEXT,
  big_head_url TEXT, small_head_url TEXT, head_img_md5 TEXT,
  chat_room_notify INTEGER, is_in_chat_room INTEGER, description TEXT,
  extra_buffer BLOB, chat_room_type INTEGER)
```

- 显示名优先级：`remark`（我设的备注）> `nick_name`（对方昵称）> `username`（wxid）
- 字段名是 `username`，**不是** `user_name`（与 `Name2Id` 相反，两个库写法不一样）

```sql
CREATE TABLE chat_room(id INTEGER PRIMARY KEY, username TEXT, owner TEXT, ext_buffer BLOB)
```

`ext_buffer` 是 protobuf，内含群成员名单。粗略提取群名片→wxid：

```python
# field 2 (\x12) = 群名片, field 2 (\x12 内嵌) = wxid
for m in re.finditer(rb"\x12([\x01-\x7f])([^\x12\"]{1,120})", buf):
    ln = m.group(1)[0]
    name = m.group(2)[:ln].decode("utf-8", "replace")
    tail = buf[m.end(): m.end()+40]
    if re.match(rb"\"\x11|\"\x13|\"\x10", tail):
        wxid = tail[2:2+tail[1]].decode("utf-8", "replace")
```

这条正则是启发式的（没跑完整 protobuf 解析器），遇到生僻结构会漏。
**信心：中（约 70%）** —— 依据是在 chruang buffers 上抽样验证过，但未做全量交叉校验；
需要更稳的话请装 `protobuf` 或 `blackboxprotobuf` 做结构化解码。

## 五、`media_*.db`（语音）

```sql
CREATE TABLE VoiceInfo(chat_name_id INTEGER, create_time INTEGER, local_id INTEGER,
                       svr_id INTEGER, voice_data BLOB, data_index TEXT DEFAULT '0')
```

语音的实际音频在 `voice_data` 里（ silk 编码），可用 `silk-v3-decoder` 之类转 mp3。

## 六、字段解码

`message_content` / `compress_content` 可能是三种形态之一，`wxlib.decode_raw()` 自动判别：

| 形态 | 识别方式 | 处理 |
|---|---|---|
| zstd 压缩 | magic `28 b5 2f fd` | `zstandard.ZstdDecompressor().decompress()`，建议 `max_output_size=50MB` |
| UTF-8 明文 | 直接 decode 成功且无 `\x00` | 直接用 |
| UTF-16-LE | UTF-8 解不出或前 8 字节含 `\x00` | `.decode("utf-16-le")` |

**必须安装 zstandard**：`pip install zstandard`。
缺它的时候，所有压缩 XML 都会静默返回 `None`，表现为"图片/文件一条都查不到"，非常容易误判成"群里没人发图"。

纯 Python 环境（无 C 扩展）没有救急替代方案，务必提前装。
