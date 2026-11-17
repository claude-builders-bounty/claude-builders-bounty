#!/usr/bin/env python
"""cc-switch 模型链路探针（只读，不打印任何凭证）。

回答三个问题：
  ① 客户端要的模型 vs 网关实际发的模型，有没有被改写？
  ② 当前 provider 的五个模型档位各指向什么？
  ③ 各模型真实速度（只看 first_token_ms，duration_ms 常为 0）与成功率。

用法：
  python probe_ccswitch_model.py                 # 全部
  python probe_ccswitch_model.py --rewrites 30   # 只看最近 N 条改写记录

判定：rewrites 里出现 `req=A → used=B` 且 A 是你指定的模型，就是被代理改写了。
根因几乎总是：provider 的 ANTHROPIC_MODEL（主档位）不是 A。
"""
from __future__ import annotations

import argparse
import glob
import os
import sqlite3
import sys

CANDIDATES = [
    r"D:/Ai/claude code/cc-switch.db",
    os.path.expanduser("~/.cc-switch/cc-switch.db"),
    os.path.expanduser("~/AppData/Roaming/cc-switch/cc-switch.db"),
]
TIERS = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_FABLE_MODEL",
)


def find_db() -> str:
    for p in CANDIDATES:
        if os.path.exists(p):
            return p
    for pat in ("D:/*/*/cc-switch.db", os.path.expanduser("~/**/cc-switch.db")):
        hits = glob.glob(pat, recursive=True)
        if hits:
            return hits[0]
    sys.exit("✗ 找不到 cc-switch.db —— 先确认 cc-switch 装在哪")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rewrites", type=int, default=15, help="列多少条改写记录")
    a = ap.parse_args()

    db = find_db()
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    print(f"DB = {db}\n")

    # ① 五个档位
    print("① 当前 provider 的模型档位")
    for r in con.execute("SELECT name,settings_config FROM providers WHERE is_current=1"):
        print(f"   provider = {r['name']}")
        import json
        try:
            env = json.loads(r["settings_config"]).get("env", {})
        except Exception:
            print("   ✗ settings_config 解析失败")
            continue
        vals = {k: env.get(k) for k in TIERS}
        distinct = {v for v in vals.values() if v}
        for k in TIERS:
            print(f"     {k:32s} = {vals[k]}")
        if len(distinct) > 1:
            print(f"   ⚠️ 五个档位不一致（{len(distinct)} 个不同模型）"
                  f" → 子任务/降级调用会跑另一个模型")
        else:
            print("   ✓ 五个档位一致")
    print()

    # ② 改写记录
    print(f"② 最近 {a.rewrites} 条被代理改写的请求（request_model != model）")
    q = """SELECT request_model, model, status_code, created_at
           FROM proxy_request_logs WHERE request_model != model
           ORDER BY created_at DESC LIMIT ?"""
    rows = con.execute(q, (a.rewrites,)).fetchall()
    if not rows:
        print("   （无改写记录 —— 客户端请求的模型就是上游用的模型）")
    for r in rows:
        print(f"   req={str(r['request_model'])[:36]:38s} → used={str(r['model'])[:34]:36s} "
              f"HTTP={r['status_code']}")
    print()

    # ③ 速度与成功率
    print("③ 各模型真实表现（只看成功请求的首字延迟）")
    q2 = """SELECT model,
                   COUNT(*) n_all,
                   SUM(CASE WHEN status_code=200 THEN 1 ELSE 0 END) n_ok,
                   AVG(CASE WHEN status_code=200 THEN first_token_ms END) ttft
            FROM proxy_request_logs GROUP BY model ORDER BY n_all DESC LIMIT 12"""
    print(f"   {'模型':44s} {'总数':>5s} {'成功':>5s} {'成功率':>7s} {'首字ms':>9s}")
    for r in con.execute(q2):
        rate = (r["n_ok"] / r["n_all"] * 100) if r["n_all"] else 0
        print(f"   {str(r['model'])[:44]:44s} {r['n_all']:5d} {r['n_ok']:5d} "
              f"{rate:6.1f}% {(r['ttft'] or 0):9.0f}")
    print("\n   注：duration_ms 常为 0（未记录），拿它比速度会得出「一样快」的错结论。")

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
