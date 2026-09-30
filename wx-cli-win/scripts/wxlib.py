# -*- coding: utf-8 -*-
"""wxlib — 微信 4.x 本地解密库查询公共库

前置: 已用 key_tool.py 解密出 decrypted/ 目录(内含 message_*.db, contact/contact.db 等)
提供:
  connect_ro()      只读连接(自动绕开 WAL 锁)
  find_db_dir()     定位原始加密库目录
  find_dec_dir()    定位已解密目录
  locate_table()    按会话名找到 (db路径, 表名) 列表 —— 自动跨 message_N.db
  decode_raw()      zstd / utf-8 / utf-16le 自动解码
  load_nicks()      wxid -> 昵称/备注
  room_map()        群名片 -> wxid
  load_senders()    db内 rowid -> user_name (需自行合并同人别名)
  iter_msgs()       按时间窗迭代消息
  list_chats()      枚举所有会话及其活跃度

仅用于读取本人微信数据。
"""
from __future__ import annotations

import datetime
import hashlib
import os
import sqlite3

try:
    import zstandard
except ImportError:
    zstandard = None

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"

# 消息类型: 取 (local_type & 0xFFFFFFFF)，local_type 可能是 64 位复合值
TYPE_TEXT = 1
TYPE_IMAGE = 3
TYPE_VOICE = 34
TYPE_VIDEO = 43
TYPE_EMOTICON = 47
TYPE_APP = 49          # 链接/文件/小程序/合并转发/引用/拍一拍
TYPE_LOCATION = 48
TYPE_SYS = 10000       # 系统消息


def connect_ro(path: str):
    """只读连接 sqlite —— 绕开 WAL/shm 恢复导致的 "unable to open database file"

    解密产出的库常带残余 -wal/-shm，sqlite 默认要回滚/恢复日志(需在目录写),
    被拒时并不报权限错，而是直接报 unable to open database file，极易误判成路径写错。
    immutable=1 跳过 WAL 恢复；代价是读不到 wal 中未 checkpoint 的内容，
    对只读历史消息的场景无影响。先试普通连接，失败再退 immutable。
    """
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
        return conn
    except sqlite3.Error:
        pass
    uri = "file:" + path.replace("\\", "/") + "?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def find_db_dir() -> str | None:
    """自动定位微信 4.x 数据目录 **/db_storage"""
    roots = []
    for env in ("USERPROFILE", "HOME"):
        v = os.environ.get(env)
        if v:
            roots.append(os.path.join(v, "Documents", "xwechat_files"))
    for drv in "CDEFG":
        for base in (rf"{drv}:\xwechat_files",
                     rf"{drv}:\SynologyDrive\Office\xwechat_files",
                     rf"{drv}:\SynologyDrive\xwechat_files"):
            roots.append(base)
    for r in roots:
        if os.path.isdir(r):
            for sub in os.listdir(r):
                cand = os.path.join(r, sub, "db_storage")
                if os.path.isdir(cand):
                    return cand
    return None


def find_dec_dir(explicit: str | None = None) -> str | None:
    """定位已解密目录(含 contact/contact.db)"""
    if explicit:
        return explicit if os.path.isdir(explicit) else None
    cands = [
        os.environ.get("WX_DECRYPTED"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "decrypted"),
        os.path.expanduser(r"~\.workbuddy\wxkey_v4\decrypted"),
    ]
    for c in cands:
        if c and os.path.isdir(c) and os.path.isfile(os.path.join(c, "contact", "contact.db")):
            return c
    return None


def chat_id(username: str) -> str:
    """会话名 -> 消息表名后缀"""
    return hashlib.md5(username.encode()).hexdigest()


def resolve_chat(dec_dir: str, name: str) -> list[tuple[str, str]]:
    """群名/昵称/备注/wxid -> 候选 username 列表

    返回 [(username, display_name)]
    """
    conn = connect_ro(os.path.join(dec_dir, "contact", "contact.db"))
    try:
        rows = conn.execute(
            "SELECT username, nick_name, remark FROM contact").fetchall()
    finally:
        conn.close()
    hits = []
    seen = set()
    for u, n, r in rows:
        display = r or n or u
        if u == name or (n and name == n) or (r and name == r):
            if u not in seen:
                seen.add(u)
                hits.append((u, display))
    if not hits:
        # 模糊
        for u, n, r in rows:
            display = r or n or u
            if name in (n or "") or name in (r or ""):
                if u not in seen:
                    seen.add(u)
                    hits.append((u, display))
    return hits


def locate_table(dec_dir: str, username: str) -> list[tuple[str, str]]:
    """返回 [(db_path, table_name)] —— 会话可能跨多个 message_N.db"""
    tbl = "Msg_" + chat_id(username)
    found = []
    mdir = os.path.join(dec_dir, "message")
    if not os.path.isdir(mdir):
        return found
    for fn in sorted(os.listdir(mdir)):
        if not fn.startswith("message") or not fn.endswith(".db"):
            continue
        if "fts" in fn or "resource" in fn:
            continue
        p = os.path.join(mdir, fn)
        try:
            conn = connect_ro(p)
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (tbl,)).fetchone()
            conn.close()
        except sqlite3.Error:
            continue
        if row:
            found.append((p, tbl))
    return found


def load_nicks(dec_dir: str) -> dict[str, str]:
    """wxid / 微信号 -> 显示名(备注优先)"""
    nicks: dict[str, str] = {}
    conn = connect_ro(os.path.join(dec_dir, "contact", "contact.db"))
    try:
        for u, n, r in conn.execute("SELECT username, nick_name, remark FROM contact"):
            nicks[u] = r or n or u
    finally:
        conn.close()
    return nicks


