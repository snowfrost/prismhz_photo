# -*- coding: utf-8 -*-
"""v4 硬件断点密钥捕获器（修复 v3 三大致命伤）：
- LOG/OUT 全部放 C 盘 NTFS（避开 F 盘 exFAT 新文件 PermissionError 静默死亡）
- main() 加 __main__ 保护（v3 顶层裸调用 → import 即执行 → 附着后 Python 退出 → 微信陪葬）
- try/finally 保证异常时也 DebugActiveProcessStop（微信不再连坐）
- --launch 冷启动：杀微信 → 重启 → 等 Weixin.dll → 附着（登录前布好断点）
用法: python run_debugger_v4.py --launch   或   python run_debugger_v4.py (附着已运行微信)
"""
import ctypes
import ctypes.wintypes as wt
import json
import os
import struct
import subprocess
import sys
import time

WORKDIR = r"C:\Users\snowf\.workbuddy\wxkey_v4"
os.makedirs(WORKDIR, exist_ok=True)
OUT = os.path.join(WORKDIR, "captured_keys_v4.json")
LOG = os.path.join(WORKDIR, "debugger_log_v4.txt")

RVA_SET_CIPHER_KEY = 0x5FF520
MAX_RUN_SECONDS = 3600
IDLE_STOP = 120
MAX_KEYS = 40

WEIXIN_EXE = r"D:\Program Files\Tencent\Weixin\Weixin.exe"

log = open(LOG, "w", encoding="utf-8", buffering=1)
sys.stdout = log
sys.stderr = log

ntdll = ctypes.WinDLL("ntdll")
kernel32 = ctypes.WinDLL("kernel32")

CONTEXT_AMD64 = 0x100000
CTX_FLAGS = CONTEXT_AMD64 | 0x1 | 0x2 | 0x10
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
UNLOAD_DLL_DEBUG_EVENT = 7
OUTPUT_DEBUG_STRING_EVENT = 8
RIP_EVENT = 9
STATUS_SINGLE_STEP = 0x80000004
STATUS_BREAKPOINT = 0x80000003
TH32CS_SNAPTHREAD = 0x4
THREAD_SET_CONTEXT = 0x0010
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040


class CONTEXT(ctypes.Structure):
    _fields_ = [(f"p{i}Home", ctypes.c_uint64) for i in range(6)] + [
        ("ContextFlags", ctypes.c_uint32),
        ("MxCsr", ctypes.c_uint32),
        ("SegCs", ctypes.c_uint16), ("SegDs", ctypes.c_uint16), ("SegEs", ctypes.c_uint16),
        ("SegFs", ctypes.c_uint16), ("SegGs", ctypes.c_uint16), ("SegSs", ctypes.c_uint16),
        ("EFlags", ctypes.c_uint32),
        ("Dr0", ctypes.c_uint64), ("Dr1", ctypes.c_uint64), ("Dr2", ctypes.c_uint64),
        ("Dr3", ctypes.c_uint64), ("Dr6", ctypes.c_uint64), ("Dr7", ctypes.c_uint64),
        ("Rax", ctypes.c_uint64), ("Rcx", ctypes.c_uint64), ("Rdx", ctypes.c_uint64),
        ("Rbx", ctypes.c_uint64), ("Rsp", ctypes.c_uint64), ("Rbp", ctypes.c_uint64),
        ("Rsi", ctypes.c_uint64), ("Rdi", ctypes.c_uint64),
        ("R8", ctypes.c_uint64), ("R9", ctypes.c_uint64), ("R10", ctypes.c_uint64),
        ("R11", ctypes.c_uint64), ("R12", ctypes.c_uint64), ("R13", ctypes.c_uint64),
        ("R14", ctypes.c_uint64), ("R15", ctypes.c_uint64), ("Rip", ctypes.c_uint64),
        ("FltSave", ctypes.c_byte * 512),
        ("VectorRegister", ctypes.c_byte * 416),
        ("VectorControl", ctypes.c_uint64),
        ("DebugControl", ctypes.c_uint64),
        ("LastBranchToRip", ctypes.c_uint64),
        ("LastBranchFromRip", ctypes.c_uint64),
        ("LastExceptionToRip", ctypes.c_uint64),
        ("LastExceptionFromRip", ctypes.c_uint64),
    ]


