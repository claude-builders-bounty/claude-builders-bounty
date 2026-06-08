#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #3 destructive-command hook."""

import importlib.util
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "pre-tool-use.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PeerReviewAcceptanceTests(unittest.TestCase):
    """16 manual peer-review cases — bounty patterns block, safe variants allow."""

    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook_module()

    def test_required_destructive_patterns_block(self):
        blocked = (
            "rm -rf /tmp",
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE sessions",
            "DELETE FROM users",
            "sh -c 'DROP TABLE users'",
            "sudo DROP TABLE users",
            'docker exec db psql -c "DROP TABLE users"',
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(
                    self.hook.check_command(command),
                    f"expected block: {command!r}",
                )

    def test_safe_variants_allow(self):
        allowed = (
            "git status",
            "rm -f file.txt",
            "git push --force-with-lease origin main",
            'grep "DELETE FROM users" schema.sql',
            "npm run truncate-logs",
            "echo DROP TABLE users",
            "DELETE FROM users WHERE id=1",
            'find . -name "*.sql" | xargs grep DROP TABLE',
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(
                    self.hook.check_command(command),
                    f"expected allow: {command!r}",
                )


if __name__ == "__main__":
    unittest.main()
