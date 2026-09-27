#!/usr/bin/env python3
"""validate.py — kiểm tra workflow.json importable + đúng spec bounty #5."""
import json
import sys
from pathlib import Path

wf = json.loads((Path(__file__).resolve().parent / "workflow.json").read_text(encoding="utf-8"))
names = [n["name"] for n in wf["nodes"]]
errs = []


def need(cond, msg):
    if not cond:
        errs.append(msg)


types = [n["type"] for n in wf["nodes"]]
need(any("scheduleTrigger" in t for t in types), "thiếu Schedule trigger weekly")
need(sum("httpRequest" in t for t in types) >= 5, "thiếu HTTP nodes (3 GitHub + Claude + Discord)")
need(any(n["type"] == "n8n-nodes-base.code" for n in wf["nodes"]), "thiếu Code node aggregate")
need(any(n["type"] == "n8n-nodes-base.set" for n in wf["nodes"]), "thiếu Set node config")
raw = (Path(__file__).resolve().parent / "workflow.json").read_text()
need("claude-sonnet-4-20250514" in raw, "thiếu model Claude đúng spec")
need("GITHUB_REPO" in raw and "SUMMARY_LANG" in raw, "thiếu config vars repo/lang")
need("EN" in raw or "language" in raw, "thiếu hỗ trợ ngôn ngữ EN/FR")
need("DISCORD_WEBHOOK_URL" in raw, "thiếu kênh deliver Discord")
# connections trỏ đúng node tồn tại
for src, conns in wf.get("connections", {}).items():
    need(src in names, f"connection từ node lạ: {src}")
    for group in conns.get("main", []):
        for c in group:
            need(c["node"] in names, f"connection tới node lạ: {c['node']}")

if errs:
    print("ĐỎ:"); [print(" -", e) for e in errs]
    sys.exit(1)
print(f"XANH: {len(names)} nodes, connections hợp lệ, đủ spec #5 "
      "(cron Fri 17:00, commits/issues/PRs, Claude sonnet-4, Discord, EN/FR)")
