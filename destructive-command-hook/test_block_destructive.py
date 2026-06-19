#!/usr/bin/env python3
from block_destructive import find_block_reason


BLOCKED = [
    "rm -rf dist",
    "git push --force origin main",
    "git push -f",
    "psql -c 'DROP TABLE users'",
    "TRUNCATE audit_log",
    "DELETE FROM sessions;",
]

ALLOWED = [
    "rm -r dist",
    "git push origin main",
    "DELETE FROM sessions WHERE expires_at < now();",
    "python3 -m pytest",
]


for command in BLOCKED:
    assert find_block_reason(command), command
for command in ALLOWED:
    assert find_block_reason(command) is None, command

print("ok")
