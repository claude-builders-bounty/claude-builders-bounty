#!/usr/bin/env python3
"""Unit tests for block_destructive_bash.py."""

from __future__ import annotations

import unittest

from block_destructive_bash import blocked_reason


class BlockDestructiveBashTests(unittest.TestCase):
  def assert_blocked(self, command: str) -> None:
    self.assertIsNotNone(blocked_reason(command), command)

  def assert_allowed(self, command: str) -> None:
    self.assertIsNone(blocked_reason(command), command)

  def test_blocks_rm_recursive_force_variants(self) -> None:
    self.assert_blocked("rm -rf dist")
    self.assert_blocked("rm -fr dist")
    self.assert_blocked("rm -r -f dist")
    self.assert_blocked("rm -Rf dist")
    self.assert_blocked("sudo rm --recursive --force dist")

  def test_blocks_force_push(self) -> None:
    self.assert_blocked("git push --force origin main")
    self.assert_blocked("git push -f origin main")
    self.assert_blocked("git push -uf origin main")
    self.assert_blocked("git -C repo push --force origin main")
    self.assert_blocked("git push --force-with-lease origin main")

  def test_blocks_required_sql_patterns(self) -> None:
    self.assert_blocked("sqlite3 app.db 'DROP TABLE users'")
    self.assert_blocked("psql -c 'TRUNCATE audit_log'")
    self.assert_blocked("sqlite3 app.db 'DELETE FROM users'")

  def test_allows_delete_with_where(self) -> None:
    self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")
    self.assert_allowed("psql -c 'delete from sessions where expires_at < now()'")

  def test_allows_normal_commands(self) -> None:
    self.assert_allowed("npm test")
    self.assert_allowed("git status")
    self.assert_allowed("git push origin main")
    self.assert_allowed("rm dist.log")
    self.assert_allowed("rm -r dist")
    self.assert_allowed("rm --dir --force emptydir")
    self.assert_allowed("truncate -s 0 file.log")
    self.assert_allowed("echo hello")


if __name__ == "__main__":
  unittest.main()
