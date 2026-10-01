# -*- coding: utf-8 -*-
"""wxam.py —— wxgf (WxAM) 图片转码：调用微信自带的 VoipEngine.dll

背景
    V2 解出来的"显示版/高清原图"很多不是 JPEG，而是微信自研的 wxgf 格式
    （文件头 b"wxgf"）。它不是改头的 GIF，社区没有纯 Python 解码器，
    但微信自己带了：安装目录下的 VoipEngine.dll，导出函数 wxam_dec_wxam2pic_5。

用法
    from wxam import convert, available
    if available():
        jpg, ret = convert(wxgf_bytes, mode=0)      # 0=jpeg 1/2=png 3=gif

实测（微信 4.1.15.13 / Windows 11）
    * DLL 路径：<微信安装目录>\\<版本>\\VoipEngine.dll
      （本机 D://Program Files\\Tencent\\Weixin\\4.1.15.13\\VoipEngine.dll，约 20MB）
      ❗ 一定要用主程序安装目录里那个 20MB 版本。
        Roaming\\Tencent\\WeChat\\XPlugin\\...\\RadiumWMPF\\runtime\\VoipEngine.dll
        是小程序运行时用的 15MB 版本，签名/行为不一致，别用错。
    * 第 5 个参数 cfg **必须是有效指针**，传 NULL 直接 access violation。
      cfg 缓冲区至少 32 字节，首 4 字节 (int) 填输出格式。
    * 实测一组 71KB 的 wxgf：mode=0 -> JPEG 152KB；mode=1 -> PNG 1.9MB；mode=3 -> GIF 1.0MB。
      所以默认取 mode=0（jpeg），体积与画质最平衡。

并发注意
    Web 服务里必须做 DLL 单例 + 调用加锁：浏览器并发加载图片时重复
    LoadLibrary 会互相踩崩，表现为"图片全部 404"，而 curl 串行测试一切正常。
    本模块已内置 threading.Lock()。
"""
from __future__ import annotations

import ctypes
import os
import threading

_voip = None
_lock = threading.Lock()
CAP = 52 * 1024 * 1024
MODE_JPEG, MODE_PNG, MODE_PNG2, MODE_GIF = 0, 1, 2, 3


def find_dll(weixin_root: str | None = None) -> str | None:
    """定位主程序安装目录里的 VoipEngine.dll（选版本号最大的）"""
    cands: list[str] = []
    roots = [weixin_root] if weixin_root else [
        r"D:/Program Files/Tencent/Weixin", r"C:/Program Files/Tencent/Weixin",
        r"C:/Program Files (x86)/Tencent/Weixin",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Weixin"),
    ]
    for r in roots:
        if not (r and os.path.isdir(r)):
            continue
        try:
            for ver in os.listdir(r):
                p = os.path.join(r, ver, "VoipEngine.dll")
                if os.path.isfile(p):
                    cands.append(p)
        except OSError:
            pass
    if not cands:
        return None
    return sorted(cands, key=lambda p: os.path.basename(os.path.dirname(p)))[-1]


def available(dll: str | None = None) -> bool:
    return bool(dll or find_dll())


def _load(dll: str | None = None):
    global _voip
    if _voip is None:
        path = dll or find_dll()
        if not path:
            raise FileNotFoundError("找不到 VoipEngine.dll")
        d = os.path.dirname(path)
        try:
            os.add_dll_directory(d)
        except Exception:
            pass
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
        v = ctypes.WinDLL(path)
        fn = v.wxam_dec_wxam2pic_5
        fn.argtypes = [ctypes.c_int64, ctypes.c_int, ctypes.c_int64,
                       ctypes.POINTER(ctypes.c_int), ctypes.c_int64]
        fn.restype = ctypes.c_int64
        v._fn = fn
        _voip = v
    return _voip


def convert(data: bytes, mode: int = MODE_JPEG, dll: str | None = None):
    """wxgf 字节 -> (转码后字节 | None, ret)。mode: 0=jpeg 1/2=png 3=gif"""
    v = _load(dll)
    with _lock:
        cfg = ctypes.create_string_buffer(32)          # 不能传 NULL！
        ctypes.cast(cfg, ctypes.POINTER(ctypes.c_int))[0] = mode
        out = ctypes.create_string_buffer(CAP)
        out_sz = ctypes.c_int(CAP)
        inb = ctypes.create_string_buffer(data, len(data))
        ret = v._fn(ctypes.addressof(inb), len(data), ctypes.addressof(out),
                    ctypes.byref(out_sz), ctypes.addressof(cfg))
        if ret != 0:
            return None, ret
        n = out_sz.value
        if n <= 0 or n > CAP:
            return None, "badsize:%d" % n
        return out.raw[:n], 0