class DEBUG_EVENT(ctypes.Structure):
    class _U(ctypes.Union):
        class _EXCEPTION(ctypes.Structure):
            _fields_ = [("ExceptionCode", ctypes.c_uint32), ("ExceptionFlags", ctypes.c_uint32),
                        ("ExceptionRecord", ctypes.c_uint64), ("ExceptionAddress", ctypes.c_void_p),
                        ("NumberParameters", ctypes.c_uint32), ("pad", ctypes.c_uint32),
                        ("Information", ctypes.c_uint64 * 15)]
        _fields_ = [("Exception", _EXCEPTION), ("raw", ctypes.c_byte * 160)]
    _fields_ = [("dwDebugEventCode", ctypes.c_uint32), ("dwProcessId", ctypes.c_uint32),
                ("dwThreadId", ctypes.c_uint32), ("u", _U)]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", ctypes.c_uint32), ("cntUsage", ctypes.c_uint32),
                ("th32ThreadID", ctypes.c_uint32), ("th32OwnerProcessID", ctypes.c_uint32),
                ("tpBasePri", ctypes.c_uint32), ("tpDeltaPri", ctypes.c_uint32), ("dwFlags", ctypes.c_uint32)]


class PBI(ctypes.Structure):
    _fields_ = [("ExitStatus", ctypes.c_void_p), ("PebBaseAddress", ctypes.c_void_p),
                ("AffinityMask", ctypes.c_void_p), ("BasePriority", ctypes.c_void_p),
                ("UniqueProcessId", ctypes.c_void_p), ("InheritedFrom", ctypes.c_void_p)]


def get_main_pid():
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Weixin.exe", "/FO", "CSV", "/NH"],
                       capture_output=True, text=True, errors="replace", encoding="mbcs")
    best = None
    for line in r.stdout.strip().split("\n"):
        if not line.strip():
            continue
        p = line.strip('"').split('","')
        if len(p) >= 5:
            try:
                pid = int(p[1])
                mem = int(p[4].replace(",", "").replace(" K", "").strip() or 0)
            except ValueError:
                continue
            if best is None or mem > best[1]:
                best = (pid, mem)
    return best


def get_weixin_base(hproc):
    psapi = ctypes.WinDLL("Psapi")
    arr = (ctypes.c_uint64 * 4096)()
    needed = wt.DWORD()
    if psapi.EnumProcessModulesEx(hproc, arr, ctypes.sizeof(arr), ctypes.byref(needed), 0x03):
        cnt = min(needed.value // 8, 4096)
        for i in range(cnt):
            name_buf = ctypes.create_unicode_buffer(512)
            psapi.GetModuleFileNameExW(hproc, ctypes.c_uint64(arr[i]), name_buf, 512)
            if name_buf.value.replace("/", "\\").lower().endswith("\\weixin.dll"):
                return arr[i]
    return None


def read_mem(hproc, addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)
    if kernel32.ReadProcessMemory(hproc, ctypes.c_void_p(addr), buf, size, ctypes.byref(n)):
        return buf.raw[: n.value]
    return None


def patch_peb(hproc):
    pbi = PBI()
    st = ntdll.NtQueryInformationProcess(ctypes.c_void_p(hproc), 0, ctypes.byref(pbi), ctypes.sizeof(pbi), None)
    if st != 0 or not pbi.PebBaseAddress:
        print(f"[!] NtQueryInformationProcess failed st={st}")
        return
    peb = pbi.PebBaseAddress
    w = ctypes.c_byte(0)
    kernel32.WriteProcessMemory(hproc, ctypes.c_void_p(peb + 2), ctypes.byref(w), 1, None)
    z = (ctypes.c_uint32 * 1)()
    kernel32.WriteProcessMemory(hproc, ctypes.c_void_p(peb + 0xBC), ctypes.byref(z), 4, None)
    print(f"[*] PEB patched at 0x{peb:x}")


def set_dr0(hthread, addr):
    ctx = CONTEXT()
    ctx.ContextFlags = CTX_FLAGS
    if not kernel32.GetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx)):
        return False
    ctx.Dr0 = addr
    ctx.Dr7 = (ctx.Dr7 & ~0xFFFF) | 0x1
    if not kernel32.SetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx)):
        return False
    return True


