# -*- coding: utf-8 -*-
"""media.py — 微信 4.x 本地图片缓存解密与导出

实测结论 (微信 4.1.15.13, 2026-10-01):
  * 磁盘缓存位置: <xwechat_files>/<账号>/msg/attach/<md5(会话username)>/<YYYY-MM>/Img/
  * 文件名就是消息 XML 里的 md5 (CDN md5), 可直接拼; hardlink 库仅作兜底
      表 image_hardlink_info_v4(md5, file_name, file_size, dir1, dir2)
      路径 = msg/attach/<dir2id[dir1]>/<dir2id[dir2]>/Img/<file_name>
      (dir1 是会话 hash 目录、dir2 是月份, 顺序写反 100% 找不到且不报错)
  * 三者关系:
      {md5}.dat      显示版      收到即下载
      {md5}_h.dat    高清原图    只有点开过大图才有
      {md5}_t.dat    小缩略图    始终有
  * 加解密 -> 见 v2dec.py (V0/V1/V2 三代, 密钥离线派生)
  * wxgf 转码 -> 见 wxam.py (调微信自带 VoipEngine.dll)

本模块保留早期的 XOR/hardlink 兜底逻辑; 新代码请优先用 v2dec + wxam。
"""

from __future__ import annotations

import os
import re
import sqlite3

try:
    from PIL import Image
except ImportError:
    Image = None

XOR_KEY = 0xA0
V2_MAGIC = b"\x07\x08\x56\x32"
JPEG, PNG, GIF, BMP = b"\xff\xd8\xff", b"\x89PNG", b"GIF8", b"BM"
_MAGIC_EXT = [(JPEG, ".jpg"), (PNG, ".png"), (GIF, ".gif"), (BMP, ".bmp")]


def sniff_ext(data: bytes) -> str | None:
    """按文件头判断扩展名"""
    for magic, ext in _MAGIC_EXT:
        if data[:len(magic)] == magic:
            return ext
    return None


def xor_decrypt(data: bytes, key: int = XOR_KEY) -> bytes:
    """逐字节 XOR —— 微信 4.x 缩略图缓存的老式加密"""
    return bytes(b ^ key for b in data)


def find_attach_root(xwechat_root: str | None = None) -> str | None:
    """定位 msg/attach 目录

    find_db_dir() 返回的是 <xwechat_files>/<user>/db_storage,
    而 attach 在 <xwechat_files>/<user>/msg/attach —— 需要往上一级再进 msg。
    """
    if xwechat_root and os.path.isdir(os.path.join(xwechat_root, "msg", "attach")):
        return os.path.join(xwechat_root, "msg", "attach")
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wxlib

    roots = []
    dbdir = wxlib.find_db_dir()
    if dbdir:
        roots.append(os.path.dirname(dbdir))       # <user>/
        roots.append(os.path.dirname(os.path.dirname(dbdir)))
    env = os.environ.get("WX_USER_DIR")
    if env:
        roots.append(env)
    for r in roots:
        cand = os.path.join(r, "msg", "attach")
        if os.path.isdir(cand):
            return cand
    return None


