#!/usr/bin/env python3
"""Tests for pre-tool-use-hook.py"""
import json
import subprocess
import sys
import os

HOOK_PATH = os.path.join(os.path.dirname(__file__), "pre-tool-use-hook.py")

def run_hook(command: str) -> int:
    """Run the hook with a simulated bash command and return exit code."""
    input_data = json.dumps({
        "tool": "bash",
        "input": {"command": command}
    })
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=input_data,
        capture_output=True,
        text=True
    )
    return result.returncode

def test_safe_command_allowed():
    assert run_hook("ls -la") == 0
    assert run_hook("echo hello") == 0
    assert run_hook("git status") == 0
    assert run_hook("npm install") == 0

def test_rm_rf_blocked():
    assert run_hook("rm -rf /tmp/test") == 2
    assert run_hook("rm -fr /home/user") == 2

def test_drop_table_blocked():
    assert run_hook("psql -c 'DROP TABLE users;'") == 2
    assert run_hook("echo 'DROP TABLE schema.migrations' | psql") == 2

def test_truncate_blocked():
    assert run_hook("psql -c 'TRUNCATE TABLE logs;'") == 2
    assert run_hook("TRUNCATE sessions;") == 2

def test_delete_without_where_blocked():
    assert run_hook("psql -c 'DELETE FROM users;'") == 2

def test_delete_with_where_allowed():
    assert run_hook("psql -c 'DELETE FROM users WHERE id = 1;'") == 0

def test_git_push_force_blocked():
    assert run_hook("git push --force origin main") == 2
    assert run_hook("git push -f origin main") == 2
    assert run_hook("git push --force-with-lease origin main") == 2

def test_git_push_allowed():
    assert run_hook("git push origin main") == 0

def test_fork_bomb_blocked():
    assert run_hook(":(){ :|:& };:") == 2

def test_mkfs_blocked():
    assert run_hook("mkfs.ext4 /dev/sda1") == 2

if __name__ == "__main__":
    test_safe_command_allowed()
    test_rm_rf_blocked()
    test_drop_table_blocked()
    test_truncate_blocked()
    test_delete_without_where_blocked()
    test_delete_with_where_allowed()
    test_git_push_force_blocked()
    test_git_push_allowed()
    test_fork_bomb_blocked()
    test_mkfs_blocked()
    print("All tests passed!")
