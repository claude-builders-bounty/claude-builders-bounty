#!/usr/bin/env python3
"""Test suite for block-destructive.py (37 hook cases + installer check).

Run:  python3 test_hook.py
Expects: 37/37 hook cases PASS and the installer one-liner from
hooks/README.md registers exactly one hook entry when run twice.
Exit 0 when everything passes.
"""
import json
import subprocess
import sys

HOOK = "./block-destructive.py"

# (command, should_block, label)
CASES = [
    ("rm -rf /tmp/foo", True, "rm -rf"),
    ("rm -fr /tmp/foo", True, "rm -fr"),
    ("rm -r -f /tmp/foo", True, "rm -r -f"),
    ("rm -f -r /tmp/foo", True, "rm -f -r"),
    ("sudo rm -rf /", True, "sudo rm -rf"),
    ("sudo -u alice rm -rf /tmp/x", True, "sudo -u rm -rf"),
    ("rm --recursive --force /tmp/x", True, "rm long flags"),
    ("rm --force --recursive /tmp/x", True, "rm long flags reversed"),
    ("ls /tmp; rm -rf /tmp/foo", True, "rm after semicolon"),
    ("echo hi && rm -rf /tmp/foo", True, "rm after &&"),
    ("DROP TABLE users;", True, "DROP TABLE"),
    ("drop table users", True, "drop table lowercase"),
    ('psql -c "DROP TABLE users;"', True, "DROP TABLE inside psql quotes"),
    ("git push --force origin main", True, "git push --force"),
    ("git push -f origin main", True, "git push -f"),
    ("git push origin main --force", True, "git push --force trailing"),
    ("TRUNCATE TABLE logs;", True, "TRUNCATE"),
    ("truncate sessions", True, "truncate lowercase"),
    ("DELETE FROM users;", True, "DELETE without WHERE"),
    ("delete from users", True, "delete lowercase no where"),
    ("DELETE FROM users WHERE id=1; DELETE FROM logs;", True, "second stmt no WHERE"),
    ("ls -la", False, "ls"),
    ("git status", False, "git status"),
    ("git push origin main", False, "git push normal"),
    ("git push --force-with-lease origin main", False, "force-with-lease (safe)"),
    ("rm file.txt", False, "rm single file"),
    ("rm -r /tmp/dir", False, "rm -r only"),
    ("rm -f file.txt", False, "rm -f only"),
    ("echo hello", False, "echo"),
    ('echo "rm -rf /"', False, "rm inside echo quotes"),
    ("DELETE FROM users WHERE id=1;", False, "DELETE with WHERE"),
    ("DELETE FROM users WHERE created_at < '2024-01-01';", False, "DELETE with WHERE date"),
    ("git push --force-with-lease", False, "force-with-lease bare"),
    ("npm install", False, "npm install"),
    ("psql -c 'SELECT * FROM users;'", False, "SELECT"),
    ("grep -rf pattern file", False, "grep -rf is not rm"),
    ("format /tmp/x", False, "word containing rm"),
]


def test_installer_idempotent():
    """Run the installer one-liner from hooks/README.md twice against a
    throwaway HOME and assert exactly one hook entry is registered."""
    import os
    import re
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "hooks", "README.md"),
              encoding="utf-8") as f:
        text = f.read()
    m = re.search(r'python3 -c "([^"]+)"', text)
    assert m, "installer one-liner not found in hooks/README.md"
    program = m.group(1)
    with tempfile.TemporaryDirectory() as home:
        os.makedirs(os.path.join(home, ".claude"))
        env = dict(os.environ, HOME=home)
        for _ in range(2):
            p = subprocess.run([sys.executable, "-c", program],
                               env=env, capture_output=True, text=True)
            assert p.returncode == 0, p.stderr
        with open(os.path.join(home, ".claude", "settings.json"),
                  encoding="utf-8") as f:
            settings = json.load(f)
    entries = settings["hooks"]["PreToolUse"]
    assert len(entries) == 1, entries
    assert entries[0]["hooks"][0]["command"] == (
        "python3 ~/.claude/hooks/block-destructive.py")
    print("PASS | installer idempotent (2 runs -> 1 entry)")
    return True


def main():
    fails = 0
    for cmd, should_block, label in CASES:
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": cmd}, "cwd": "/tmp/testproj"}
        p = subprocess.run([sys.executable, HOOK], input=json.dumps(event),
                           capture_output=True, text=True)
        blocked = False
        if p.stdout.strip():
            try:
                d = json.loads(p.stdout)
                blocked = d.get("hookSpecificOutput", {}).get(
                    "permissionDecision") == "deny"
            except json.JSONDecodeError:
                blocked = p.returncode != 0
        ok = (blocked == should_block) and p.returncode == 0
        if not ok:
            fails += 1
        print(("PASS" if ok else "FAIL"), "| expect",
              "BLOCK" if should_block else "ALLOW", "| got",
              "BLOCK" if blocked else "ALLOW", "|", label)
    print()
    print("FAILURES: %d / %d" % (fails, len(CASES)))
    try:
        test_installer_idempotent()
    except AssertionError as e:
        print("FAIL | installer idempotent:", e)
        fails += 1
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
