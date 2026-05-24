#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)

blocked = [
    ("rm -rf /tmp/build", "rm"),
    ("rm -fr dist", "rm"),
    ("rm -r -f ./cache", "rm"),
    ("psql -c 'DROP TABLE users'", "DROP"),
    ("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE"),
    ("mysql -e 'DELETE FROM users'", "DELETE"),
    ("git push --force origin main", "force"),
    ("git push -f", "force"),
]
allowed = [
    "rm ./single-file.txt",
    "git push origin main",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
    "npm test",
]

for command, expected in blocked:
    reason = hook.classify(command)
    assert reason, f"expected blocked: {command}"

for command in allowed:
    assert hook.classify(command) is None, f"expected allowed: {command}"

payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/demo"}, "cwd": "/tmp/project"}
proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
out = json.loads(proc.stdout)
assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
assert out["hookSpecificOutput"]["permissionDecision"] == "deny"

safe_payload = {"tool_name": "Bash", "tool_input": {"command": "npm test"}, "cwd": "/tmp/project"}
proc = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(safe_payload), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
assert proc.stdout == ""

print("All destructive Bash hook tests passed.")
