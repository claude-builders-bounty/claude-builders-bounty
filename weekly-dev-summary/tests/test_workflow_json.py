#!/usr/bin/env python3
"""test_workflow_json.py — assert acceptance #5 trên workflow.json (stdlib only)."""
import json
import sys
from pathlib import Path

wf = json.loads((Path(__file__).resolve().parent.parent / "workflow.json").read_text())
by_name = {n["name"]: n for n in wf["nodes"]}
ok = fail = 0


def chk(name, cond):
    global ok, fail
    if cond:
        ok += 1
        print(f"XANH {name}")
    else:
        fail += 1
        print(f"ĐỎ {name}")


cron = by_name.get("Weekly Cron (Fri 17:00)", {}).get("parameters", {}).get("rule", {}).get("interval", [{}])[0]
chk("cron Fri 17:00", cron.get("cronExpression") == "0 17 * * 5")
types = [n["type"] for n in wf["nodes"]]
chk("3 GitHub fetches", sum("httpRequest" in t for t in types) >= 5)
chk("model claude-sonnet-4-20250514", "claude-sonnet-4-20250514" in json.dumps(wf))
chk("config repo/lang/delivery", all(k in json.dumps(by_name.get("Config", {})) for k in ("repo", "language", "delivery")))
chk("EN/FR + model configurable", "SUMMARY_LANG" in json.dumps(wf) and "CLAUDE_MODEL" in json.dumps(wf))
chk("IF email-or-discord", by_name.get("IF Email or Discord", {}).get("type") == "n8n-nodes-base.if")
chk("Discord + Email deliver", "Deliver (Discord)" in by_name and "Deliver (Email)" in by_name)
chk("merged_at filter + caps", "merged_at" in json.dumps(wf) and "slice(0, 30)" in json.dumps(wf))
chk("Claude retry", by_name.get("Claude Summary", {}).get("retryOnFail") is True)
conns = wf.get("connections", {})
allnames = set(by_name)
chk("7+ connections hợp lệ", len(conns) >= 7 and all(
    s in allnames and all(c["node"] in allnames for g in v.get("main", []) for c in g)
    for s, v in conns.items()))
print(f"KQ: {ok} xanh / {fail} đỏ")
sys.exit(1 if fail else 0)
