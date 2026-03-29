#!/usr/bin/env python3
"""
Test suite for pre-tool-use security hook.
Run: python3 test-hook.py
"""

import subprocess
import json
import sys
from pathlib import Path

def run_hook(command: str, working_dir: str = "/test/project"):
    """Run the hook with given command and return (exit_code, stderr)."""
    tool_input = json.dumps({
        "command": command,
        "working_directory": working_dir
    })
    
    result = subprocess.run(
        [sys.executable, "pre-tool-use.py"],
        input=tool_input,
        capture_output=True,
        text=True
    )
    
    return result.returncode, result.stderr

def test_rm_rf_root():
    """Test blocking rm -rf /"""
    exit_code, stderr = run_hook("rm -rf /")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "BLOCKED" in stderr, "Expected BLOCKED message"
    assert "rm -rf" in stderr.lower(), "Expected rm -rf in message"
    print("✅ rm -rf / blocked correctly")

def test_drop_table():
    """Test blocking DROP TABLE"""
    exit_code, stderr = run_hook("DROP TABLE users")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    assert "DROP TABLE" in stderr, "Expected DROP TABLE in message"
    print("✅ DROP TABLE blocked correctly")

def test_delete_without_where():
    """Test blocking DELETE without WHERE"""
    exit_code, stderr = run_hook("DELETE FROM users")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ DELETE without WHERE blocked correctly")

def test_git_force_push():
    """Test blocking git push --force"""
    exit_code, stderr = run_hook("git push --force origin main")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ git push --force blocked correctly")

def test_git_force_flag():
    """Test blocking git push -f"""
    exit_code, stderr = run_hook("git push -f")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ git push -f blocked correctly")

def test_safe_rm():
    """Test allowing safe rm commands"""
    exit_code, stderr = run_hook("rm -rf /tmp/test-files")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ Safe rm allowed correctly")

def test_safe_git_push():
    """Test allowing normal git push"""
    exit_code, stderr = run_hook("git push origin main")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ Safe git push allowed correctly")

def test_force_with_lease():
    """Test allowing git push --force-with-lease"""
    exit_code, stderr = run_hook("git push --force-with-lease origin main")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ git push --force-with-lease allowed correctly")

def test_dry_run():
    """Test allowing rm with --dry-run"""
    exit_code, stderr = run_hook("rm -rf / --dry-run")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ rm --dry-run allowed correctly")

def test_delete_with_where():
    """Test allowing DELETE with WHERE clause"""
    exit_code, stderr = run_hook("DELETE FROM users WHERE id = 1")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ DELETE with WHERE allowed correctly")

def test_mkfs():
    """Test blocking mkfs commands"""
    exit_code, stderr = run_hook("mkfs.ext4 /dev/sda1")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ mkfs blocked correctly")

def test_dd_disk_write():
    """Test blocking dd to disk"""
    exit_code, stderr = run_hook("dd if=/dev/zero of=/dev/sda bs=1M")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ dd to disk blocked correctly")

def test_safe_dd():
    """Test allowing safe dd to file"""
    exit_code, stderr = run_hook("dd if=/dev/zero of=/tmp/file.img bs=1M count=100")
    assert exit_code == 0, f"Expected exit code 0, got {exit_code}"
    print("✅ Safe dd to file allowed correctly")

def test_drop_database():
    """Test blocking DROP DATABASE"""
    exit_code, stderr = run_hook("DROP DATABASE production")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ DROP DATABASE blocked correctly")

def test_truncate_table():
    """Test blocking TRUNCATE TABLE"""
    exit_code, stderr = run_hook("TRUNCATE TABLE logs")
    assert exit_code == 1, f"Expected exit code 1, got {exit_code}"
    print("✅ TRUNCATE TABLE blocked correctly")

def test_log_file_created():
    """Test that blocked attempts are logged"""
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    
    # Run a blocked command
    run_hook("rm -rf /", "/test/project/path")
    
    # Check log file exists and contains our entry
    assert log_file.exists(), "Log file should exist"
    content = log_file.read_text()
    assert "rm -rf" in content, "Log should contain blocked command"
    assert "/test/project/path" in content, "Log should contain project path"
    assert "CRITICAL" in content, "Log should contain severity"
    print("✅ Log file created and populated correctly")

def run_all_tests():
    """Run all tests."""
    tests = [
        test_rm_rf_root,
        test_drop_table,
        test_delete_without_where,
        test_git_force_push,
        test_git_force_flag,
        test_safe_rm,
        test_safe_git_push,
        test_force_with_lease,
        test_dry_run,
        test_delete_with_where,
        test_mkfs,
        test_dd_disk_write,
        test_safe_dd,
        test_drop_database,
        test_truncate_table,
        test_log_file_created,
    ]
    
    print("=" * 60)
    print("Running Security Hook Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
