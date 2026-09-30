# 微信 4.x 本地数据库加密体系

> 面向“为什么 wx-cli 在 4.1.10+ 失效，以及路线 B 为什么能work”的技术说明。
> 适用版本：桌面版 Windows 4.x（实测 4.1.15.13）。

## 1. 加密参数（SQLCipher 4 兼容）

| 项 | 值 |
|---|---|
| 页密码套件 | AES-256-CBC |
| 页大小 | 4096 字节 |
| 完整性校验 | HMAC-SHA512 |
| salt | 数据库文件**前 16 字节** |
| reserve（每页保留区） | 80 字节 = IV(16) + HMAC(64) |
| 密钥派生 | PBKDF2-HMAC-SHA512，iter = **256000**，dklen = 32 |
| 每个库独立 | 是，同 passphrase 但不同 salt → 不同 raw key |

## 2. 三层密钥推导

```
passphrase (32 字节，微信运行时传给 WCDB)
    │  PBKDF2-HMAC-SHA512(passphrase, salt, 256000, 32)
    ▼
raw_key / enc_key (32 字节) ──────────► AES-256-CBC 页解密
    │  mac_salt = salt ⊕ 0x3A
    │  PBKDF2-SHA512(raw_key, mac_salt, 2, 32)
    ▼
mac_key (32 字节) ──────────► HMAC-SHA512 完整性校验
```

校验范围（`verify_enc_key` 实现）：

```python
mac_salt  = bytes(b ^ 0x3A for b in salt)          # salt = db[:16]
mac_key   = pbkdf2_hmac("sha512", enc_key, mac_salt, 2, 32)
data      = page1[16 : 4096 - 80 + 16]             # 跳过 salt，含 reserve 中的 IV
stored    = page1[4096 - 64 : 4096]                # 页尾 64 字节 HMAC
ok        = hmac_sha512(mac_key, data) == stored
```

这是**验证 key 是否猜对**的最快手段（2 轮迭代，毫秒级），
比直接 PBKDF2 256000 轮快几个数量级——暴力破解时务必先用它做筛选。

## 3. 为什么 old-style 方法失效

| 方法 | 失效原因 |
|---|---|
| 内存扫描找 raw key | 4.1.10+ 内存里不再长期保存明文 raw key |
| 内存扫描找 passphrase | 运行时做了异或混淆 + 定时清零 |
| `wx_key` 特征码 | 24 字节 pattern 在 4.1.15.13 中 0 匹配 |
| CNG (`BCryptKeyDerivation`) 断点 | 微信自带 PBKDF2 实现，不调用系统 CNG |
| 本地 PBKDF2 暴力 | 候选空间太大且 raw key 早已不在内存 |

## 4. 硬件断点：抓 `setCipherKey`

**核心思路**：不找结果（raw key），抓**输入**（passphrase）。
WCDB 打开每个加密库时都会调用 `setCipherKey(cipher?)`，参数里就是 passphrase。

### x64 调用约定

```
setCipherKey(rcx = this, rdx = UnsafeData*, r8d = pageSize, r9d = cipherVersion)
UnsafeData 布局: [RDX+0x08] = m_buffer, [RDX+0x10] = m_size
```

### 如何定位函数地址（离线分析，不需运行微信）

1. 在 `Weixin.dll` 的 `.rdata` 找字符串 `com.Tencent.WCDB.Config.Cipher`
2. 找引用该字符串的初始化指令序列：`lea rcx,[obj]; lea rdx,[str]; call`
3. 得到 LiteralString 对象（本例位于 `.data`），反查其**代码引用**
4. 命中信号：附近出现 `mov r9d, 0x80000000`（`Priority::Highest`）
5. 用 `.pdata` 段的 RUNTIME_FUNCTION 记录确定函数精确起止边界

> ⚠️ **RVA 随版本变化**。本仓库实测：4.1.15.13 → `setCipherKey` RVA = `0x5FF520`。
> 换版本请重新按上述 5 步定位，或用 `.pdata` 中的边界做静态对齐。

### 调试器要点（capture_key.py）

- `DebugActiveProcess` 附着**主进程**（`Weixin.dll` 只在主进程加载，约 1GB 内存的那个）
- 补 PEB 反调试标记：`PEB+2 (BeingDebugged) = 0`、`PEB+0xBC (NtGlobalFlag) = 0`
- 对所有线程设 `DR0 = base + RVA`，`DR7` 置位 L0（执行断点，1 字节）
- `CREATE_THREAD_DEBUG_EVENT` 里给新线程补断点（微信会频繁建线程）
- 命中后：`DR6` 清理 → 设 `EFlags.RF` → `DBG_CONTINUE` 放行
- 结束时必须 `DebugActiveProcessStop`（否则被调试进程会被杀）

## 5. 抓到的到底是什么

`setCipherKey` 抓到的是 **passphrase 的 32 字节原始二进制**（不是 64 字符 hex 字符串）。

验证三种假设时，只有“原始二进制当 passphrase 再 PBKDF2 派生”是对的：

```
A:  32 字节直接当 enc_key            → 0/28 命中
B1: 32 字节原始二进制当 passphrase   → 28/28 命中 ✅
B2: 64 字符 hex 字符串当 passphrase  → 0/28 命中
```

`key_tool.py set-passphrase <64位hex>` 内部就是 `bytes.fromhex(...)` 走 B1 路线。
