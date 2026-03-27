#!/usr/bin/env python3
"""Tests for the destructive command guard hook."""

import json
import os
import subprocess
import sys
import tempfile

HOOK_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "hooks", "block-destructive.py"
)


def run_hook(command, tool_name="Bash", project_path="/test/project"):
    """Run the hook with a simulated tool call. Returns (exit_code, stdout)."""
    payload = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": project_path,
    })
    # Use an isolated HOME so log writes don't pollute the real filesystem
    env = {**os.environ, "HOME": tempfile.mkdtemp()}
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.returncode, result.stdout


def test(name, command, should_block, tool_name="Bash"):
    """Run one test case. Returns True on pass."""
    exit_code, stdout = run_hook(command, tool_name=tool_name)
    blocked = exit_code != 0
    status = "PASS" if blocked == should_block else "FAIL"
    expected = "block" if should_block else "allow"
    actual = "blocked" if blocked else "allowed"
    print(f"  [{status}] {name}: expected {expected}, got {actual}")
    if status == "FAIL":
        print(f"         command:   {command}")
        print(f"         exit_code: {exit_code}")
        if stdout.strip():
            print(f"         stdout:    {stdout[:200]}")
    return status == "PASS"


def main():
    results = []
    print("Destructive Command Guard — Test Suite\n")

    # ── Commands that SHOULD be blocked ──────────────────────────────────
    print("Should BLOCK:")
    results.append(test("rm -rf path", "rm -rf /tmp/data", True))
    results.append(test("rm -fr path", "rm -fr ./build", True))
    results.append(test("rm -rfi path", "rm -rfi /var/log", True))
    results.append(test("sudo rm -rf", "sudo rm -rf /", True))
    results.append(test("DROP TABLE", "psql -c 'DROP TABLE users;'", True))
    results.append(test("drop table (lower)", "mysql -e 'drop table orders'", True))
    results.append(test("git push --force", "git push --force origin main", True))
    results.append(test("git push -f", "git push -f", True))
    results.append(test("git push origin -f", "git push origin main -f", True))
    results.append(test("TRUNCATE", "psql -c 'TRUNCATE TABLE sessions;'", True))
    results.append(test("truncate (lower)", "mysql -e 'truncate users'", True))
    results.append(test("DELETE FROM no WHERE", "psql -c 'DELETE FROM users;'", True))
    results.append(test("delete from (lower)", "mysql -e 'delete from logs'", True))

    print()

    # ── Commands that should be ALLOWED ──────────────────────────────────
    print("Should ALLOW:")
    results.append(test("rm single file", "rm file.txt", False))
    results.append(test("rm -r (no force)", "rm -r dir/", False))
    results.append(test("rm -f (no recursive)", "rm -f file.txt", False))
    results.append(test("git push (normal)", "git push origin main", False))
    results.append(test("git pull", "git pull --rebase", False))
    results.append(test("DELETE with WHERE", "psql -c 'DELETE FROM users WHERE id = 1;'", False))
    results.append(test("SELECT query", "psql -c 'SELECT * FROM users;'", False))
    results.append(test("ls command", "ls -la", False))
    results.append(test("echo command", "echo hello world", False))
    results.append(test("npm install", "npm install express", False))
    results.append(test("Non-Bash tool", "rm -rf /", False, tool_name="Read"))
    results.append(test("Non-Bash tool (Write)", "DROP TABLE x;", False, tool_name="Write"))

    print()

    # ── Log file verification ────────────────────────────────────────────
    print("Log verification:")
    tmp_home = tempfile.mkdtemp()
    env = {**os.environ, "HOME": tmp_home}
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": "rm -rf /important"},
        "project_path": "/my/project",
    })
    subprocess.run(
        [sys.executable, HOOK_PATH],
        input=payload, capture_output=True, text=True, env=env,
    )
    log_path = os.path.join(tmp_home, ".claude", "hooks", "blocked.log")
    if os.path.exists(log_path):
        with open(log_path) as f:
            content = f.read()
        has_timestamp = "BLOCKED" in content
        has_command = "rm -rf /important" in content
        has_project = "/my/project" in content
        log_ok = has_timestamp and has_command and has_project
        print(f"  [{'PASS' if log_ok else 'FAIL'}] Log contains timestamp, command, and project path")
        results.append(log_ok)
    else:
        print("  [FAIL] Log file was not created")
        results.append(False)

    print()

    # ── Summary ──────────────────────────────────────────────────────────
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
