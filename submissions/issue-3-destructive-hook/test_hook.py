#!/usr/bin/env python3
"""
Tests for the pre-tool-use destructive-command hook.

Run with: python3 test_hook.py
"""

import json
import subprocess
import sys
import tempfile
import os
from pathlib import Path

HOOK = Path(__file__).parent / "hook.py"


def run_hook(tool_name: str, command: str) -> tuple[int, str]:
    """Run the hook with a given tool call, return (exit_code, stdout)."""
    payload = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def test(description: str, tool: str, command: str, expect_blocked: bool) -> bool:
    code, out = run_hook(tool, command)
    blocked = code == 2
    ok = blocked == expect_blocked
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {description}")
    if not ok:
        print(f"         expected blocked={expect_blocked}, got code={code}")
        if out:
            print(f"         output: {out[:200]}")
    return ok


def main():
    print("=== hook.py tests ===\n")
    results = []

    # --- Should be BLOCKED ---
    results.append(test("rm -rf /tmp/x",            "Bash", "rm -rf /tmp/x",               True))
    results.append(test("rm -fr /tmp/x",            "Bash", "rm -fr /tmp/x",               True))
    results.append(test("sudo rm -rf /*",           "Bash", "sudo rm -rf /*",              True))
    results.append(test("DROP TABLE users",         "Bash", "DROP TABLE users;",           True))
    results.append(test("DROP DATABASE mydb",       "Bash", "DROP DATABASE mydb;",         True))
    results.append(test("DROP SCHEMA public",       "Bash", "DROP SCHEMA public CASCADE;", True))
    results.append(test("git push --force",         "Bash", "git push origin main --force",True))
    results.append(test("git push -f",              "Bash", "git push -f",                 True))
    results.append(test("TRUNCATE TABLE logs",      "Bash", "TRUNCATE TABLE logs;",        True))
    results.append(test("DELETE FROM no WHERE",     "Bash", "DELETE FROM orders;",         True))

    # --- Should be ALLOWED ---
    results.append(test("rm -i (interactive)",      "Bash", "rm -i file.txt",              False))
    results.append(test("rm single file",           "Bash", "rm file.txt",                 False))
    results.append(test("git push (normal)",        "Bash", "git push origin main",        False))
    results.append(test("git push --force-with-lease","Bash","git push --force-with-lease",False))
    results.append(test("DELETE with WHERE",        "Bash", "DELETE FROM users WHERE id=1;",False))
    results.append(test("SELECT statement",         "Bash", "SELECT * FROM users;",        False))
    results.append(test("CREATE TABLE",             "Bash", "CREATE TABLE foo (id int);",  False))
    results.append(test("Non-bash tool",            "Read", "rm -rf /tmp/x",               False))

    print()
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    if passed < total:
        print("SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("All tests passed!")


if __name__ == "__main__":
    main()
