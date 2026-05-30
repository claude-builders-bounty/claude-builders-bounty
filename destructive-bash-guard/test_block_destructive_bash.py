#!/usr/bin/env python3

from __future__ import annotations

import unittest

from block_destructive_bash import evaluate_command


class DestructiveBashGuardTest(unittest.TestCase):
  def test_allows_normal_commands(self) -> None:
    self.assertIsNone(evaluate_command("git status && python -m pytest"))

  def test_blocks_rm_rf(self) -> None:
    self.assertIn("rm -rf", evaluate_command("rm -rf build") or "")
    self.assertIn("rm -rf", evaluate_command("rm -fr build") or "")

  def test_blocks_drop_table(self) -> None:
    self.assertIn("DROP TABLE", evaluate_command("psql -c 'DROP TABLE users'") or "")

  def test_blocks_git_force_push(self) -> None:
    self.assertIn("force push", evaluate_command("git push origin main --force") or "")
    self.assertIn("force push", evaluate_command("git push -f origin main") or "")

  def test_blocks_truncate(self) -> None:
    self.assertIn("TRUNCATE", evaluate_command("mysql -e 'TRUNCATE audit_log'") or "")

  def test_blocks_delete_without_where(self) -> None:
    self.assertIn("DELETE FROM", evaluate_command("DELETE FROM sessions") or "")

  def test_allows_delete_with_where(self) -> None:
    self.assertIsNone(evaluate_command("DELETE FROM sessions WHERE expires_at < now()"))


if __name__ == "__main__":
  unittest.main()