def clear_dr0(hthread):
    ctx = CONTEXT()
    ctx.ContextFlags = CTX_FLAGS
    if not kernel32.GetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx)):
        return
    ctx.Dr0 = 0
    ctx.Dr7 &= ~0x1
    kernel32.SetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx))


def set_rf(hthread):
    ctx = CONTEXT()
    ctx.ContextFlags = CTX_FLAGS
    if not kernel32.GetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx)):
        return
    ctx.EFlags |= 0x10000
    kernel32.SetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx))


def list_threads(pid):
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    te = THREADENTRY32()
    te.dwSize = ctypes.sizeof(te)
    tids = []
    ok = kernel32.Thread32First(snap, ctypes.byref(te))
    while ok:
        if te.th32OwnerProcessID == pid:
            tids.append(te.th32ThreadID)
        ok = kernel32.Thread32Next(snap, ctypes.byref(te))
    kernel32.CloseHandle(snap)
    return tids


def launch_mode():
    print("[*] LAUNCH MODE: killing all Weixin.exe ...", flush=True)
    r = subprocess.run(["taskkill", "/F", "/IM", "Weixin.exe", "/T"],
                       capture_output=True, text=True, errors="replace")
    print(f"    taskkill rc={r.returncode}", flush=True)
    time.sleep(3)
    print("[*] starting WeChat ...", flush=True)
    subprocess.Popen([WEIXIN_EXE], cwd=os.path.dirname(WEIXIN_EXE))
    for i in range(90):
        time.sleep(1)
        best = get_main_pid()
        if best:
            pid_check = best[0]
            h = kernel32.OpenProcess(0x0410, False, pid_check)
            if h:
                try:
                    base = get_weixin_base(h)
                    if base:
                        print(f"[*] main process ready pid={pid_check}", flush=True)
                        return pid_check
                finally:
                    kernel32.CloseHandle(h)
        print(f"    waiting Weixin.dll ({i})", flush=True)
    return None


