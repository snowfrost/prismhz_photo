# -*- coding: utf-8 -*-
"""v2dec.py —— 微信 4.x V2/V1 .dat 图片解密（纯离线，不碰微信进程）

实测通过：微信 4.1.15.13 / Windows 11 / 账号 snowfrostsky，4728 张群图 100% 解出。

────────────────────────────────────────────────────────────
一、三代加密（按文件头 6 字节签名区分）
────────────────────────────────────────────────────────────
  V0  无签名                 整文件单字节 XOR
      key = 首字节 ^ 0xFF（JPEG 首字节恒为 FF）
  V1  \\x07\\x08V1\\x08\\x07       AES-128-ECB 头 + 单字节 XOR 尾
      key = b"cfcd208495d565ef"（社区已破解的固定 key）
  V2  \\x07\\x08V2\\x08\\x07       AES-128-ECB 头 + 单字节 XOR 尾
      key = 账号级，离线派生（见下）
V2 是 4.x 的绝对主流。实测朋友圈缓存 184/184 全是 V2。

────────────────────────────────────────────────────────────
二、V2 文件结构（逐字节）
────────────────────────────────────────────────────────────
  偏移   长度   内容
  0      6      魔数 \\x07\\x08V2\\x08\\x07
  6      4      aes_size (u32 LE)  —— 头部被 AES 加密的明文长度（实测恒 1024）
  10     4      xor_size (u32 LE)  —— 尾部被单字节 XOR 的明文长度
  14     1      标志字节（实测恒 0x01）
  15     N      AES-128-ECB 密文，N = (aes_size // 16 + 1) * 16
  15+N   M      中间明文（缩略图为 0，高清图为一大段）
  末尾   xor_size  单字节 XOR 的明文

  总长公式（实测精确成立）：
      file_size == 15 + (aes_size // 16 + 1) * 16 + raw_len + xor_size

  解密即三段拼接：
      plaintext = AES_ECB_dec(data[15 : 15+N])[:aes_size] + raw + xor(tail)

  ⚠ 两个坑：
    1. AES 密文长度是 (aes_size//16 + 1)*16，不是 aes_size 也不是向上取整——
       aes_size 恰为 16 的倍数时 PKCS7 会**多补一整块**，写错就整体错位。
    2. 15+N 处的 16 字节"分隔尾"不是老资料说的全局常量 56fbf4...，
       4.1.x 已变，按长度跳过即可，**不要硬编码**。

────────────────────────────────────────────────────────────
三、密钥离线派生（核心，无需扫内存）
────────────────────────────────────────────────────────────
  code  = MMKV 统计文件名里的数字：
          %APPDATA%\\Tencent\\xwechat\\net\\kvcomm\\key_<code>_*.statistic
          （旧版在 Tencent\\WeChat\\<n>\\kvcomm\\，还有 ilink\\kvcomm 一并扫）
  wxid  = 数据目录名去掉 _xxxx 后缀：snowfrostsky_da31 -> snowfrostsky
  aes_key = md5(f"{code}{wxid}").hexdigest()[:16].encode()   # 16 个 ASCII 字符
  xor_key = code & 0xFF

  ⚠ 两个魔鬼细节：
    1. aes_key 是 hexdigest 的前 16 个 **ASCII 字符**直接当 16 字节密钥，
       不是 hex 解码后的 8 字节——想当然解码会白白浪费半小时。
    2. wxid 必须去掉 _xxxx 后缀，否则派生出来的 key 解不开任何文件。

  校验：拿任一 V2 文件的 data[15:31] 做 ECB 解密，命中图像魔数
        （FFD8FF / 89504E47 / GIF8 / RIFF / wxgf）即为正确。一次单块运算，微秒级。

  ❗ 不要用 2 字节魔数（如 b"\\x89\\x50"）做判据：同一账号下所有缩略图的
     首密文块完全相同（ECB + 相同 JPEG 头），判据退化成 1/65536，
     扫 5 万个候选几乎必然产生假阳性。至少用 3 字节。
"""
from __future__ import annotations

import hashlib
import os
import re
import struct

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:  # pragma: no cover
    Cipher = None

V2_MAGIC_FULL = b"\x07\x08V2\x08\x07"
V1_MAGIC_FULL = b"\x07\x08V1\x08\x07"
V1_KEY = b"cfcd208495d565ef"

# 判据至少 3 字节，别用 2 字节（见上面模块 docstring 的教训）
MAGICS = [b"\xff\xd8\xff", b"\x89PNG", b"RIFF", b"wxgf", b"GIF8"]
MAGIC_EXT = [(b"\xff\xd8\xff", ".jpg"), (b"\x89PNG", ".png"), (b"GIF8", ".gif"),
             (b"RIFF", ".webp"), (b"wxgf", ".wxgf"), (b"BM", ".bmp")]


# ────────────────────────── 密钥派生 ──────────────────────────

def clean_wxid(wxid: str) -> str:
    """去掉账号后缀：snowfrostsky_da31 -> snowfrostsky；wxid_xxx_6409 -> wxid_xxx"""
    parts = wxid.split("_")
    if len(parts) >= 2 and re.fullmatch(r"[0-9a-f]{4}", parts[-1] or "x"):
        return "_".join(parts[:-1])
    if wxid.startswith("wxid_") and len(parts) >= 3:
        return "_".join(parts[:2])
    return wxid