def room_map(dec_dir: str, room: str) -> dict[str, str]:
    """群名片 displayname -> wxid"""
    out: dict[str, str] = {}
    conn = connect_ro(os.path.join(dec_dir, "contact", "contact.db"))
    try:
        row = conn.execute(
            "SELECT ext_buffer FROM chat_room WHERE username=?", (room,)).fetchone()
    finally:
        conn.close()
    if not row or not row[0]:
        return out
    buf = row[0]
    # protobuf 结构: \n<len>\n<alias> \x12<len><displayname> "\x13<wxid>
    import re
    for m in re.finditer(rb"\x12([\x01-\x7f])([^\x12\"]{1,120})", buf):
        ln = m.group(1)[0]
        name = m.group(2)[:ln].decode("utf-8", "replace")
        tail = buf[m.end(): m.end() + 40]
        mw = re.match(rb"\"\x11|\"\x13|\"\x10", tail)
        if mw:
            wlen = tail[1]
            wxid = tail[2: 2 + wlen].decode("utf-8", "replace")
            if wxid:
                out[name] = wxid
    return out


def load_senders(db_path: str) -> dict[int, str]:
    """message_N.db 内 rowid -> user_name

    注意 Name2Id 的主键是 user_name，rowid 是隐式序号。
    同一自然人可能占多个 rowid(微信号一个、wxid 一个)，调用方需自行合并。
    """
    conn = connect_ro(db_path)
    try:
        return dict(conn.execute("SELECT rowid, user_name FROM Name2Id"))
    finally:
        conn.close()


def decode_raw(raw) -> str | None:
    """数据库字段 -> 字符串(zstd / utf-8 / utf-16le 自动识别)

    没装 zstandard 时压缩字段会静默返回 None —— 表现为"图片/文件一条都查不到"，
    务必先 `pip install zstandard`。
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        return raw
    if not isinstance(raw, (bytes, bytearray)):
        return None
    if raw[:4] == ZSTD_MAGIC:
        if zstandard is None:
            return None
        try:
            d = zstandard.ZstdDecompressor().decompress(
                raw, max_output_size=50 * 1024 * 1024)
        except Exception:
            try:
                d = zstandard.ZstdDecompressor().stream_reader(raw).read()
            except Exception:
                return None
        for enc in ("utf-8", "utf-16-le"):
            try:
                return d.decode(enc)
            except Exception:
                continue
        return None
    for enc in ("utf-8", "utf-16-le"):
        try:
            s = raw.decode(enc)
            if "\x00" not in s[:8]:
                return s
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def strip_sender(body: str) -> tuple[str | None, str]:
    """文本消息 'wxid:\n内容' -> (wxid, 内容)"""
    if ":\n" in body:
        head, _, rest = body.partition(":\n")
        head = head.strip()
        if head and len(head) < 80 and "\n" not in head and "@" not in head[:1]:
            return head, rest
    return None, body


def iter_msgs(dec_dir: str, username: str, since: int | None = None,
              until: int | None = None):
    """迭代某会话消息: yield (ts, sender_id, base_type, text, raw_bytes)

    自动跨 message_N.db, 按时间排序
    """
    locs = locate_table(dec_dir, username)
    rows = []
    for db, tbl in locs:
        conn = connect_ro(db)
        sql = (f"SELECT create_time, real_sender_id, local_type, "
               f"message_content, compress_content FROM {tbl}")
        conds, args = [], []
        if since:
            conds.append("create_time >= ?")
            args.append(since)
        if until:
            conds.append("create_time < ?")
            args.append(until)
        if conds:
            sql += " WHERE " + " AND ".join(conds)
        sql += " ORDER BY create_time, sort_seq"
        try:
            rows.extend(conn.execute(sql, args).fetchall())
        except sqlite3.Error:
            pass
        conn.close()
    rows.sort(key=lambda r: r[0])
    for ts, sid, ltype, content, comp in rows:
        if ltype is None:
            continue
        base = ltype & 0xFFFFFFFF if ltype > 0xFFFFFFFF else ltype
        text = decode_raw(content)
        if text is None:
            text = decode_raw(comp)
        yield ts, sid, base, text, content


def list_chats(dec_dir: str) -> list[tuple[str, str, int, int, int]]:
    """枚举所有会话: [(md5_stem, table, count, first_ts, last_ts)]"""
    mdir = os.path.join(dec_dir, "message")
    agg: dict[str, list] = {}
    for fn in sorted(os.listdir(mdir)):
        if not fn.endswith(".db") or "fts" in fn or "resource" in fn:
            continue
        p = os.path.join(mdir, fn)
        try:
            conn = connect_ro(p)
            names = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name LIKE 'Msg_%'").fetchall()]
        except sqlite3.Error:
            continue
        for t in names:
            try:
                c, mn, mx = conn.execute(
                    f"SELECT COUNT(*), MIN(create_time), MAX(create_time) "
                    f"FROM {t}").fetchone()
            except sqlite3.Error:
                continue
            k = t[4:]
            if k in agg:
                agg[k][0] += c
                agg[k][1] = min(agg[k][1], mn or 0)
                agg[k][2] = max(agg[k][2], mx or 0)
            else:
                agg[k] = [c, mn or 0, mx or 0]
        try:
            conn.close()
        except sqlite3.Error:
            pass
    return [(k, "Msg_" + k, v[0], v[1], v[2]) for k, v in
            sorted(agg.items(), key=lambda x: -x[1][0])]


def ts_str(ts: int, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).strftime(fmt)
    except Exception:
        return str(ts)


def days_ago(n: int) -> int:
    return int((datetime.datetime.now() - datetime.timedelta(days=n)).timestamp())
