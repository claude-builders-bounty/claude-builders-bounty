#!/usr/bin/env python3
"""Unit tests for generate_changelog (no network)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from generate_changelog import (  # noqa: E402
    classify,
    clean_subject,
    collect_commits,
    main,
    render,
)


class ClassifyTests(unittest.TestCase):
    def test_conventional(self):
        self.assertEqual(classify("feat: add login"), "Added")
        self.assertEqual(classify("fix(api): null deref"), "Fixed")
        self.assertEqual(classify("chore!: drop node 16"), "Changed")
        self.assertEqual(classify("remove: legacy flag"), "Removed")

    def test_heuristic(self):
        self.assertEqual(classify("Fixed crash on empty input"), "Fixed")
        self.assertEqual(classify("Add dark mode toggle"), "Added")
        self.assertEqual(classify("Remove unused CSS"), "Removed")

    def test_clean(self):
        self.assertEqual(clean_subject("feat: add login (#12)"), "Add login")


class IntegrationTests(unittest.TestCase):
    def test_render_and_cli_on_temp_repo(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "t@example.com"], cwd=repo, check=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=repo, check=True
            )
            (repo / "a.txt").write_text("a\n", encoding="utf-8")
            subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "feat: initial file"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "tag", "v0.1.0"], cwd=repo, check=True)
            (repo / "b.txt").write_text("b\n", encoding="utf-8")
            subprocess.run(["git", "add", "b.txt"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "fix: correct typo"],
                cwd=repo,
                check=True,
                capture_output=True,
            )
            commits = collect_commits(repo, "v0.1.0")
            self.assertEqual(len(commits), 1)
            block = render("Unreleased", commits)
            self.assertIn("### Fixed", block)
            self.assertIn("Correct typo", block)

            out = repo / "CHANGELOG.md"
            rc = main(["--repo", str(repo), "--output", str(out)])
            self.assertEqual(rc, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("# Changelog", text)
            self.assertIn("### Fixed", text)


if __name__ == "__main__":
    unittest.main()