def derive_key(code: int, wxid: str) -> tuple[bytes, int]:
    """-> (aes_key: 16 bytes, xor_key: int)"""
    wx = clean_wxid(wxid)
    return hashlib.md5(("%d%s" % (code, wx)).encode()).hexdigest()[:16].encode(), code & 0xFF


def find_codes(appdata: str | None = None) -> list[int]:
    """从 MMKV statistic 文件名里提取全部候选 code（去重升序）"""
    base = appdata or os.path.expandvars(r"%APPDATA%\Tencent")
    out: set[int] = set()
    if not os.path.isdir(base):
        return []
    for dp, _dn, fn in os.walk(base):
        if "kvcomm" not in dp.lower():
            continue
        for f in fn:
            if ".statistic" not in f.lower():
                continue
            m = re.search(r"key_(\d+)_", f) or re.search(r"(\d{4,})", f)
            if m:
                out.add(int(m.group(1)))
    return sorted(out)


def find_wxids(xwechat_root: str) -> list[str]:
    """数据根目录名（如 <...>/xwechat_files/snowfrostsky_da31）-> 候选 wxid"""
    name = os.path.basename(os.path.normpath(xwechat_root))
    return list(dict.fromkeys([name, clean_wxid(name)]))


def xor_key_from_tail(thumb_dir: str, n: int = 32) -> int | None:
    """兜底：从缩略图尾部反推 xor_key（JPEG 结尾恒为 FF D9）"""
    if not os.path.isdir(thumb_dir):
        return None
    vote: dict[int, int] = {}
    cnt = 0
    for f in sorted(os.listdir(thumb_dir)):
        if not re.fullmatch(r"[a-f0-9]{32}_t\.dat", f):
            continue
        raw = open(os.path.join(thumb_dir, f), "rb").read()
        if raw[:6] != V2_MAGIC_FULL or len(raw) < 2:
            continue
        k1, k2 = raw[-2] ^ 0xFF, raw[-1] ^ 0xD9
        if k1 == k2:
            vote[k1] = vote.get(k1, 0) + 1
        cnt += 1
        if cnt >= n:
            break
    return max(vote, key=vote.get) if vote else None


def auto_key(xwechat_root: str, sample: bytes | None = None):
    """自动找密钥：遍历 code × wxid，用真实 V2 文件做 oracle

    返回 (aes_key, xor_key, code, wxid)；找不到抛 RuntimeError。
    """
    if Cipher is None:
        raise RuntimeError("需要 cryptography: pip install cryptography")
    if sample is None:
        sample = _find_sample(xwechat_root)
    if sample is None:
        raise RuntimeError("找不到 V2 样本文件")
    c0 = sample[15:31]

    for code in find_codes():
        for wxid in find_wxids(xwechat_root):
            for w in dict.fromkeys([clean_wxid(wxid), wxid]):
                k = hashlib.md5(("%d%s" % (code, w)).encode()).hexdigest()[:16].encode()
                if _ok(k, c0):
                    return k, code & 0xFF, code, w
    raise RuntimeError("未能派生出密钥：检查 MMKV 路径与数据目录名")


def _ok(key: bytes, c0: bytes) -> bool:
    try:
        pt = Cipher(algorithms.AES(key), modes.ECB()).decryptor().update(c0)
    except Exception:
        return False
    return any(pt[:len(m)] == m for m in MAGICS)


def _find_sample(xwechat_root: str) -> bytes | None:
    attach = os.path.join(xwechat_root, "msg", "attach")
    if not os.path.isdir(attach):
        return None
    for dp, _dn, fn in os.walk(attach):
        for f in fn:
            if f.endswith("_t.dat"):
                p = os.path.join(dp, f)
                with open(p, "rb") as fh:
                    if fh.read(6) == V2_MAGIC_FULL:
                        return open(p, "rb").read()
    return None


# ────────────────────────── 解密 ──────────────────────────

def is_v2(data: bytes) -> bool:
    return data[:6] in (V2_MAGIC_FULL, V1_MAGIC_FULL)


def decrypt(data: bytes, aes_key: bytes, xor_key: int = 0xA0) -> bytes | None:
    """解一个 V0/V1/V2 .dat 文件；失败返回 None"""
    if data[:6] in (V2_MAGIC_FULL, V1_MAGIC_FULL):
        key = V1_KEY if data[:6] == V1_MAGIC_FULL else aes_key
        aes_size, xor_size = struct.unpack("<II", data[6:14])
        n = (aes_size // 16 + 1) * 16
        if len(data) < 15 + n:
            return None
        try:
            head = Cipher(algorithms.AES(key), modes.ECB()).decryptor().update(
                data[15:15 + n])[:aes_size]
        except Exception:
            return None
        rest = data[15 + n:]
        m = min(xor_size, len(rest))
        return head + rest[:len(rest) - m] + bytes(b ^ xor_key for b in rest[len(rest) - m:])
    # V0：整个文件单字节 XOR，key 由首字节反推
    if sniff(data):
        return data
    k = data[0] ^ 0xFF
    out = bytes(b ^ k for b in data)
    return out if sniff(out) else None


def sniff(data: bytes) -> str | None:
    """按文件头判断扩展名"""
    for m, e in MAGIC_EXT:
        if data[:len(m)] == m:
            return e
    return None
