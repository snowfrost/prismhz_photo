# 微信 4.x 图片体系全解（V2 已攻克）

> 实测环境：微信 4.1.15.13 / Windows 11 / 账号 snowfrostsky
> 验证规模：某群 4728 张图 **100% 解密成功**，0 张损坏

## 一、图片存在哪

| 媒体 | 路径 | 命名 |
|---|---|---|
| 聊天图片 | `msg/attach/<md5(会话username)>/<YYYY-MM>/Img/*.dat` | 内容 md5，后缀区分质量档 |
| 聊天气泡缓存 | `cache/<YYYY-MM>/Message/<md5(会话username)>/Bubble/<md5>_b.dat` | md5 |
| 聊天缩略图 | `cache/<YYYY-MM>/Message/<md5(会话username)>/Thumb/<md5>` | md5 |
| 朋友圈浏览缓存 | `cache/<YYYY-MM>/Sns/Img/<两位hex>/<md5>` | md5，无扩展名 |
| 视频 | `msg/video/...` | md5 |

**会话目录名 = md5(会话 username)**，这一点很重要：知道群名（`xxx@chatroom`）
就能直接算出目录，不必查 hardlink 数据库。

## 二、三代加密：V0 / V1 / V2

按文件头 6 字节签名区分：

| 版本 | 头签名 | 方案 | 密钥 |
|---|---|---|---|
| V0 | 无签名 | 整文件单字节 XOR | `首字节 ^ 0xFF`（JPEG 首字节恒 FF） |
| V1 | `07 08 56 31 08 07` | AES-128-ECB 头 + XOR 尾 | 固定 `cfcd208495d565ef` |
| **V2** | `07 08 56 32 08 07` | AES-128-ECB 头 + XOR 尾 | **账号级，离线派生** |

实测 4.1.13～4.1.15：朋友圈缓存 184/184 全是 V2；聊天图片抽样 400 个中 367 个是 V2。
**V2 是绝对主流。**

## 三、V2 格式逐字节

```
偏移   长度   内容
0      6      魔数 \x07\x08V2\x08\x07
6      4      aes_size (u32 LE)   —— 头部被 AES 加密的明文长度（实测恒 0x400 = 1024）
10     4      xor_size (u32 LE)   —— 尾部被单字节 XOR 的明文长度
14     1      标志字节（实测恒 0x01）
15     N      AES-128-ECB 密文，N = (aes_size // 16 + 1) * 16
15+N   M      中间明文（缩略图为 0，高清图为一大段）
末尾   xor_size  单字节 XOR 段
```

**总长公式精确成立**（三张不同大小的图逐字节验证）：

```
file_size == 15 + (aes_size // 16 + 1) * 16 + raw_len + xor_size
```

解密 = 三段拼接：

```python
plain = AES_ECB_dec(data[15 : 15+N])[:aes_size] + raw + bytes(b ^ xor_key for b in tail)
```

### ⚠ 踩过的坑（别再踩）

1. **不是"16 字节头"**。早期误判成 `07 08 56 32 | 08 07 00 04 | <u32> | <u32>` 共 16 字节，
   于是 AES 段起点算成 offset 16，整体错位一个字块，怎么试都不对。
   实际签名占 6 字节，**密文从 offset 15 开始**。
2. **AES 密文长度是 `(aes_size//16 + 1)*16`，不是向上取整**。
   `aes_size` 恰为 16 的倍数（实测恒 1024）时，PKCS7 会**多补一整块**（16 字节）。
   少算这一块，后面全部对不上。
3. **`15+N` 处的 16 字节"分隔尾"不是全局常量**。老资料写 `56fbf4...`，
   实测 4.1.x 已变。按长度跳过即可，**不要硬编码**。
4. 用 XML 里的 `aeskey` 做 AES-ECB / CBC 各种变体都是死路——**那把 key 跟 V2 无关**。

## 四、密钥离线派生（核心）

**密钥不落在磁盘上，但可以从 MMKV 文件名离线派生**，完全不需要扫内存 / 挂调试器：

```
code  = MMKV 统计文件名里的数字
        路径：%APPDATA%\Tencent\xwechat\net\kvcomm\key_<code>_<...>.statistic
        旧版：%APPDATA%\Tencent\WeChat\<n>\kvcomm\
              还有 \Tencent\xwechat\radium\ilink\...\kvcomm\
        正则：key_(\d+)_
wxid  = 数据目录名去掉 _xxxx 后缀          # snowfrostsky_da31 -> snowfrostsky

aes_key = md5(f"{code}{wxid}").hexdigest()[:16].encode()   # 16 个 ASCII 字符！
xor_key = code & 0xFF                                      # 本机实测 0xA0
```

### ⚠ 两个魔鬼细节

1. **`aes_key` 是 hexdigest 的前 16 个 ASCII 字符直接当 16 字节密钥用**，
   不是 hex 解码后的 8 字节。想当然解码，会浪费半小时。
2. **wxid 必须去掉 `_xxxx` 后缀**，否则派生出来的 key 解不开任何文件。

### 校验方法

拿任一 V2 文件的 `data[15:31]` 做一次 ECB 解密，明文命中图像魔数即为正确：

```
FF D8 FF     JPEG
89 50 4E 47  PNG
47 49 46 38  GIF
52 49 46 46  RIFF (WebP)
77 78 67 66  wxgf
```

