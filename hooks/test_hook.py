#!/usr/bin/env python3
"""Tests for the pre-tool-use security hook."""

import json
import os
import subprocess
import sys
import tempfile

HOOK_PATH = os.path.join(os.path.dirname(__file__), "pre-tool-use.py")


def run_hook(tool_name: str, command: str) -> tuple[int, str]:
    """Run the hook with the given tool call and return (exit_code, stdout)."""
    hook_input = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": "/tmp/test-project",
    })
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=hook_input,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def test_blocks_rm_rf():
    code, out = run_hook("Bash", "rm -rf /")
    assert code == 2, f"Expected exit 2, got {code}"
    data = json.loads(out)
    assert data["decision"] == "block"
    print("✅ Blocks rm -rf")


def test_blocks_rm_rf_variant():
    code, out = run_hook("Bash", "rm -fr /home/user")
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks rm -fr variant")


def test_blocks_drop_table():
    code, out = run_hook("Bash", 'psql -c "DROP TABLE users;"')
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks DROP TABLE")


def test_blocks_git_push_force():
    code, out = run_hook("Bash", "git push --force origin main")
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks git push --force")


def test_blocks_git_push_f():
    code, out = run_hook("Bash", "git push -f origin main")
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks git push -f")


def test_blocks_truncate():
    code, out = run_hook("Bash", 'mysql -e "TRUNCATE users;"')
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks TRUNCATE")


def test_blocks_delete_without_where():
    code, out = run_hook("Bash", 'psql -c "DELETE FROM users;"')
    assert code == 2, f"Expected exit 2, got {code}"
    print("✅ Blocks DELETE FROM without WHERE")


def test_allows_delete_with_where():
    code, _ = run_hook("Bash", 'psql -c "DELETE FROM users WHERE id = 5;"')
    assert code == 0, f"Expected exit 0, got {code}"
    print("✅ Allows DELETE FROM with WHERE")


def test_allows_normal_commands():
    safe_commands = [
        "ls -la",
        "cat file.txt",
        "git status",
        "git push origin main",
        "echo hello",
        "python3 script.py",
        "npm install",
        "rm file.txt",  # single file rm is fine
    ]
    for cmd in safe_commands:
        code, _ = run_hook("Bash", cmd)
        assert code == 0, f"Blocked safe command: {cmd}"
    print("✅ Allows all normal commands")


def test_ignores_non_bash_tools():
    code, _ = run_hook("Read", "rm -rf /")
    assert code == 0, "Should ignore non-bash tools"
    print("✅ Ignores non-bash tool calls")


def test_logging():
    """Verify blocked attempts are logged."""
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    # Remove existing log
    if os.path.exists(log_path):
        os.remove(log_path)
    
    run_hook("Bash", "rm -rf /important")
    
    assert os.path.exists(log_path), "Log file not created"
    with open(log_path) as f:
        content = f.read()
    assert "rm -rf /important" in content
    assert "BLOCKED" in content
    assert "/tmp/test-project" in content
    print("✅ Logs blocked attempts correctly")


if __name__ == "__main__":
    tests = [
        test_blocks_rm_rf,
        test_blocks_rm_rf_variant,
        test_blocks_drop_table,
        test_blocks_git_push_force,
        test_blocks_git_push_f,
        test_blocks_truncate,
        test_blocks_delete_without_where,
        test_allows_delete_with_where,
        test_allows_normal_commands,
        test_ignores_non_bash_tools,
        test_logging,
    ]
    
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{passed+failed} passed")
    if failed:
        sys.exit(1)
    print("All tests passed! 🎉")
