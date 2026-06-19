#!/usr/bin/env python3
"""Tests for block-destructive.py hook. Run: python3 test_hook.py"""

import json, subprocess, sys, os

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "block-destructive.py")

TESTS = [
    # Should be BLOCKED
    ("rm -rf /tmp/test", True, "rm -rf"),
    ("rm -fr /tmp/test", True, "rm -fr variant"),
    ("rm --force /tmp/test", True, "rm --force"),
    ("rm -rf /", True, "rm -rf root"),
    ("sudo rm -rf /var/log", True, "sudo rm"),
    ("DROP TABLE users;", True, "DROP TABLE"),
    ("DROP DATABASE production;", True, "DROP DATABASE"),
    ("TRUNCATE TABLE users;", True, "TRUNCATE"),
    ("DELETE FROM users;", True, "DELETE FROM without WHERE"),
    ("git push origin --force", True, "git push --force"),
    ("git push -f origin main", True, "git push -f"),
    ("chmod 777 /etc/passwd", True, "chmod 777"),
    ("mkfs.ext4 /dev/sda1", True, "mkfs"),
    ("dd if=/dev/zero of=/dev/sda", True, "dd to device"),

    # Should be ALLOWED
    ("rm /tmp/single_file.txt", False, "rm single file (no -rf)"),
    ("git push origin main", False, "normal git push"),
    ("DROP COLUMN is not SQL", False, "DROP not followed by TABLE"),
    ("SELECT * FROM users WHERE id = 1", False, "SELECT query"),
    ("DELETE FROM users WHERE id = 1;", False, "DELETE FROM with WHERE"),
    ("ls -la /tmp", False, "ls command"),
    ("pip install requests", False, "pip install"),
    ("python3 manage.py migrate", False, "Django migrate"),
    ("echo 'hello world'", False, "echo"),
    ("git commit -m 'fix bug'", False, "git commit"),
]


def run_hook(command: str) -> tuple:
    mock_input = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command}
    })
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=mock_input, capture_output=True, text=True, timeout=5
    )
    return result.returncode, result.stdout


def main():
    passed = failed = 0
    for command, should_block, description in TESTS:
        exit_code, stdout = run_hook(command)
        was_blocked = (exit_code == 2)
        ok = was_blocked == should_block
        passed += ok
        failed += not ok
        status = "PASS" if ok else "FAIL"
        expected = "BLOCKED" if should_block else "ALLOWED"
        actual = "BLOCKED" if was_blocked else "ALLOWED"
        print(f"  [{status}] {description}: expected={expected}, actual={actual}")
        if not ok and stdout:
            print(f"        Output: {stdout[:100]}")

    print(f"\nResults: {passed} passed, {failed} failed, {passed + failed} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
