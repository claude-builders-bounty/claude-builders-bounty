#!/usr/bin/env python3
"""Tests for hooks/block_destructive_bash.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


BLOCKED = [
    "rm -rf /tmp/build",
    "rm -fr ./dist",
    "psql -c 'DROP TABLE users'",
    "git push --force origin main",
    "git push -f origin main",
    "mysql -e 'TRUNCATE TABLE sessions'",
    "psql -c 'DELETE FROM users'",
    "psql -c 'DELETE FROM users;'",
]

ALLOWED = [
    "npm test",
    "rm ./dist/file.txt",
    "git push origin main",
    "psql -c 'SELECT * FROM users'",
    "psql -c 'DELETE FROM users WHERE id = 1'",
]


def test_blocked_patterns() -> None:
    for command in BLOCKED:
        assert module.blocked_reason(command), command


def test_allowed_patterns() -> None:
    for command in ALLOWED:
        assert module.blocked_reason(command) is None, command


if __name__ == "__main__":
    test_blocked_patterns()
    test_allowed_patterns()
    print("All tests passed")
