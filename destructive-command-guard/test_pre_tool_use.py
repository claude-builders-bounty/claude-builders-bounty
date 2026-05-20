#!/usr/bin/env python3
"""
Test suite for destructive command guard hook.
Run: python3 test_pre_tool_use.py
"""

import json
import os
import subprocess
import sys

HOOK_SCRIPT = os.path.join(os.path.dirname(__file__), 'pre-tool-use.py')

PASS = 0
FAIL = 0


def run_hook(command, tool_name="Bash", project_path="/test/project"):
    """Run the hook with simulated PreToolUse input.
    Returns (exit_code, stdout, stderr)."""
    input_data = json.dumps({
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "project_path": project_path,
    })
    proc = subprocess.Popen(
        [sys.executable, HOOK_SCRIPT],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    out, err = proc.communicate(input=input_data.encode("utf-8"), timeout=5)
    return proc.returncode, out.decode("utf-8", errors="replace").strip(), err.decode("utf-8", errors="replace").strip()

def get_decision(stdout):
    """Parse hook decision JSON from stdout."""
    if not stdout:
        return None
    try:
        data = json.loads(stdout)
        return data.get("hookSpecificOutput", {})
    except json.JSONDecodeError:
        return None


def test(name, command, *, should_block, match_pattern=""):
    """Run a single test case."""
    global PASS, FAIL
    _, stdout, _ = run_hook(command)
    decision = get_decision(stdout)

    if should_block:
        is_blocked = decision is not None and decision.get("permissionDecision") == "deny"
        ok = is_blocked
        status = "BLOCKED" if is_blocked else "ALLOWED (expected BLOCKED)"
    else:
        is_allowed = decision is None or decision.get("permissionDecision") != "deny"
        ok = is_allowed
        status = "ALLOWED" if is_allowed else "BLOCKED (expected ALLOWED)"

    if ok:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} -> {status}")
        if should_block and match_pattern and decision:
            reason = decision.get("permissionDecisionReason", "")
            if match_pattern not in reason:
                print(f"         Expected pattern '{match_pattern}' not in: {reason}")
        if stdout:
            print(f"         stdout: {stdout[:200]}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# =====================================================================
# BLOCKED TESTS -- these should all be denied
# =====================================================================

section("rm -rf variants")
test("rm -rf /tmp", "rm -rf /tmp/build", should_block=True, match_pattern="rm -rf")
test("rm -rf with -r and -f", "rm -r -f /var/log", should_block=True)
test("rm -fr (reverse flags)", "rm -fr /tmp/cache", should_block=True)
test("rm --recursive --force", "rm --recursive --force /opt/old", should_block=True)
test("rm -rf / (root)", "rm -rf /", should_block=True, match_pattern="rm -rf /")
test("rm -rf --no-preserve-root /", "rm -rf --no-preserve-root /", should_block=True, match_pattern="rm -rf /")

section("Database destructive")
test("DROP TABLE", "DROP TABLE users;", should_block=True, match_pattern="DROP")
test("DROP DATABASE", "DROP DATABASE production;", should_block=True, match_pattern="DROP")
test("DROP SCHEMA", "DROP SCHEMA public CASCADE;", should_block=True, match_pattern="DROP")
test("TRUNCATE TABLE", "TRUNCATE TABLE logs;", should_block=True, match_pattern="TRUNCATE")
test("TRUNCATE bare", "TRUNCATE users;", should_block=True, match_pattern="TRUNCATE")
test("DELETE FROM no WHERE (end)", "DELETE FROM users;", should_block=True, match_pattern="DELETE")
test("DELETE FROM no WHERE (newline)", "DELETE FROM accounts\n", should_block=True, match_pattern="DELETE")

section("Git force push")
test("git push --force", "git push --force origin main", should_block=True, match_pattern="git push")
test("git push --force-with-lease", "git push --force-with-lease", should_block=True, match_pattern="git push")
test("git push -f", "git push -f origin master", should_block=True, match_pattern="git push")
test("git force to main", "git push origin main --force", should_block=True)

section("Permissions")
test("chmod 777", "chmod 777 /var/www/html", should_block=True, match_pattern="chmod 777")
test("chmod -R 777", "chmod -R 777 .", should_block=True, match_pattern="chmod 777")

section("Fork bombs")
test("fork bomb classic", ":(){ :|:& };:", should_block=True, match_pattern="fork bomb")
test("fork bomb variant", "() { :|:& };:", should_block=True)

section("Disk / device writes")
test("dd to /dev/sda", "dd if=/dev/zero of=/dev/sda bs=512 count=1", should_block=True, match_pattern="dd")
test("redirect to /dev/sda", "cat img > /dev/sda", should_block=True, match_pattern="block device")
test("mkfs", "mkfs.ext4 /dev/sdb1", should_block=True, match_pattern="mkfs")

section("Windows destructive")
test("format C:", "format C: /FS:NTFS", should_block=True, match_pattern="format")
test("del /f /s", "del /f /s /q C:\\temp\\*", should_block=True, match_pattern="del /f")
test("rmdir /s", "rmdir /s /q C:\\old", should_block=True, match_pattern="rmdir /s")

# =====================================================================
# ALLOWED TESTS -- these should pass through
# =====================================================================

section("Safe commands (allowed)")
test("ls", "ls -la", should_block=False)
test("echo", "echo hello world", should_block=False)
test("cat", "cat file.txt", should_block=False)
test("mkdir", "mkdir -p /tmp/new", should_block=False)
test("grep", "grep -r 'pattern' .", should_block=False)
test("npm install", "npm install express", should_block=False)
test("pip install", "pip install requests", should_block=False)
test("git status", "git status", should_block=False)
test("git commit", "git commit -m 'fix'", should_block=False)
test("git push (no force)", "git push origin feature/branch", should_block=False)
test("curl", "curl https://example.com", should_block=False)
test("docker build", "docker build -t app .", should_block=False)
test("chmod 644", "chmod 644 file.txt", should_block=False)

section("Safe overlaps (build/CI cleanups)")
test("rm -rf node_modules", "rm -rf node_modules", should_block=False)
test("rm -rf __pycache__", "rm -rf __pycache__", should_block=False)
test("rm -rf .next", "rm -rf .next", should_block=False)
test("rm -rf dist", "rm -rf dist", should_block=False)
test("rm -rf build", "rm -rf build", should_block=False)
test("rm *.o", "rm -f *.o", should_block=False)

section("DELETE with WHERE (safe)")
test("DELETE with WHERE", "DELETE FROM users WHERE id = 1;", should_block=False)

section("Edge cases")
test("empty command", "", should_block=False)
test("whitespace only", "   ", should_block=False)
test("complex safe command", "find . -name '*.py' | xargs wc -l", should_block=False)
test("git push to feature branch", "git push origin feature/my-feature", should_block=False)

# =====================================================================
# SUMMARY
# =====================================================================

total = PASS + FAIL
print(f"\n{'='*60}")
print(f"  Results: {PASS}/{total} passed", end="")
if FAIL > 0:
    print(f", {FAIL} FAILED")
else:
    print(" -- All tests pass!")

print(f"{'='*60}\n")
sys.exit(0 if FAIL == 0 else 1)
