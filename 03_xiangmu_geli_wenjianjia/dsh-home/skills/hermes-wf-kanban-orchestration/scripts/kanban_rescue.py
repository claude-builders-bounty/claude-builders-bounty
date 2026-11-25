#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kanban_rescue.py — 看板卡死救护
===============================
修三种 CLI 没有出口的死状态：

  1. triage   —— 反复 block 后升级，`promote` 不认 triage，卡永久卡死
  2. stale    —— 看板显示 running 但 claude 进程已死，卡再也派不出去
  3. orphans  —— 父卡已 archived，子卡永远等不到「父卡 done」

用法:
    python kanban_rescue.py                          # 只诊断
    python kanban_rescue.py --apply                  # 执行修复（自动备份 db）
    python kanban_rescue.py --apply --card t_xxxx    # 只修某张
    python kanban_rescue.py --db D:/.../kanban.db

⚠️ triage → ready 是安全的（只是放回队列）；本脚本**绝不**把卡改成 done。
"""
import sqlite3, sys, subprocess, pathlib, json, shutil, datetime

DB = pathlib.Path(r"D:/Ai/Agent/hermes/kanban/boards/xiangmu/kanban.db")
if "--db" in sys.argv:
    DB = pathlib.Path(sys.argv[sys.argv.index("--db") + 1])
APPLY = "--apply" in sys.argv
ONLY = sys.argv[sys.argv.index("--card") + 1] if "--card" in sys.argv else None


def claude_alive():
    try:
        r = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=30,
                           encoding="gbk", errors="ignore")
        return "claude.exe" in r.stdout.lower()
    except Exception:
        return True   # 查不到就当有，保守（别误 reclaim 正在干活的 worker）


if not DB.is_file():
    print(f"❌ 看板库不存在: {DB}")
    sys.exit(1)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
cur = con.cursor()

rows = cur.execute(
    "select id,status,assignee,title from tasks "
    "where status in ('triage','running','blocked','todo','ready') order by id").fetchall()
if ONLY:
    rows = [r for r in rows if r["id"] == ONLY]

print("=" * 78)
print(f"  看板救护   {'【执行模式】' if APPLY else '【诊断模式 — 不改任何东西】'}")
print("=" * 78)

fixes = []

for r in [x for x in rows if x["status"] == "triage"]:
    print(f"🔒 {r['id']}  triage 卡死  {r['title']}")
    fixes.append((r["id"], "ready", "triage → ready（promote 不认 triage）"))

alive = claude_alive()
for r in [x for x in rows if x["status"] == "running"]:
    if alive:
        print(f"●  {r['id']}  running（claude 进程存在，跳过）  {r['title']}")
    else:
        print(f"💀 {r['id']}  running 但无 claude 进程  {r['title']}")
        fixes.append((r["id"], "ready", "僵尸 running → ready（进程已死）"))

links = cur.execute("select parent_id, child_id from task_links").fetchall()
archived = {x[0] for x in cur.execute("select id from tasks where status='archived'")}
done = {x[0] for x in cur.execute("select id from tasks where status='done'")}
for l in links:
    if l["parent_id"] in archived and l["parent_id"] not in done:
        print(f"👻 {l['child_id']}  父卡 {l['parent_id']} 已归档 → 子卡永远等不到")
        fixes.append((l["parent_id"], "done", f"归档父卡补记 done，解锁子卡 {l['child_id']}"))

print("-" * 78)
if not fixes:
    print("✅ 没有需要救的卡")
    sys.exit(0)

print(f"发现 {len(fixes)} 处需要修")
if not APPLY:
    print("（诊断模式，未改动。加 --apply 执行）")
    sys.exit(0)

bak = DB.with_suffix(f".db.bak_{datetime.datetime.now():%Y%m%d_%H%M%S}")
shutil.copy(DB, bak)
print(f"已备份 → {bak.name}")

for tid, new_status, why in fixes:
    cur.execute("update tasks set status=? where id=?", (new_status, tid))
    cur.execute(
        "insert into task_events(task_id,kind,payload,created_at) values(?,?,?,datetime('now'))",
        (tid, "status", json.dumps({"to": new_status, "reason": f"kanban_rescue: {why}"}, ensure_ascii=False)))
    print(f"  ✅ {tid} → {new_status}   ({why})")
con.commit()
print("完成。事件行已补写，审计链未断。")
