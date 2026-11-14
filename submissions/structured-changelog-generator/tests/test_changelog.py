#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Small tests for changelog.py using a throwaway local git repo."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = ROOT / "changelog.py"


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="changelog-test-", dir=str(ROOT)))
        run(["git", "init", "-q"], self.tmp)
        run(["git", "config", "user.email", "test@example.com"], self.tmp)
        run(["git", "config", "user.name", "Test"], self.tmp)
        self._commit("feat: add alpha", "a.txt", "alpha\n")
        run(["git", "tag", "v1.0.0"], self.tmp)
        self._commit("fix: correct beta", "b.txt", "beta\n")
        self._commit("docs: update readme", "README.md", "readme\n")
        self._commit("Remove legacy module", "c.txt", "c\n")
        self._commit("Random cleanup", "d.txt", "d\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _commit(self, message, filename, content):
        (self.tmp / filename).write_text(content, encoding="utf-8")
        run(["git", "add", "-A"], self.tmp)
        run(["git", "commit", "-q", "-m", message], self.tmp)

    def test_since_latest_tag_categorizes(self):
        proc = run([sys.executable, str(SCRIPT), "--repo", str(self.tmp), "--no-links"], self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = proc.stdout
        self.assertIn("## Fixed", out)
        self.assertIn("correct beta", out)
        self.assertIn("## Changed", out)
        self.assertIn("update readme", out)
        self.assertIn("## Removed", out)
        self.assertIn("legacy module", out.lower())
        self.assertIn("## Other", out)
        self.assertIn("Random cleanup", out)
        # alpha was before the tag, so it must not appear
        self.assertNotIn("add alpha", out)

    def test_full_history_without_tag(self):
        run(["git", "tag", "-d", "v1.0.0"], self.tmp)
        proc = run([sys.executable, str(SCRIPT), "--repo", str(self.tmp), "--no-links"], self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("add alpha", proc.stdout)

    def test_output_file(self):
        out = self.tmp / "CHANGELOG.md"
        proc = run([sys.executable, str(SCRIPT), "--repo", str(self.tmp), "--output", str(out), "--no-links"], self.tmp)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(out.exists())
        self.assertIn("# Changelog", out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
