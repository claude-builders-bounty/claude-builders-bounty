#!/usr/bin/env python3
"""Tests for the destructive-guard pre-tool-use hook."""

import json
import subprocess
import sys
import os

HOOK = os.path.join(os.path.dirname(__file__), "hook.py")


def run_hook(tool_name: str, command: str) -> tuple[int, dict]:
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, HOOK],
        input=payload,
        capture_output=True,
        text=True,
    )
    try:
        output = json.loads(result.stdout) if result.stdout.strip() else {}
    except json.JSONDecodeError:
        output = {}
    return result.returncode, output


def test(desc: str, tool: str, cmd: str, expect_blocked: bool) -> bool:
    code, out = run_hook(tool, cmd)
    blocked = (code == 2)
    ok = blocked == expect_blocked
    status = "✅" if ok else "❌"
    print(f"  {status} {desc}")
    if not ok:
        print(f"     got code={code}, expected_blocked={expect_blocked}, out={out}")
    return ok


if __name__ == "__main__":
    print("Running destructive-guard hook tests...\n")
    results = []

    # --- Should BLOCK ---
    results.append(test("rm -rf /",             "Bash", "rm -rf /",              True))
    results.append(test("rm -fr /tmp/foo",       "Bash", "rm -fr /tmp/foo",       True))
    results.append(test("rm -Rf dir",            "Bash", "rm -Rf dir",            True))
    results.append(test("DROP TABLE users",      "Bash", "DROP TABLE users;",     True))
    results.append(test("drop table (lowercase)","Bash", "drop table orders;",    True))
    results.append(test("git push --force",      "Bash", "git push origin main --force", True))
    results.append(test("git push -f",           "Bash", "git push -f",           True))
    results.append(test("TRUNCATE table",        "Bash", "TRUNCATE TABLE logs;",  True))
    results.append(test("DELETE FROM no WHERE",  "Bash", "DELETE FROM sessions;", True))

    # --- Should ALLOW ---
    results.append(test("rm -r (no -f)",         "Bash", "rm -r ./build",         False))
    results.append(test("rm -f single file",     "Bash", "rm -f /tmp/foo.txt",    False))
    results.append(test("git push normal",       "Bash", "git push origin main",  False))
    results.append(test("DELETE FROM with WHERE","Bash", "DELETE FROM logs WHERE ts < '2024-01-01';", False))
    results.append(test("ls command",            "Bash", "ls -la",                False))
    results.append(test("non-Bash tool ignored", "Read", "rm -rf /",              False))

    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} tests passed")
    sys.exit(0 if passed == total else 1)
