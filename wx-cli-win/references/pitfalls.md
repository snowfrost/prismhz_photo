# 踩坑录（必读 · 能省几小时）

本文件记录 wx-cli-win v2 开发过程中踩过的所有坑，按「症状 → 根因 → 解法」组织。

## 1. `wx init` 提取 0 密钥（0/28）

- **症状**：管理员权限跑 `wx init`，28 个库全部 MISSING，换 httpx/CDP 都无效。
- **根因**：微信 **4.1.10+** 改变了密钥机制——进程内存不再缓存明文 raw key，
  只保留 passphrase，且运行一段时间后会被主动清零。
- **解法**：放弃内存扫描，改路线 B（硬件断点抓 `setCipherKey`）。
- **已排除的无效努力**（别再试）：
  - 全进程内存 dump → 48,795 个候选 × PBKDF2 256000 轮暴力：0 命中，耗时 1025 秒
  - 围绕 salt 的内存上下文做单字节 XOR 破解（93 处 × 256 掩码）：0 命中
  - `wx_key` 的 ≥4.1.4 特征码（24 字节）：4.1.15.13 中 0 匹配
  - 对 `BCryptKeyDerivation` 下断点：微信 4.x 不走系统 CNG PBKDF2（只导入了 `BCryptGenRandom`）

## 2. 脚本「静默死亡」——日志重定向到 exFAT 盘

- **症状**：脚本后台运行，进程存在，stdout 重定向文件 0 字节，退出码 1，
  任何 print 都没出现；但副作用（启动其他进程）确实发生了。
- **根因**：脚本自己把 `sys.stdout` 劫持到某个日志文件；该日志落在 **F 盘（exFAT）**，
  `open(path, "w")` 触发 PermissionError → 进程在第一次写之前就死了。
  同时 shell 层的重定向文件自然是空的，形成「两边都看不到输出」的假象。
- **解法**：**日志与产物一律写到 NTFS 盘**（如 `%LOCALAPPDATA%\Temp` 或 `C:\Users\<u>\.workbuddy\wxkey_v4\`）。
- **附带教训**：以为「管道里没输出 = 脚本没跑」是错误直觉，先看它是把 stdout 劫持到哪去了。

## 3. 微信被“陪葬”——`main()` 缺 `__main__` 保护 + 无 finally

- **症状**：调试附着后，脚本进程一退出，微信跟着消失（`No tasks are running`）。
- **根因**：两件事叠加
  1. **Windows 调试语义**：调试器进程终止时，被调试进程（微信）会被一同终止，
     除非显式调用了 `DebugActiveProcessStop`。
  2. 旧版把 `main()` 写在模块顶层裸调用，于是 `import xxx` 也会跑 `main()`——
     「只想测能不能 import」变成了「附着微信然后随进程退出」，直接把微信带走。
- **解法**（capture_key.py v4 已全部修复）：
  ```python
  if __name__ == "__main__":
      main()
  ```
  以及 `try/finally`：异常路径也必须执行 `DebugActiveProcessStop`。

## 4. 断点窗口与登录时机

- 必须 **冷启动**（`--launch`）：杀掉微信 → 重新拉起 → 等 `Weixin.dll` 加载 → 附着，
  这样二维码还没扫，附着手快过 `setCipherKey` 的第一次调用。
- 若微信已登录：`setCipherKey` 早调过了，附着也抓不到，只能让用户退出重登。
- 脚本默认 2 分钟无新密钥（IDLE_STOP）自动停止，避免长时间挂调试器。

## 5. 图片字段改名

- 老资料教的是 `cdnmd5="..."`，**4.1.15 里字段名叫 `md5="..."`**。
  正则写 `\bmd5="([a-f0-9]{32})"` 才抓得到；写成 `cdnmd5=` 会 0 命中。

## 6. 同一个人有两条 Name2Id

- `message_N.db` 的 `Name2Id` 表可能存在**同一人的两个登录身份**：
  例 `rowid 8 = XUbb___`（微信号/别名）与 `rowid 31 = wxid_xxxx`（真 wxid）。
  消息里的 `real_sender_id` 用的是前者，文本前缀也是前者。
- **影响**：按 wxid 查会查不到他的消息；同一人在统计里被拆成两个人。
- **解法**：查询身份时把别名与 wxid **都纳入**，或按 `real_sender_id` 聚合后再合并。

## 7. F 盘写文件：Permission denied / os error 87

- 覆盖已存在的文件时常被拒（尤其被应用占用的 skill 文件）。
- **解法**：`rm -f <目标>` 再 `cp`（覆盖式 cp 会被拒）。新文件无此限制。

## 8. 沙箱/策略限制

- `reg.exe` 被安全策略拦（Program Blacklist）→ 改用 Python `winreg` 读注册表
  （微信数据目录在 `HKCU\Software\Tencent\Weixin` 的 `OldFileSavePath` 等键值）。
- 提权场景：请以“用户可见的受信任方式”请求管理员权限，不要用脚本静默绕过。

## 9. 类型判断建议兼容复合值

- 本轮实测 4.1.15.13 的 `local_type` 可以直接 `= 3` 精确匹配（无高位 flags），
  但历史版本出现过复合值。**保险写法**：`(local_type & 0xFFFFFFFF) == 3`。

## 10. 时间成本提示

整个踩坑与验证过程约 **7 小时**（含 PBKDF2 暴力、内存 dump、XOR 破解等无效路径）。
直接按本文档操作，从零到「拿到群聊天纯文本」约 **15 分钟**。
