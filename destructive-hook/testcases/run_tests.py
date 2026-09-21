#!/usr/bin/env python3
"""Run the hook against allowed/blocked test cases.

Also verifies that every blocked attempt is appended to the blocked log
with a timestamp, the reason, the project path, and the command.
The log path is redirected to a temp file via DESTRUCTIVE_HOOK_LOG.
"""
import json, os, subprocess, sys, tempfile, re
HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "..", "scripts", "destructive_hook.py")

cases = json.load(open(os.path.join(HERE, "cases.json")))

with tempfile.TemporaryDirectory() as tmp:
    log_file = os.path.join(tmp, "blocked.log")
    env = dict(os.environ, DESTRUCTIVE_HOOK_LOG=log_file)
    fail = 0
    for c in cases:
        payload = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": c["cmd"]},
            "cwd": "/home/user/demo-project",
        })
        r = subprocess.run([sys.executable, HOOK], input=payload,
                           capture_output=True, text=True, timeout=10,
                           env=env)
        expected = 2 if c["expected"] == "blocked" else 0
        ok = r.returncode == expected
        mark = "PASS" if ok else "FAIL"
        if not ok:
            fail += 1
        print(f"[{mark}] {c['expected']:>7}  {c['cmd'][:70]}", file=sys.stdout)
        if not ok:
            print(f"        exit={r.returncode} expected={expected}", file=sys.stdout)
            if r.stderr:
                print(f"        stderr: {r.stderr.strip()[:100]}", file=sys.stdout)

    # --- blocked.log format check ---
    blocked_count = sum(1 for c in cases if c["expected"] == "blocked")
    log_ok = True
    if not os.path.exists(log_file):
        print("[FAIL] log          blocked.log was not created")
        log_ok = False
    else:
        lines = [l for l in open(log_file, encoding="utf-8").read().splitlines() if l.strip()]
        if len(lines) != blocked_count:
            print(f"[FAIL] log          {len(lines)} log lines, expected {blocked_count}")
            log_ok = False
        line_re = re.compile(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\+\d{2}:\d{2})? "
            r"\| reason=\S.* \| project=/home/user/demo-project "
            r"\| command='.*'$"
        )
        for i, line in enumerate(lines):
            if not line_re.match(line):
                print(f"[FAIL] log          line {i + 1} bad format: {line[:100]}")
                log_ok = False
        if log_ok:
            print(f"[PASS] log          {blocked_count} lines, all contain timestamp+reason+project+command")
    if not log_ok:
        fail += 1

print()
total = len(cases) + 1
print(f"{total - fail}/{total} passed")
sys.exit(1 if fail else 0)
