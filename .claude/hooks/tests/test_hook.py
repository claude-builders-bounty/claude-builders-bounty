#!/usr/bin/env python3
"""Tests for block-destructive-bash.py.

Runs the actual hook script as a subprocess with realistic PreToolUse JSON
payloads and asserts on exit code, the JSON deny decision, the stderr
message, and the blocked.log entries. Uses an isolated temp HOME so the real
~/.claude directory is never touched.

Run:  python3 tests/test_hook.py
"""

import json
import os
import subprocess
import sys
import tempfile

HOOK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "block-destructive-bash.py")

PASS = []
FAIL = []


def run_hook(command, tool_name="Bash", cwd="/tmp/proj"):
    payload = {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": cwd,
        "hook_event_name": "PreToolUse",
        "tool_name": tool_name,
        "tool_input": {"command": command, "description": "test"},
    }
    home = tempfile.mkdtemp(prefix="hooktest-home-")
    env = dict(os.environ, HOME=home)
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=json.dumps(payload).encode(),
        capture_output=True,
        env=env,
        timeout=15,
    )
    log_path = os.path.join(home, ".claude", "hooks", "blocked.log")
    log = ""
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as fh:
            log = fh.read()
    return proc.returncode, proc.stdout.decode(), proc.stderr.decode(), log


def check(name, fn):
    try:
        fn()
    except AssertionError as exc:
        FAIL.append((name, str(exc)))
        print("FAIL %s: %s" % (name, exc))
    else:
        PASS.append(name)
        print("ok   %s" % name)


def expect_blocked(command, **kw):
    rc, out, err, log = run_hook(command, **kw)
    assert rc == 2, "expected exit 2, got %d (cmd=%r)" % (rc, command)
    decision = json.loads(out or "{}")
    pd = decision.get("hookSpecificOutput", {}).get("permissionDecision")
    assert pd == "deny", "expected JSON deny decision, got %r" % (pd,)
    reason = decision["hookSpecificOutput"].get("permissionDecisionReason", "")
    assert len(reason) > 20, "deny reason should explain why"
    assert "BLOCKED" in err, "stderr should carry a human-readable message"
    assert "cwd=/tmp/proj" in log and command.split("&&")[-1].strip()[:20] in log, \
        "log must record cwd and the attempted command"
    assert log[:4].isdigit() and "T" in log.split("|")[0], \
        "log line must start with an ISO timestamp"


def expect_allowed(command, **kw):
    rc, out, err, log = run_hook(command, **kw)
    assert rc == 0, "expected exit 0, got %d (cmd=%r)" % (rc, command)
    assert out.strip() == "", "allowed commands must produce no stdout"
    assert log == "", "allowed commands must not be logged"


# --- must block -------------------------------------------------------------
check("block: rm -rf /", lambda: expect_blocked("rm -rf /"))
check("block: rm -rf ~", lambda: expect_blocked("rm -rf ~"))
check("block: rm -rf $HOME", lambda: expect_blocked("rm -rf $HOME"))
check("block: rm -rf .", lambda: expect_blocked("rm -rf ."))
check("block: rm -fr /usr", lambda: expect_blocked("rm -fr /usr"))
check("block: rm -r -f /tmp/x", lambda: expect_blocked("rm -r -f /tmp/x"))
check("block: sudo rm -rf /", lambda: expect_blocked("sudo rm -rf /"))
check("block: chained smuggling",
      lambda: expect_blocked("echo starting backup && rm -rf /"))
check("block: semicolon chain", lambda: expect_blocked("ls; rm -rf ~"))
check("block: pipe chain", lambda: expect_blocked("cat f | rm -rf /"))
check("block: rm -r / (no -f, dangerous target)",
      lambda: expect_blocked("rm -r /"))
check("block: rm -r /etc", lambda: expect_blocked("rm -r /etc"))
check("block: git push --force", lambda: expect_blocked("git push --force origin main"))
check("block: git push -f", lambda: expect_blocked("git push -f"))
check("block: DROP TABLE", lambda: expect_blocked("sqlite3 app.db 'DROP TABLE users'"))
check("block: TRUNCATE", lambda: expect_blocked('psql -c "TRUNCATE sessions"'))
check("block: DELETE without WHERE", lambda: expect_blocked("sqlite3 app.db 'DELETE FROM users'"))
check("block: mkfs", lambda: expect_blocked("mkfs.ext4 /dev/sda1"))
check("block: dd to device", lambda: expect_blocked("dd if=/dev/zero of=/dev/sda bs=1M"))
check("block: fork bomb", lambda: expect_blocked(":(){ :|:& };:"))
check("block: redirect to disk", lambda: expect_blocked("echo x > /dev/sda"))
check("block: sh -c smuggling", lambda: expect_blocked("sh -c 'rm -rf /'"))
check("block: $( ) substitution", lambda: expect_blocked("echo $(rm -rf /)"))
check("block: backtick substitution", lambda: expect_blocked("echo `rm -rf /`"))
check("block: env-prefix", lambda: expect_blocked("FOO=bar rm -rf /tmp"))
check("block: quoted -rf", lambda: expect_blocked('rm "-rf" /tmp/x'))
check("block: powershell recurse+force",
      lambda: expect_blocked("Remove-Item -Recurse -Force C:\\", tool_name="PowerShell"))

# --- must allow --------------------------------------------------------------
check("allow: ls", lambda: expect_allowed("ls -la /tmp"))
check("allow: git push (normal)", lambda: expect_allowed("git push origin main"))
check("allow: git push --force-with-lease",
      lambda: expect_allowed("git push --force-with-lease origin main"))
check("allow: DELETE with WHERE",
      lambda: expect_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'"))
check("allow: plain rm file", lambda: expect_allowed("rm README.md"))
check("allow: rm -r scoped subdir", lambda: expect_allowed("rm -r ./build"))
check("allow: npm test", lambda: expect_allowed("npm test"))
check("allow: grep mentioning rm -rf",
      lambda: expect_allowed("grep -r 'rm -rf' . --include='*.md'"))
check("allow: echo mentioning DROP TABLE",
      lambda: expect_allowed("echo 'do not DROP TABLE ever'"))
check("allow: git commit mentioning rm -rf",
      lambda: expect_allowed("git commit -m 'guard against rm -rf'"))
check("allow: mkdir && cp", lambda: expect_allowed("mkdir -p dist && cp -r src dist"))
check("allow: non-shell tool",
      lambda: expect_allowed("anything", tool_name="Read"))
check("allow: empty command", lambda: expect_allowed(""))
check("allow: psql select", lambda: expect_allowed("psql -c 'SELECT * FROM users'"))
check("allow: coreutils truncate", lambda: expect_allowed("truncate -s 0 bigfile.log"))

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
