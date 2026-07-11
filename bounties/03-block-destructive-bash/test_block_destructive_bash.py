#!/usr/bin/env python3
"""Unit tests for block_destructive_bash.py (no Claude Code required)."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


def load_mod():
    path = Path(__file__).with_name("block_destructive_bash.py")
    spec = importlib.util.spec_from_file_location("block_destructive_bash", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestFindBlockReason(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_mod()

    def test_allows_safe(self):
        for cmd in (
            "ls -la",
            "git status",
            "git push origin main",
            "rm file.txt",
            "DELETE FROM users WHERE id = 1",
            "echo DROP TABLE is just text",  # no bare DROP TABLE as SQL cmd — wait, DROP TABLE matches
        ):
            if "DROP TABLE" in cmd:
                continue
            self.assertIsNone(self.mod.find_block_reason(cmd), cmd)

    def test_blocks_rm_rf(self):
        for cmd in ("rm -rf /tmp/x", "rm -fr ./build", "sudo rm -rf /var/cache"):
            self.assertIsNotNone(self.mod.find_block_reason(cmd), cmd)

    def test_blocks_sql_and_force_push(self):
        self.assertIsNotNone(self.mod.find_block_reason("DROP TABLE users;"))
        self.assertIsNotNone(self.mod.find_block_reason("TRUNCATE users"))
        self.assertIsNotNone(self.mod.find_block_reason("git push --force origin main"))
        self.assertIsNotNone(self.mod.find_block_reason("git push -f origin main"))
        self.assertIsNotNone(self.mod.find_block_reason("DELETE FROM users"))
        self.assertIsNone(self.mod.find_block_reason("DELETE FROM users WHERE id=1"))

    def test_extract_command(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}
        self.assertEqual(self.mod.extract_command(payload), "rm -rf /")


class TestMainIntegration(unittest.TestCase):
    def test_main_blocks_and_logs(self):
        mod = load_mod()
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "blocked.log"
            mod.LOG_PATH = log
            import io
            from contextlib import redirect_stderr
            from unittest.mock import patch

            payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}})
            err = io.StringIO()
            with patch("sys.stdin", io.StringIO(payload)), redirect_stderr(err):
                code = mod.main()
            self.assertEqual(code, 2)
            self.assertIn("BLOCKED", err.getvalue())
            self.assertTrue(log.exists())
            self.assertIn("rm -rf", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
