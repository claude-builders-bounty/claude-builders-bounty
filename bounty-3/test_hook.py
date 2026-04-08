#!/usr/bin/env python3
"""Tests for pre_tool_use_hook.py"""

import json
import subprocess
import sys
import os
import tempfile

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), "pre_tool_use_hook.py")


def run_hook(tool_name: str, command: str) -> dict:
    """Run the hook with given input and return parsed JSON output."""
    data = json.dumps({"tool_name": tool_name, "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, HOOK_SCRIPT],
        input=data, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def test_allows_non_bash():
    assert run_hook("Read", "rm -rf /")["decision"] == "allow"
    assert run_hook("Write", "DROP TABLE users")["decision"] == "allow"
    print("✓ Allows non-Bash tools")


def test_allows_safe_commands():
    safe = ["ls -la", "cat file.txt", "git status", "pwd", "echo hello",
            "python script.py", "npm install", "make build", "grep pattern file",
            "git add -A", "git commit -m 'test'", "cd /tmp"]
    for cmd in safe:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "allow", f"Should allow: {cmd}"
    print(f"✓ Allows {len(safe)} safe commands")


def test_blocks_rm_rf():
    blocked = [
        "rm -rf /",
        "rm -rf /home/user",
        "rm -fr /var/log",
        "rm -Rf ./node_modules",
        "sudo rm -rf /",
    ]
    for cmd in blocked:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "block", f"Should block: {cmd}"
    print(f"✓ Blocks {len(blocked)} rm -rf variants")


def test_allows_safe_rm():
    safe = ["rm file.txt", "rm -i file.txt", "rm single_file.log", "rmdir empty_dir"]
    for cmd in safe:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "allow", f"Should allow: {cmd}"
    print(f"✓ Allows {len(safe)} safe rm commands")


def test_blocks_drop_table():
    blocked = [
        "DROP TABLE users;",
        "drop table users;",
        "Drop Table Users;",
        "DROP TABLE IF EXISTS users;",
        "  DROP  TABLE  schema.table  ;  ",
    ]
    for cmd in blocked:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "block", f"Should block: {cmd}"
    print(f"✓ Blocks {len(blocked)} DROP TABLE variants")


def test_blocks_git_push_force():
    blocked = [
        "git push --force",
        "git push --force origin main",
        "git push -f",
        "git push -f origin",
        "git push --force-with-lease",  # still force
    ]
    for cmd in blocked:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "block", f"Should block: {cmd}"
    print(f"✓ Blocks {len(blocked)} git push --force variants")


def test_allows_safe_git_push():
    safe = ["git push", "git push origin main", "git push -u origin feature"]
    for cmd in safe:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "allow", f"Should allow: {cmd}"
    print(f"✓ Allows {len(safe)} safe git push commands")


def test_blocks_truncate():
    blocked = [
        "TRUNCATE TABLE users;",
        "truncate table users;",
        "TRUNCATE users;",
        "truncate schema.table;",
    ]
    for cmd in blocked:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "block", f"Should block: {cmd}"
    print(f"✓ Blocks {len(blocked)} TRUNCATE variants")


def test_blocks_delete_without_where():
    blocked = [
        "DELETE FROM users;",
        "delete from users;",
        "DELETE FROM users",
        "DELETE FROM schema.table;",
    ]
    for cmd in blocked:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "block", f"Should block: {cmd}"
    print(f"✓ Blocks {len(blocked)} DELETE without WHERE")


def test_allows_delete_with_where():
    safe = [
        "DELETE FROM users WHERE id = 1;",
        "delete from users where active = false;",
        "DELETE FROM users\nWHERE created_at < '2020-01-01';",
    ]
    for cmd in safe:
        result = run_hook("Bash", cmd)
        assert result["decision"] == "allow", f"Should allow: {cmd}"
    print(f"✓ Allows {len(safe)} DELETE with WHERE")


def test_empty_command():
    assert run_hook("Bash", "")["decision"] == "allow"
    print("✓ Allows empty command")


def test_multiline_blocks():
    cmd = "echo safe\nrm -rf /tmp/thing"
    result = run_hook("Bash", cmd)
    assert result["decision"] == "block"
    print("✓ Blocks destructive command in multiline input")


if __name__ == "__main__":
    test_allows_non_bash()
    test_allows_safe_commands()
    test_blocks_rm_rf()
    test_allows_safe_rm()
    test_blocks_drop_table()
    test_blocks_git_push_force()
    test_allows_safe_git_push()
    test_blocks_truncate()
    test_blocks_delete_without_where()
    test_allows_delete_with_where()
    test_empty_command()
    test_multiline_blocks()
    print("\n🎉 All tests passed!")
