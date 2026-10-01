#!/usr/bin/env python3
"""Unit tests for block_destructive.py"""
import sys, os, json, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hooks'))

from block_destructive import check_command

BLOCKED = [
    "rm -rf /tmp/test",
    "rm -fr /var/log",
    "rm --recursive --force .",
    "git push --force",
    "git push -f origin main",
    "git push --force-with-lease",
    "DROP TABLE users",
    "DROP DATABASE prod",
    "TRUNCATE sessions",
    "DELETE FROM logs",
    "DELETE FROM users WHERE 1=1",  # no real WHERE
    "chmod -R 777 /app",
]

ALLOWED = [
    "ls -la",
    "git push origin main",
    "git push origin feat/my-feature",
    "npm install",
    "DELETE FROM logs WHERE id > 1000 AND created_at < \'2020-01-01\'",
    "echo \'DROP TABLE is dangerous\'",
    "grep -r pattern .",
]

passed = 0
failed = 0

for cmd in BLOCKED:
    blocked, reason = check_command(cmd)
    if blocked:
        print(f"  ✅ BLOCKED: {cmd[:60]}")
        passed += 1
    else:
        print(f"  ❌ SHOULD HAVE BLOCKED: {cmd[:60]}")
        failed += 1

for cmd in ALLOWED:
    blocked, reason = check_command(cmd)
    if not blocked:
        print(f"  ✅ ALLOWED: {cmd[:60]}")
        passed += 1
    else:
        print(f"  ❌ SHOULD HAVE ALLOWED: {cmd[:60]} (reason: {reason})")
        failed += 1

print(f"\n{passed}/{passed+failed} tests passed")
sys.exit(0 if failed == 0 else 1)
