#!/usr/bin/env python3
"""
Test Suite for block-destructive-bash hook
Verifies all required patterns, non-interference, and logging.
"""

import subprocess
import json
import os
from pathlib import Path

HOOK_PATH = Path(__file__).parent / "block-destructive-bash.py"

def run_test(command: str) -> tuple[int, str]:
    payload = json.dumps({
        "tool_name": "bash",
        "tool_input": {"command": command},
        "cwd": "/test/project"
    })
    result = subprocess.run(
        ["python", str(HOOK_PATH)],
        input=payload,
        text=True,
        capture_output=True
    )
    return result.returncode, result.stderr

def main():
    print("Testing block-destructive-bash hook...")

    # Should be BLOCKED (exit code 1)
    blocked_cases = [
        "rm -rf /tmp/test",
        "rm -rf node_modules",
        "rm -r -f /var/data",
        "rm --recursive --force ./build",
        "DROP TABLE users;",
        "drop table orders",
        "git push origin main --force",
        "git push -f origin feature",
        "git push origin --force-with-lease",
        "TRUNCATE TABLE sessions;",
        "truncate analytics_events",
        "DELETE FROM users;",
        "DELETE FROM public.accounts",
    ]

    for cmd in blocked_cases:
        code, err = run_test(cmd)
        assert code == 1, f"Expected '{cmd}' to be BLOCKED, got exit code {code}"
        assert "BLOCKED BY HOOK" in err, f"Expected error message for '{cmd}'"
        print(f"  ✅ Correctly blocked: {cmd}")

    # Should be ALLOWED (exit code 0)
    allowed_cases = [
        "git status",
        "git push origin feature",
        "npm install",
        "pnpm build",
        "rm file.txt",
        "rm -i old_data.csv",
        "DELETE FROM users WHERE id = 42;",
        "delete from orders where status = 'cancelled';",
        "SELECT * FROM users;",
    ]

    for cmd in allowed_cases:
        code, err = run_test(cmd)
        assert code == 0, f"Expected '{cmd}' to be ALLOWED, got exit code {code} ({err})"
        print(f"  ✅ Correctly allowed: {cmd}")

    # Verify log file was written
    log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    assert log_file.exists(), "Log file ~/.claude/hooks/blocked.log was not created!"
    print(f"  ✅ Blocked log verified at {log_file}")

    print(f"\n🎉 All {len(blocked_cases) + len(allowed_cases)} test assertions PASSED successfully!")

if __name__ == "__main__":
    main()