def load_index(dec_dir: str, only_existing: bool = True) -> dict[str, tuple[str, int, str]]:
    """读 hardlink 库: 图片 md5 -> (磁盘绝对路径, 字节大小, 后缀)

    only_existing=True 时过滤掉磁盘上已不存在的条目。
    hardlink 索引是历史累积的，约有 0.6% 的条目指向已被清理的缓存文件
    (实测 8822 条里 55 条失效)，不过滤会让调用方误以为"路径算错了"。

    返回空 dict 说明 hardlink.db 没解密，或本机不是 4.1.15+ 的目录结构。
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wxlib

    hl_path = os.path.join(dec_dir, "hardlink", "hardlink.db")
    attach = find_attach_root()
    if not (os.path.isfile(hl_path) and attach):
        return {}
    conn = wxlib.connect_ro(hl_path)
    try:
        dir2id = dict(conn.execute("SELECT rowid, username FROM dir2id"))
        out: dict[str, tuple[str, int, str]] = {}
        for md5, fn, size, d1, d2 in conn.execute(
                "SELECT md5, file_name, file_size, dir1, dir2 "
                "FROM image_hardlink_info_v4"):
            p = _build_path(attach, dir2id, fn, d1, d2)
            if only_existing and not os.path.isfile(p):
                continue
            out[md5] = (p, size, os.path.splitext(fn)[1])
        return out
    finally:
        conn.close()


def load_index_loose(dec_dir: str):
    """同 load_index, 额外返回 attach 根目录"""
    return load_index(dec_dir), find_attach_root()


def _build_path(attach: str, dir2id: dict, fn: str, d1, d2) -> str:
    """路径 = msg/attach/<dir2id[dir1]>/<dir2id[dir2]>/Img/<fn>

    实测: dir1 是会话 hash 目录, dir2 是 'YYYY-MM'。
    顺序写反会 100% 找不到文件(且不报错, 只表现为 missing)。
    """
    return os.path.join(attach, dir2id.get(d1, "_"), dir2id.get(d2, "_"),
                        "Img", fn)


def decrypt_file(path: str, prefer_xor: bool = True) -> tuple[bytes | None, str]:
    """解密一个缓存文件 -> (字节, 形态标签)

    形态标签: plain / xor / v2-unsolved / missing / unreadable
    """
    if not os.path.isfile(path):
        return None, "missing"
    try:
        raw = open(path, "rb").read()
    except OSError:
        return None, "unreadable"
    if sniff_ext(raw):
        return raw, "plain"
    if raw[:4] == V2_MAGIC:
        # V2 已攻克: 见 v2dec.decrypt()。这里保留兜底, 优先用 v2dec。
        try:
            from v2dec import decrypt as _v2, auto_key as _ak
        except ImportError:
            return None, "v2-need-v2dec"
        try:
            pt = _v2(raw, *_ak(os.environ.get("WX_USER_DIR", "."))[:2])
        except Exception:
            return None, "v2-no-key"
        if pt:
            return pt, "v2"
        return None, "v2-unsolved"
    if prefer_xor:
        pt = xor_decrypt(raw)
        if sniff_ext(pt):
            return pt, "xor"
    return None, "unreadable"


def export(dec_dir: str, out_dir: str, only_md5: set | None = None,
           max_n: int | None = None) -> dict:
    """批量解密导出图片

    only_md5: 只导这些图片 md5 (通常来自消息 XML 的 md5="...")
    返回统计 dict: {plain, xor, v2-unsolved, missing, exported}
    """
    index, _ = load_index_loose(dec_dir)
    os.makedirs(out_dir, exist_ok=True)
    stat = {"plain": 0, "xor": 0, "v2-unsolved": 0, "missing": 0,
            "unreadable": 0, "exported": 0, "indexed": len(index)}
    n = 0
    for md5, (path, _size, _ext) in index.items():
        if only_md5 is not None and md5 not in only_md5:
            continue
        if max_n is not None and n >= max_n:
            break
        data, how = decrypt_file(path)
        stat[how] = stat.get(how, 0) + 1
        if data is None:
            continue
        ext = sniff_ext(data) or ".bin"
        # 文件名带上时间线索: 用源文件名里的原始 hash
        src = os.path.basename(path)
        out = os.path.join(out_dir, os.path.splitext(src)[0] + ext)
        with open(out, "wb") as f:
            f.write(data)
        stat["exported"] += 1
        n += 1
    return stat


def group_image_md5(dec_dir: str, username: str, since: int | None = None) -> dict:
    """从消息 XML 提取 图片md5 -> (aeskey, 声明缩略图字节数, 时间戳)"""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wxlib

    out: dict[str, tuple] = {}
    for dbp, tbl in wxlib.locate_table(dec_dir, username):
        conn = wxlib.connect_ro(dbp)
        sql = ("SELECT create_time, message_content, compress_content FROM %s "
               "WHERE (local_type & 0xFFFFFFFF)=3" % tbl)
        args = []
        if since:
            sql = ("SELECT create_time, message_content, compress_content FROM %s "
                   "WHERE (local_type & 0xFFFFFFFF)=3 AND create_time>=?" % tbl)
            args.append(since)
        rows = conn.execute(sql, args).fetchall()
        conn.close()
        for ts, content, comp in rows:
            body = wxlib.decode_raw(content) or wxlib.decode_raw(comp)
            if not body:
                continue
            m = re.search(r'\bmd5="([a-f0-9]{32})"', body)
            k = re.search(r'\baeskey="([a-f0-9]{32})"', body)
            t = re.search(r'\bcdnthumblength="(\d+)"', body)
            if m and m.group(1) not in out:
                out[m.group(1)] = (k.group(1) if k else None,
                                   int(t.group(1)) if t else None, ts)
    return out
