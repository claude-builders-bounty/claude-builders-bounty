#!/usr/bin/env python3
"""
Test suite for dangerous_bash_guard.py
Runs without Claude Code — feeds synthetic hook JSON to stdin.
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK_SCRIPT = Path(__file__).parent / "dangerous_bash_guard.py"

# ── Test Cases ────────────────────────────────────────────────────

TESTS = [
    # (description, tool_name, command, should_block)
    # --- rm -rf ---
    ("rm -rf /", "Bash", "rm -rf /", True),
    ("rm -fr /tmp", "Bash", "rm -fr /tmp", True),
    ("rm -afr stuff", "Bash", "rm -afr stuff", True),
    ("rm file.txt (safe)", "Bash", "rm file.txt", False),
    ("rm -r dir (no -f)", "Bash", "rm -r dir", False),
    ("git rm -rf (not bash rm)", "Bash", "git rm -rf cached", True),

    # --- DROP ---
    ("DROP TABLE users", "Bash", 'psql -c "DROP TABLE users"', True),
    ("DROP DATABASE prod", "Bash", 'mysql -e "DROP DATABASE prod"', True),
    ("drop table (case insensitive)", "Bash", 'echo "drop table foo"', True),
    ("SELECT (safe)", "Bash", 'psql -c "SELECT * FROM users"', False),

    # --- git push --force ---
    ("git push --force", "Bash", "git push --force origin main", True),
    ("git push -f", "Bash", "git push -f origin main", True),
    ("git push --force-with-lease (safe)", "Bash", "git push --force-with-lease origin main", False),
    ("git push (safe)", "Bash", "git push origin main", False),

    # --- TRUNCATE ---
    ("TRUNCATE TABLE users", "Bash", 'psql -c "TRUNCATE TABLE users"', True),
    ("TRUNCATE users", "Bash", 'psql -c "TRUNCATE users"', True),
    ("truncate table (lowercase)", "Bash", 'mysql -e "truncate table logs"', True),

    # --- DELETE FROM without WHERE ---
    ("DELETE FROM without WHERE", "Bash", 'psql -c "DELETE FROM users;"', True),
    ("DELETE FROM with WHERE (safe)", "Bash", 'psql -c "DELETE FROM users WHERE id = 1;"', False),
    ("DELETE FROM no semicolon no WHERE (allowed)", "Bash", 'mysql -e "DELETE FROM sessions"', False),

    # --- Non-Bash tools (should always allow) ---
    ("Write tool (not Bash)", "Write", "rm -rf /", False),
    ("Edit tool (not Bash)", "Edit", "DROP TABLE users", False),

    # --- Edge cases ---
    ("empty command", "Bash", "", False),
    ("safe echo", "Bash", "echo hello world", False),
    ("safe npm install", "Bash", "npm install express", False),
    ("safe python script", "Bash", "python main.py", False),
    ("multiline with rm -rf", "Bash", "cd /tmp && rm -rf build && echo done", True),
]


def run_hook(tool_name: str, command: str) -> dict | None:
    """Run the hook script with synthetic input, return parsed JSON or None."""
    hook_input = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/test/project",
    })

    try:
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=hook_input,
            capture_output=True,
            text=True,
            timeout=10,
            env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": "/tmp/test-hooks"},
        )

        if result.stdout.strip():
            return json.loads(result.stdout.strip())
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"  ERROR: {e}")
        return None


def main():
    passed = 0
    failed = 0

    for desc, tool_name, command, should_block in TESTS:
        output = run_hook(tool_name, command)
        was_blocked = output is not None and output.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

        if was_blocked == should_block:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"  [{status}] {desc}")
        if was_blocked != should_block:
            print(f"       Expected: {'blocked' if should_block else 'allowed'}, Got: {'blocked' if was_blocked else 'allowed'}")
            if output:
                print(f"       Output: {json.dumps(output, indent=2)[:200]}")

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")

    # Cleanup test log
    log_path = Path("/tmp/test-hooks/.claude/hooks/blocked.log")
    if log_path.exists():
        log_entries = log_path.read_text(encoding="utf-8").strip().splitlines()
        print(f"\nBlocked log entries: {len(log_entries)}")
        # Show last few log entries
        lines = log_entries[-3:]
        for line in lines:
            entry = json.loads(line)
            print(f"  [{entry.get('timestamp', '?')}] {entry.get('command', '?')[:60]}...")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
