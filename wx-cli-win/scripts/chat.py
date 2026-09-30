# -*- coding: utf-8 -*-
"""chat.py — 微信 4.x 本地聊天记录查询（已解密库）

用法:
    python chat.py list                              # 列出所有会话(按消息量排序)
    python chat.py list --days 30                    # 只看近 30 天有活动的
    python chat.py dump  "群名或备注" --days 30       # 导出可读聊天记录
    python chat.py dump  "张三" --days 7 --out a.txt
    python chat.py stats "群名" --days 30             # 统计: 类型/日活/发言人/发图榜
    python chat.py shares "群名" --days 30            # 导出链接与文件分享清单
    python chat.py pics  "群名" --days 30             # 导出图片索引
    python chat.py pics  "群名" --days 30 --export --out pics
                                                      # 并把图片从缓存解密导出

全局参数:
    --dec DIR      指定解密目录(默认自动探测)
    --days N       时间窗(默认全部)

依赖: Python 3.10+, 可选 zstandard(解压压缩字段)

仅用于处理本人微信数据。
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wxlib as W  # noqa: E402


def _nicks_with_alias(dec: str) -> dict[str, str]:
    """wxid/微信号 -> 显示名; 并为群成员名片补别名"""
    return W.load_nicks(dec)


def _md5_map(dec: str) -> dict[str, str]:
    """md5(username) -> username"""
    out = {}
    conn_path = os.path.join(dec, "contact", "contact.db")
    if not os.path.isfile(conn_path):
        return out
    import sqlite3
    conn = sqlite3.connect(conn_path)
    for (u,) in conn.execute("SELECT username FROM contact"):
        if u:
            out[W.chat_id(u)] = u
    conn.close()
    return out


def cmd_list(args):
    dec = args.dec
    rows = W.list_chats(dec)
    md5map = _md5_map(dec)
    nicks = _nicks_with_alias(dec)
    print(f"共 {len(rows)} 个会话\n")
    print(f"{'消息数':>8}  {'最后活跃':<17}  {'会话':<40} 表后缀")
    print("-" * 92)
    for key, tbl, cnt, mn, mx in rows[: args.top]:
        uname = md5map.get(key)
        disp = nicks.get(uname, uname or "?") if uname else "(未知会话)"
        if mx:
            last = W.ts_str(mx, "%Y-%m-%d %H:%M")
        else:
            last = "-"
        if args.days and mx and mx < W.days_ago(args.days):
            continue
        star = "群 " if (uname or "").endswith("@chatroom") else "   "
        print(f"{cnt:>8}  {last:<17}  {star}{disp[:38]:<40} {key[:12]}…")
    return 0


def _resolve(args) -> tuple[str, str]:
    hits = W.resolve_chat(args.dec, args.chat)
    if not hits:
        print(f"[!] 未找到会话: {args.chat}", file=sys.stderr)
        print("    试试: python chat.py list", file=sys.stderr)
        sys.exit(2)
    if len(hits) > 1 and not args.pick:
        print(f"[*] 匹配到 {len(hits)} 个会话，默认取第一个；用 --pick N 指定：")
        for i, (u, d) in enumerate(hits[:10]):
            print(f"    {i}: {d}  ({u})")
    idx = args.pick or 0
    return hits[min(idx, len(hits) - 1)]


def cmd_dump(args):
    dec = args.dec
    username, disp = _resolve(args)
    since = W.days_ago(args.days) if args.days else None
    locs = W.locate_table(dec, username)
    if not locs:
        print("[!] 该会话无消息表（可能已被清理）")
        return 1
    nicks = _nicks_with_alias(dec)
    senders = {}
    for db, _t in locs:
        senders.update(W.load_senders(db))

    lines = []
    n = 0
    for ts, sid, base, text, raw in W.iter_msgs(dec, username, since):
        n += 1
        dt = W.ts_str(ts, "%m-%d %H:%M")
        body = text or ""
        if base == W.TYPE_TEXT:
            who_id, content = W.strip_sender(body)
            who = nicks.get(who_id or senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: {content}")
        elif base == W.TYPE_IMAGE:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <图片>")
        elif base == W.TYPE_EMOTICON:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <表情>")
        elif base == W.TYPE_VIDEO:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <视频>")
        elif base == W.TYPE_VOICE:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <语音>")
        elif base == W.TYPE_SYS:
            lines.append(f"[{dt}] <系统> {body[:160]}")
        elif base == W.TYPE_LOCATION:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <位置>")
        elif base == W.TYPE_APP:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            title = re.search(r"<title>(.*?)</title>", body, re.S)
            lines.append(f"[{dt}] {who}: <链接/文件> "
                         + (html.unescape(title.group(1))[:120] if title else ""))
        else:
            who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
            lines.append(f"[{dt}] {who}: <type{base}> {body[:120]}")

    out = args.out or f"chat_{W.chat_id(username)[:8]}.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# 会话: {disp} ({username})\n")
        f.write(f"# 导出时间窗: {'近 ' + str(args.days) + ' 天' if args.days else '全部'}\n")
        f.write(f"# 消息数: {n}   生成于 {W.ts_str(int(__import__('time').time()))}\n\n")
        f.write("\n".join(lines))
    print(f"[*] 会话: {disp} ({username})")
    print(f"[*] 消息数: {n}  ->  {out}")
    return 0


def cmd_stats(args):
    dec = args.dec
    username, disp = _resolve(args)
    since = W.days_ago(args.days) if args.days else None
    nicks = _nicks_with_alias(dec)
    locs = W.locate_table(dec, username)
    senders = {}
    for db, _t in locs:
        senders.update(W.load_senders(db))

    types = Counter()
    days = Counter()
    talkers = Counter()
    pics = Counter()
    n = 0
    for ts, sid, base, text, raw in W.iter_msgs(dec, username, since):
        n += 1
        types[base] += 1
        days[W.ts_str(ts, "%Y-%m-%d")] += 1
        who = senders.get(sid, f"id{sid}")
        talkers[nicks.get(who, who)] += 1
        if base == W.TYPE_IMAGE:
            pics[nicks.get(who, who)] += 1

    print(f"=== {disp} ({username}) 统计 ===")
    print(f"消息总数: {n}\n")
    NAME = {1: "文本", 3: "图片", 34: "语音", 43: "视频", 47: "表情",
            49: "链接/文件", 48: "位置", 10000: "系统"}
    print("--- 类型分布 ---")
    for t, c in types.most_common(12):
        print(f"  {NAME.get(t, f'type{t}'):<10} {c}")
    print("\n--- 日活跃 TOP10 ---")
    for d, c in Counter(days).most_common(10):
        print(f"  {d}  {c}")
    print("\n--- 发言 TOP15 ---")
    for w, c in talkers.most_common(15):
        print(f"  {w:<20} {c}")
    if pics:
        print("\n--- 发图 TOP10 ---")
        for w, c in pics.most_common(10):
            print(f"  {w:<20} {c} 张")
    return 0


def cmd_shares(args):
    dec = args.dec
    username, disp = _resolve(args)
    since = W.days_ago(args.days) if args.days else None
    locs = W.locate_table(dec, username)
    nicks = _nicks_with_alias(dec)
    senders = {}
    for db, _t in locs:
        senders.update(W.load_senders(db))

    links, files = [], []
    for ts, sid, base, text, raw in W.iter_msgs(dec, username, since):
        if base != W.TYPE_APP or not text:
            continue
        body = html.unescape(html.unescape(text))
        mt = re.search(r"<appmsg[^>]*>.*?<type>(\d+)</type>", body, re.S)
        atype = int(mt.group(1)) if mt else 0
        title_r = re.search(r"<title>(.*?)</title>", body, re.S)
        title = re.sub(r"<[^>]+>", "", html.unescape(title_r.group(1))).strip() if title_r else ""
        who = nicks.get(senders.get(sid, ""), senders.get(sid, "?"))
        dt = W.ts_str(ts, "%Y-%m-%d %H:%M")
        if atype == 5:
            u = re.search(r"<url>(.*?)</url>", body, re.S)
            if u:
                links.append(f"[{dt}] {who} | {title} | {html.unescape(u.group(1))[:160]}")
        elif atype == 6:
            e = re.search(r"<fileext>(.*?)</fileext>", body, re.S)
            ln = re.search(r"<totallen>(\d+)</totallen>", body)
            size = int(ln.group(1)) // 1024 if ln else 0
            files.append(f"[{dt}] {who} | {title} ({size}KB .{e.group(1) if e else '?'})")

    print(f"=== {disp} 分享清单 ({'近 ' + str(args.days) + ' 天' if args.days else '全部'}) ===")
    print(f"\n--- 链接 {len(links)} ---")
    print("\n".join(links) or "  (无)")
    print(f"\n--- 文件 {len(files)} ---")
    print("\n".join(files) or "  (无)")
    return 0


def cmd_pics(args):
    """导出图片索引，并可选从本地缓存真正解密出图"""
    import media as M

    dec = args.dec
    username, disp = _resolve(args)
    since = W.days_ago(args.days) if args.days else None
    locs = W.locate_table(dec, username)
    nicks = _nicks_with_alias(dec)
    senders = {}
    for db, _t in locs:
        senders.update(W.load_senders(db))

    items = []
    for ts, sid, base, text, raw in W.iter_msgs(dec, username, since):
        if base != W.TYPE_IMAGE or not text:
            continue
        md5 = re.search(r'\bmd5="([a-f0-9]{32})"', text)
        tl = re.search(r'cdnthumblength="(\d+)"', text)
        items.append((ts, senders.get(sid, "?"),
                      md5.group(1) if md5 else "", int(tl.group(1)) if tl else 0))

    outdir = args.out or "pics_" + W.chat_id(username)[:8]
    os.makedirs(outdir, exist_ok=True)

    index = {}
    if getattr(args, "export", False):
        index, _ = M.load_index_loose(dec)

    n_hit = n_dec = n_v2 = n_plain = 0
    idx_path = os.path.join(outdir, "index.tsv")
    with open(idx_path, "w", encoding="utf-8") as f:
        f.write("time\twho\tmd5\tthumbsize\tlocal_file\tform\n")
        for ts, who, md5, tl in items:
            local, form = "", ""
            if md5 and md5 in index:
                p = index[md5][0]
                if os.path.isfile(p):
                    n_hit += 1
                    local = os.path.basename(p)
                    data, how = M.decrypt_file(p)
                    form = how
                    if how == "v2-unsolved":
                        n_v2 += 1
                    if data is not None:
                        ext = M.sniff_ext(data) or ".bin"
                        o = os.path.join(outdir, os.path.splitext(local)[0] + ext)
                        with open(o, "wb") as fo:
                            fo.write(data)
                        n_dec += 1
                        if how == "plain":
                            n_plain += 1
            f.write(f"{W.ts_str(ts)}\t{nicks.get(who, who)}\t{md5}\t{tl}\t"
                    f"{local}\t{form}\n")

    print(f"[*] 会话: {disp} ({username})")
    print(f"[*] 图片消息 {len(items)} 条 -> {idx_path}")
    if getattr(args, "export", False):
        print(f"[*] 缓存索引 {len(index)} 张；命中 {n_hit} 张，"
              f"成功导出 {n_dec} 张 -> {outdir}")
        if n_v2:
            print(f"[*] 其中 {n_v2} 张为 _h.dat 高清容器格式，暂不支持（缩略图通常已导出）")
        if n_plain:
            print(f"[*] 其中 {n_plain} 张本身为明文，直接复制")
        print("[*] 未命中 = 该图本地未缓存（多见于仅在手机端查看过的图）")
    else:
        print("[*] 加 --export 可从本机微信缓存真正解密出图片文件")
    return 0


def main():
    ap = argparse.ArgumentParser(description="微信本地聊天记录查询")
    ap.add_argument("--dec", help="解密目录(含 contact/contact.db)")
    ap.add_argument("cmd", choices=["list", "dump", "stats", "shares", "pics"])
    ap.add_argument("chat", nargs="?", help="群名/备注/wxid")
    ap.add_argument("--days", type=int, help="近 N 天")
    ap.add_argument("--out", help="输出文件/目录")
    ap.add_argument("--pick", type=int, help="同名多选时取第 N 个")
    ap.add_argument("--top", type=int, default=40, help="list 显示条数")
    ap.add_argument("--export", action="store_true",
                    help="pics: 从本机微信缓存真正解密导出图片")
    args = ap.parse_args()

    dec = W.find_dec_dir(args.dec)
    if not dec:
        print("[!] 找不到已解密目录。请先执行:\n"
              "    python key_tool.py set-passphrase <hex>\n"
              "    python key_tool.py extract --db-dir <db_storage> --output all_keys.json\n"
              "    python key_tool.py decrypt --db-dir <db_storage> --keys all_keys.json "
              "--output decrypted\n"
              "或直接 --dec 指定目录", file=sys.stderr)
        return 2
    args.dec = dec
    if args.cmd != "list" and not args.chat:
        print("[!] 需要提供会话名", file=sys.stderr)
        return 2

    return {"list": cmd_list, "dump": cmd_dump, "stats": cmd_stats,
            "shares": cmd_shares, "pics": cmd_pics}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
