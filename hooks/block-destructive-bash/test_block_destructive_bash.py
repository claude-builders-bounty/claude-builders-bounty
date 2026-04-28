#!/usr/bin/env python3
"""Self-test for block_destructive_bash.py — runs without any framework.

Usage:
  python3 test_block_destructive_bash.py
"""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "block_destructive_bash.py"


def run_hook(command: str | None, tool_name: str = "Bash") -> dict:
    payload = {"tool_name": tool_name}
    if command is not None:
        payload["tool_input"] = {"command": command}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert proc.returncode == 0, f"hook exited {proc.returncode}: {proc.stderr}"
    return json.loads(proc.stdout)


# (case_label, command, expected_decision)
CASES = [
    # --- BLOCKED ---
    ("rm -rf /tmp/foo", "rm -rf /tmp/foo", "block"),
    ("rm -fr /tmp/foo (flag order)", "rm -fr /tmp/foo", "block"),
    ("rm --recursive --force /tmp/foo", "rm --recursive --force /tmp/foo", "block"),
    ("DROP TABLE users", "psql -c 'DROP TABLE users'", "block"),
    ("drop table (lowercase)", "sqlite3 db.sqlite 'drop table users'", "block"),
    ("DROP DATABASE prod", "psql -c 'DROP DATABASE prod'", "block"),
    ("git push --force", "git push --force origin main", "block"),
    ("git push -f", "git push -f origin main", "block"),
    ("TRUNCATE users", "psql -c 'TRUNCATE users'", "block"),
    ("TRUNCATE TABLE users", "psql -c 'TRUNCATE TABLE users'", "block"),
    ("DELETE FROM users (no WHERE)", "psql -c 'DELETE FROM users'", "block"),
    ("delete from users (lowercase no WHERE)", "psql -c 'delete from users;'", "block"),
    # --- ALLOWED ---
    ("ls", "ls -la", "approve"),
    ("rm single file no flags", "rm /tmp/foo.txt", "approve"),
    ("rm -i interactive", "rm -i /tmp/foo.txt", "approve"),
    ("git push (no force)", "git push origin main", "approve"),
    ("git push --force-with-lease (safe)", "git push --force-with-lease origin main", "approve"),
    ("DELETE FROM with WHERE", "psql -c 'DELETE FROM users WHERE id = 5'", "approve"),
    ("delete from with where lowercase", "psql -c 'delete from users where id = 5'", "approve"),
    ("create table (allowed)", "sqlite3 db 'CREATE TABLE foo(id INT)'", "approve"),
    ("rm -r dir (no -f)", "rm -r build/", "approve"),
    ("file containing 'rm -rf' as text", "echo 'do not run rm -rf'", "block"),  # NOTE: deliberately blocked — we err on the side of safety
]


def main() -> int:
    failures: list[str] = []
    for label, command, expected in CASES:
        out = run_hook(command)
        actual = out.get("decision")
        if actual != expected:
            failures.append(
                f"  FAIL [{label}]\n"
                f"    command : {command!r}\n"
                f"    expected: {expected}\n"
                f"    actual  : {actual}\n"
                f"    output  : {out}\n"
            )
        else:
            print(f"  ok    [{label}] -> {actual}")

    # Edge: non-Bash tool always approved
    out = run_hook("rm -rf /", tool_name="Read")
    if out.get("decision") != "approve":
        failures.append(f"  FAIL non-Bash tool with rm -rf payload should approve: {out}")
    else:
        print("  ok    [non-Bash tool short-circuits to approve]")

    # Edge: empty command approved
    out = run_hook("")
    if out.get("decision") != "approve":
        failures.append(f"  FAIL empty command should approve: {out}")
    else:
        print("  ok    [empty command approves]")

    # Edge: malformed JSON approved (we send via run() with a fixed payload — simulate by pre-corrupting)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        timeout=5,
    )
    out = json.loads(proc.stdout)
    if out.get("decision") != "approve":
        failures.append(f"  FAIL malformed JSON should approve: {out}")
    else:
        print("  ok    [malformed event JSON approves]")

    print()
    if failures:
        print(f"{len(failures)} FAILURE(S):\n" + "".join(failures))
        return 1
    print("All cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
