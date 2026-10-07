# -*- coding: utf-8 -*-
"""棱镜Hz 女团面部资产出图：解析选角提示词文件，调 RunningHub G-2 经济版生成 4 张定妆照

使用前：export RUNNINGHUB_API_KEY=<你的key>（key 从环境变量读，不落盘）
换团时：改下方 SRC（选角 md 路径）与 TAGS（成员→文件名映射）
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PY = sys.executable  # 用当前 Python 运行 runninghub.py；直连方案见 SKILL.md
RH = os.environ.get("RUNNINGHUB_CLI", r"C:/Users/snowf/.workbuddy/skills/OpenClaw_RH_Skills/scripts/runninghub.py")
KEY = os.environ.get("RUNNINGHUB_API_KEY", "")
if not KEY:
    sys.exit("请先设置 RUNNINGHUB_API_KEY 环境变量")

SRC = os.environ.get("PRISM_CASTING_MD",
                     str(Path(__file__).resolve().parents[1] / "references" / "棱镜Hz-女团选角-面部资产提示词.md"))
OUT = Path(os.environ.get("PRISM_OUT_DIR", Path(__file__).resolve().parents[1] / "images"))
OUT.mkdir(parents=True, exist_ok=True)

text = Path(SRC).read_text(encoding="utf-8")
blocks = re.split(r"^## (Hz-\d+)[｜|]", text, flags=re.M)
members = []
for i in range(1, len(blocks) - 1, 2):
    mid, body = blocks[i], blocks[i + 1]
    m = re.search(r"###\s*面部资产提示词\s*\n(.*?)(?=\n---|\Z)", body, flags=re.S)
    if not m:
        print(f"[WARN] {mid} 未找到提示词")
        continue
    prompt = m.group(1).strip()
    prompt = re.sub(r"^#+\s*", "", prompt, flags=re.M).strip()
    members.append((mid, prompt))

print(f"解析到 {len(members)} 位成员: {[m[0] for m in members]}", flush=True)

TAGS = {"Hz-01": "Hz01_vocal", "Hz-02": "Hz02_dance", "Hz-03": "Hz03_visual", "Hz-04": "Hz04_rap"}


def gen(member):
    mid, prompt = member
    tag = TAGS.get(mid, mid.replace("-", ""))
    out = OUT / f"prism_{tag}.png"
    cmd = [PY, RH,
           "--endpoint", "rhart-image-g-2/text-to-image",
           "--prompt", prompt,
           "--param", "aspectRatio=3:4",
           "--param", "resolution=1k",
           "-o", str(out)]
    env = {**os.environ, "RUNNINGHUB_API_KEY": KEY}
    print(f"[START] {mid} -> {out.name} (prompt {len(prompt)} 字)", flush=True)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, env=env,
                           encoding="utf-8", errors="replace", timeout=1300)
        print(f"[DONE ] {mid} rc={r.returncode}", flush=True)
        tail = (r.stdout or "").strip().splitlines()
        for line in tail[-6:]:
            print("   ", line, flush=True)
        if r.stderr and r.returncode != 0:
            print("    STDERR:", r.stderr.strip()[-300:], flush=True)
    except subprocess.TimeoutExpired:
        print(f"[FAIL ] {mid} 超时", flush=True)
        return mid, 1, None
    return mid, r.returncode, out if out.exists() else None


results = []
with ThreadPoolExecutor(max_workers=2) as ex:
    for res in ex.map(gen, members):
        results.append(res)

print("\n===== 汇总 =====", flush=True)
ok = 0
for mid, rc, f in results:
    status = "OK" if rc == 0 and f else "FAIL"
    if status == "OK":
        ok += 1
    print(f"{mid}: {status} {f or ''}", flush=True)
print(f"成功 {ok}/{len(results)}")

# PNG 完整性校验：尾部 12 字节必须是 IEND 块
import struct
for mid, rc, f in results:
    if rc == 0 and f and Path(f).exists():
        data = Path(f).read_bytes()
        ok_png = data[-12:] == bytes.fromhex("0000000049454e44ae426082")
        print(f"{mid}: PNG校验 {'OK' if ok_png else 'BROKEN(截断?)'} size={len(data)}", flush=True)

sys.exit(0 if ok == len(results) else 1)
