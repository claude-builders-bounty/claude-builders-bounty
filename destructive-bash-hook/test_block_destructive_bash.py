#!/usr/bin/env python3
from block_destructive_bash import block_reason


blocked_cases = [
    ("rm -rf dist", "rm -rf style recursive forced deletion"),
    ("rm -fr ./tmp", "rm -rf style recursive forced deletion"),
    ("git push --force origin main", "forced git push"),
    ("git push -f origin main", "forced git push"),
    ("psql -c 'DROP TABLE users'", "DROP TABLE statement"),
    ("sqlite3 app.db 'TRUNCATE audit_log'", "TRUNCATE statement"),
    ("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM statement without a WHERE clause"),
]

allowed_cases = [
    "rm -r dist",
    "git push origin main",
    "sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < datetime()'",
    "npm test",
    "grep -R 'DROP TABLE' docs",
]


for command, expected_reason in blocked_cases:
    actual_reason = block_reason(command)
    assert actual_reason == expected_reason, (command, actual_reason)

for command in allowed_cases:
    assert block_reason(command) is None, command

print("All destructive bash hook checks passed.")