def main():
    attached = False
    pid = None
    hproc = None
    keys = []
    try:
        if "--launch" in sys.argv:
            lpid = launch_mode()
            if not lpid:
                print("[!] launch failed")
                return
            pid, mem = lpid, 0
        else:
            best = get_main_pid()
            if not best:
                print("[!] Weixin.exe not found")
                return
            pid, mem = best
        print(f"[*] target pid={pid} mem={mem/1024:.0f}MB", flush=True)

        hproc = kernel32.OpenProcess(0x1FFFFF, False, pid)
        if not hproc:
            print(f"[!] OpenProcess failed err={kernel32.GetLastError()}")
            return

        base = get_weixin_base(hproc)
        if not base:
            print("[!] Weixin.dll not found in target")
            return
        bp_addr = base + RVA_SET_CIPHER_KEY
        print(f"[*] Weixin.dll base=0x{base:x}  setCipherKey=0x{bp_addr:x}", flush=True)

        patch_peb(hproc)

        if not kernel32.DebugActiveProcess(ctypes.c_uint32(pid)):
            print(f"[!] DebugActiveProcess failed err={kernel32.GetLastError()}")
            return
        attached = True
        print("[*] debugger attached", flush=True)

        for tid in list_threads(pid):
            ht = kernel32.OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_QUERY_INFORMATION, False, tid)
            if ht:
                if set_dr0(ht, bp_addr):
                    print(f"[*] DR0 set on thread {tid}")
                kernel32.CloseHandle(ht)

        seen = set()
        t0 = time.time()
        last_new = time.time()
        last_hb = 0
        ev_count = 0
        ev = DEBUG_EVENT()

        while time.time() - t0 < MAX_RUN_SECONDS:
            if not kernel32.WaitForDebugEvent(ctypes.byref(ev), 1000):
                if keys and time.time() - last_new > IDLE_STOP:
                    print("[*] idle timeout with keys, stopping")
                    break
                if time.time() - last_hb > 30:
                    last_hb = time.time()
                    print(f"[*] heartbeat t={time.time()-t0:.0f}s events={ev_count} keys={len(keys)} waiting-relogin", flush=True)
                continue
            ev_count += 1
            code, epid, etid = ev.dwDebugEventCode, ev.dwProcessId, ev.dwThreadId
            if code not in (6, 7, 8):
                print(f"[*] event code={code} tid={etid}", flush=True)
            status = DBG_CONTINUE

            if code == CREATE_THREAD_DEBUG_EVENT:
                ht = ctypes.c_void_p.from_buffer_copy(ev, 12).value
                if ht:
                    set_dr0(ht, bp_addr)

            elif code == EXCEPTION_DEBUG_EVENT:
                exc_code = ev.u.Exception.ExceptionCode
                exc_addr = ev.u.Exception.ExceptionAddress or 0
                if exc_code == STATUS_SINGLE_STEP and exc_addr == bp_addr:
                    print(f"[*] SINGLE_STEP at bp! tid={etid}", flush=True)
                    hthread = kernel32.OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_QUERY_INFORMATION, False, etid)
                    if hthread:
                        ctx = CONTEXT()
                        ctx.ContextFlags = CTX_FLAGS
                        if kernel32.GetThreadContext(ctypes.c_void_p(hthread), ctypes.byref(ctx)):
                            rdx = ctx.Rdx
                            buf_ptr_b = read_mem(hproc, rdx + 8, 8)
                            size_b = read_mem(hproc, rdx + 0x10, 8)
                            if buf_ptr_b and size_b:
                                buf_ptr = struct.unpack("<Q", buf_ptr_b)[0]
                                size = struct.unpack("<Q", size_b)[0]
                                if 0 < size <= 256:
                                    key = read_mem(hproc, buf_ptr, size)
                                    if key and key not in seen:
                                        seen.add(key)
                                        keys.append(key.hex())
                                        last_new = time.time()
                                        print(f"[KEY] tid={etid} size={size} key={key.hex()}", flush=True)
                        set_rf(hthread)
                        kernel32.CloseHandle(hthread)
                    status = DBG_CONTINUE
                    if len(seen) >= MAX_KEYS:
                        print("[*] max keys reached")
                        break
                elif exc_code == STATUS_SINGLE_STEP:
                    print(f"[*] stray SINGLE_STEP at 0x{exc_addr:x} (not bp)", flush=True)
                    status = DBG_CONTINUE
                elif exc_code == STATUS_BREAKPOINT:
                    status = DBG_CONTINUE
                else:
                    status = DBG_EXCEPTION_NOT_HANDLED

            elif code == EXIT_PROCESS_DEBUG_EVENT:
                print("[!] target process exiting!")
                kernel32.ContinueDebugEvent(epid, etid, DBG_CONTINUE)
                break

            kernel32.ContinueDebugEvent(epid, etid, status)

        print(f"[*] loop ended. unique keys: {len(keys)}", flush=True)
    except Exception as e:
        import traceback
        print(f"[!!!] EXCEPTION: {e}", flush=True)
        traceback.print_exc(file=sys.stdout)
        log.flush()
    finally:
        try:
            if attached and pid:
                for tid in list_threads(pid):
                    ht = kernel32.OpenThread(THREAD_GET_CONTEXT | THREAD_SET_CONTEXT | THREAD_QUERY_INFORMATION, False, tid)
                    if ht:
                        clear_dr0(ht)
                        kernel32.CloseHandle(ht)
                kernel32.DebugActiveProcessStop(pid)
                print(f"[*] detached from pid={pid}", flush=True)
        except Exception as e2:
            print(f"[!] detach error: {e2}", flush=True)
        try:
            with open(OUT, "w") as f:
                json.dump(keys, f, indent=2)
            print(f"[DONE] keys={len(keys)} -> {OUT}", flush=True)
        except Exception as e3:
            print(f"[!] write OUT error: {e3}", flush=True)


if __name__ == "__main__":
    main()
log.close()
