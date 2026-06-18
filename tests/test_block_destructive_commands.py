#!/usr/bin/env python3
"""Tests for block_destructive_commands.py hook."""

import json
import subprocess
import sys
from pathlib import Path

HOOK_PATH = Path(__file__).parent.parent / "hooks" / "block_destructive_commands.py"


def run_hook(command, tool_name="Bash"):
    """Run the hook with a given command and return (exit_code, stdout)."""
    input_data = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp",
    }
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def test_should_block_rm_rf():
    """rm -rf should BLOCK."""
    code, stdout, _ = run_hook("rm -rf /tmp/test")
    assert code == 2, f"Expected exit code 2 (block), got {code}"
    assert "block" in stdout.lower(), f"Expected block in output: {stdout}"


def test_should_allow_ls():
    """ls should PASS."""
    code, _, _ = run_hook("ls -la")
    assert code == 0, f"Expected exit code 0 (allow), got {code}"


def test_should_block_drop_table():
    """DROP TABLE should BLOCK."""
    code, stdout, _ = run_hook("DROP TABLE users;")
    assert code == 2, f"Expected exit code 2, got {code}"
    assert "block" in stdout.lower()


def test_should_block_force_push():
    """git push --force should BLOCK."""
    code, stdout, _ = run_hook("git push --force origin main")
    assert code == 2
    assert "block" in stdout.lower()


def test_should_block_truncate():
    """TRUNCATE should BLOCK."""
    code, stdout, _ = run_hook("TRUNCATE TABLE logs;")
    assert code == 2
    assert "block" in stdout.lower()


def test_should_allow_normal_git_push():
    """git push should PASS."""
    code, _, _ = run_hook("git push origin main")
    assert code == 0


def test_should_allow_delete_with_where():
    """DELETE FROM with WHERE should PASS."""
    code, _, _ = run_hook("DELETE FROM users WHERE id = 5;")
    assert code == 0


def test_should_block_delete_without_where():
    """DELETE FROM without WHERE should BLOCK."""
    code, stdout, _ = run_hook("DELETE FROM users;")
    assert code == 2
    assert "block" in stdout.lower()


def test_should_allow_single_file_rm():
    """rm file should PASS."""
    code, _, _ = run_hook("rm file.txt")
    assert code == 0


def test_should_allow_non_bash_tool():
    """Non-bash tool should PASS."""
    code, _, _ = run_hook("rm -rf /", tool_name="Read")
    assert code == 0


if __name__ == "__main__":
    # Run tests manually if pytest not available
    tests = [
        test_should_block_rm_rf,
        test_should_allow_ls,
        test_should_block_drop_table,
        test_should_block_force_push,
        test_should_block_truncate,
        test_should_allow_normal_git_push,
        test_should_allow_delete_with_where,
        test_should_block_delete_without_where,
        test_should_allow_single_file_rm,
        test_should_allow_non_bash_tool,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{passed}/{passed+failed} tests passed")
    sys.exit(0 if failed == 0 else 1)