一次 AES 单块运算，微秒级。遍历 `code × wxid` 通常几秒内收敛。

### ❗ 判据至少 3 字节

用 2 字节魔数（如 `89 50`）会踩假阳性：**同一账号下所有缩略图的首密文块完全相同**
（ECB + 相同 JPEG 头），判据退化成 1/65536，扫 5 万个候选几乎必然误报。
实测踩过：报 `offset=6 → BMP` 命中，验证发现明文 filesize=28 亿、width=636504492。

### 本机实测值（微信 4.1.15.13）

```
code    = 84645280
wxid    = snowfrostsky
aes_key = 2b295d0b959325f7
xor_key = 0xA0
```

只作核对用，换机/换号请走 `v2dec.auto_key()` 自动推导。

## 五、三种质量档（同一张图最多三份）

| 文件名 | 质量 | 什么时候存在 | 实测占比 |
|---|---|---|---|
| `{md5}.dat` | 显示版（聊天窗里看到的） | 收到消息即下载 | 7% |
| `{md5}_h.dat` | **高清原图**（2MB 级） | **只有你点开过大图才有** | 5% |
| `{md5}_t.dat` | 小缩略图（120×180 级，2～6KB） | 始终有 | 88% |

"图片很糊"**多数不是解密问题，而是微信压根没下载过高清原图**。
要下这个结论，需确认以下三处都没有：
`msg/attach` 的 `_h`/无后缀、hardlink 索引的备选落点、`cache/*/Message/*/Thumb`。

## 六、wxgf → JPEG 转码

V2 解出来的**显示版与高清图，很大比例是 wxgf**（头 `wxgf`），不是 JPEG。
它不是改头的 GIF，社区没有纯 Python 解码器——但微信自带：

- DLL：**主程序安装目录** `<微信安装目录>\<版本>\VoipEngine.dll`（约 20MB）
  ❗ 别用 `Roaming\Tencent\WeChat\XPlugin\...\RadiumWMPF\runtime\VoipEngine.dll`
  （小程序运行时版本，15MB，签名/行为不一致）
- 导出函数：`wxam_dec_wxam2pic_5`
- 签名：`(int64 in_ptr, int in_len, int64 out_ptr, int* out_size, int64 cfg_ptr) -> int64`

```python
cfg = create_string_buffer(32)
cast(cfg, POINTER(c_int))[0] = 0        # 0=jpeg 1/2=png 3=gif
out = create_string_buffer(52 * 1024 * 1024)
ret = fn(addr(inb), len(data), addr(out), byref(out_sz), addr(cfg))
```

⚠ 三个坑：
1. **cfg 不能传 NULL**，传了直接 access violation（第一次就是这么崩的）。
   缓冲区至少 32 字节，首 4 字节 int 填格式。
2. 必须用主程序目录那个 DLL，别用 RadiumWMPF 里的。
3. 并发要加锁 + DLL 单例，否则 LoadLibrary 互相踩崩，表现为"图片全部 404"，
   而 curl 串行测试一切正常，非常迷惑人。

实测：71KB wxgf → JPEG 152KB / PNG 1.9MB / GIF 1.0MB。
**默认取 mode=0（jpeg）**，体积与画质最平衡。

## 七、按发送人归档

```
message_<N>.db 的 Msg_<md5> 的 real_sender_id
        ↓
  同库 Name2Id.rowid  →  username
        ↓
  contact 表 remark/nick_name（备注优先）
        ↓
  群 chat_room.ext_buffer 的群名片（room_map()，优先度最高）
```

⚠ 注意：
1. **群的 `Msg_` 表可横跨多个 `message_N.db`**（实测某群横跨 message_0 与 message_4），
   只扫一个库会漏掉大部分图片消息。用 `wxlib.locate_table()`。
2. **`Name2Id` 同人双身份**：同一自然人可能占两个 rowid（微信号一个、wxid 一个），
   统计时要合并。
3. **群名片解析结果可能夹带控制字符**（`room_map()` 的正则边界所限），
   直接拿来建目录会报 `WinError 123 文件名、目录名或卷标语法不正确`。
   入库/建目录前必须过滤 `isprintable()` 且剔除 `\/:*?"<>|`。

## 八、故障速查

| 现象 | 原因 | 处理 |
|---|---|---|
| 解密后首块不是图像魔数 | 密钥错 / AES 段起点算错 | 重跑 `auto_key()`；确认起点是 15 不是 16 |
| 图片开头对、后面花 | AES 段长度少算一块 | 用 `(aes_size//16+1)*16` |
| 解出来是 `wxgf` 开头的乱码 | 需第二层转码 | 用 `wxam.convert()` |
| wxam 调用 access violation | cfg 传了 NULL | 给 32 字节缓冲区 |
| 建目录报 WinError 123 | 发送人名含控制字符 | `isprintable()` 过滤 + 剔非法字符 |
| 明明有图却"无缓存" | 微信没下载过（仅手机端看过） | 在电脑端点开一次即可落盘 |
| hardlink 路径全部 missing | `dir1`/`dir2` 顺序写反 | `attach/<dir2id[dir1]>/<dir2id[dir2]>/Img/` |

## 九、合规

全部操作**仅限处理本人微信本机数据**。密钥派生、解密、导出均不出本机。
未经他人同意获取、解密、传播他人微信数据违反《个人信息保护法》。
