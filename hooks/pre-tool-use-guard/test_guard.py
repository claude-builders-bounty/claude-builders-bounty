#!/usr/bin/env python3
"""
Tests for the pre-tool-use destructive command guard.

Run:  python3 -m pytest test_guard.py -v
  or: python3 test_guard.py
"""

import json
import subprocess
import sys
import os

GUARD_SCRIPT = os.path.join(os.path.dirname(__file__), "guard.py")


def run_hook(command: str) -> tuple[int, dict | None]:
    """
    Simulate a Claude Code PreToolUse hook call.

    Returns (exit_code, parsed_json_output_or_None).
    """
    hook_input = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/test-project",
    }

    result = subprocess.run(
        [sys.executable, GUARD_SCRIPT],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    output = None
    if result.stdout.strip():
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pass

    return result.returncode, output


def is_blocked(output: dict | None) -> bool:
    """Check if the hook output indicates a deny decision."""
    if output is None:
        return False
    decision = (
        output.get("hookSpecificOutput", {}).get("permissionDecision", "")
    )
    return decision == "deny"


# ── Tests: should be BLOCKED ──────────────────────────────────────────


def test_rm_rf():
    code, out = run_hook("rm -rf /")
    assert code == 0
    assert is_blocked(out), "rm -rf / should be blocked"


def test_rm_rf_directory():
    code, out = run_hook("rm -rf ./build")
    assert code == 0
    assert is_blocked(out), "rm -rf ./build should be blocked"


def test_rm_fr():
    """rm -fr is the same as rm -rf, just different flag order."""
    code, out = run_hook("rm -fr /tmp/data")
    assert code == 0
    assert is_blocked(out), "rm -fr should be blocked"


def test_drop_table():
    code, out = run_hook("psql -c 'DROP TABLE users;'")
    assert code == 0
    assert is_blocked(out), "DROP TABLE should be blocked"


def test_drop_table_case_insensitive():
    code, out = run_hook("mysql -e 'drop table accounts'")
    assert code == 0
    assert is_blocked(out), "drop table (lowercase) should be blocked"


def test_git_push_force():
    code, out = run_hook("git push --force origin main")
    assert code == 0
    assert is_blocked(out), "git push --force should be blocked"


def test_git_push_force_short():
    code, out = run_hook("git push -f origin main")
    assert code == 0
    assert is_blocked(out), "git push -f should be blocked"


def test_truncate():
    code, out = run_hook("psql -c 'TRUNCATE users;'")
    assert code == 0
    assert is_blocked(out), "TRUNCATE should be blocked"


def test_truncate_table():
    code, out = run_hook("mysql -e 'TRUNCATE TABLE orders;'")
    assert code == 0
    assert is_blocked(out), "TRUNCATE TABLE should be blocked"


def test_delete_from_no_where():
    code, out = run_hook("psql -c 'DELETE FROM users;'")
    assert code == 0
    assert is_blocked(out), "DELETE FROM without WHERE should be blocked"


def test_delete_from_no_where_no_semicolon():
    code, out = run_hook("mysql -e 'DELETE FROM orders'")
    assert code == 0
    assert is_blocked(out), "DELETE FROM without WHERE (no semicolon) should be blocked"


# ── Tests: should be ALLOWED ──────────────────────────────────────────


def test_safe_rm():
    code, out = run_hook("rm file.txt")
    assert code == 0
    assert not is_blocked(out), "rm file.txt should be allowed"


def test_safe_rm_r():
    """rm -r (without -f) is still risky but not matched by rm -rf pattern."""
    code, out = run_hook("rm -r ./old")
    assert code == 0
    assert not is_blocked(out), "rm -r (without -f) should be allowed"


def test_safe_git_push():
    code, out = run_hook("git push origin main")
    assert code == 0
    assert not is_blocked(out), "git push (no --force) should be allowed"


def test_safe_ls():
    code, out = run_hook("ls -la")
    assert code == 0
    assert not is_blocked(out), "ls -la should be allowed"


def test_safe_npm():
    code, out = run_hook("npm install express")
    assert code == 0
    assert not is_blocked(out), "npm install should be allowed"


def test_safe_delete_with_where():
    code, out = run_hook("psql -c 'DELETE FROM users WHERE id = 5;'")
    assert code == 0
    assert not is_blocked(out), "DELETE FROM with WHERE should be allowed"


def test_safe_python():
    code, out = run_hook("python3 app.py")
    assert code == 0
    assert not is_blocked(out), "python3 should be allowed"


def test_safe_cat():
    code, out = run_hook("cat /etc/hosts")
    assert code == 0
    assert not is_blocked(out), "cat should be allowed"


def test_empty_command():
    code, out = run_hook("")
    assert code == 0
    assert not is_blocked(out), "empty command should be allowed"


# ── Run tests directly ────────────────────────────────────────────────

if __name__ == "__main__":
    test_functions = [
        v for k, v in sorted(globals().items()) if k.startswith("test_")
    ]
    passed = 0
    failed = 0
    for fn in test_functions:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {fn.__name__}: {e}")
            failed += 1

    print(f"\n{'─' * 40}")
    print(f"  {passed} passed, {failed} failed, {passed + failed} total")
    if failed > 0:
        sys.exit(1)
