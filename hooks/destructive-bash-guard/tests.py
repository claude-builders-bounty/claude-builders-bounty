#!/usr/bin/env python3
"""Lightweight tests for the destructive Bash guard hook."""

from __future__ import annotations

import importlib.util
from pathlib import Path


HOOK_PATH = Path(__file__).with_name("block_destructive_bash.py")
spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
assert spec and spec.loader
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


BLOCKED = [
    "rm -rf build",
    "rm -fr /tmp/demo",
    "psql -c 'DROP TABLE users'",
    "sqlite3 app.db 'TRUNCATE users'",
    "mysql -e 'DELETE FROM users'",
    "git push --force origin main",
    "git push -f",
    "git push --force-with-lease",
]

ALLOWED = [
    "rm -r build",
    "git push origin main",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
    "grep 'DROP TABLE' README.md",
    "npm test",
]


for command in BLOCKED:
    assert hook.find_block_reason(command), f"expected blocked: {command}"

for command in ALLOWED:
    assert not hook.find_block_reason(command), f"expected allowed: {command}"

print("destructive bash guard tests passed")
