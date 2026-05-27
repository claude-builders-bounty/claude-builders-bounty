from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.generate_changelog.generate_changelog import build_changelog, category_for, commits_since, latest_tag


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class GenerateChangelogTests(unittest.TestCase):
    def test_category_mapping(self) -> None:
        self.assertEqual(category_for("feat: add dashboard"), "Added")
        self.assertEqual(category_for("fix: handle empty input"), "Fixed")
        self.assertEqual(category_for("remove deprecated flag"), "Removed")
        self.assertEqual(category_for("docs: update usage"), "Changed")

    def test_reads_commits_since_latest_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "user.email", "test@example.com")

            (repo / "app.txt").write_text("initial\n", encoding="utf-8")
            git(repo, "add", "app.txt")
            git(repo, "commit", "-m", "chore: initial")
            git(repo, "tag", "v0.1.0")

            (repo / "app.txt").write_text("initial\nfeature\n", encoding="utf-8")
            git(repo, "add", "app.txt")
            git(repo, "commit", "-m", "feat: add feature")

            (repo / "app.txt").write_text("initial\nfeature\nfix\n", encoding="utf-8")
            git(repo, "add", "app.txt")
            git(repo, "commit", "-m", "fix: repair feature")

            tag = latest_tag(repo)
            commits = commits_since(repo, tag)
            changelog = build_changelog(commits, tag, "Unreleased")

        self.assertEqual(tag, "v0.1.0")
        self.assertEqual(len(commits), 2)
        self.assertIn("### Added", changelog)
        self.assertIn("feat: add feature", changelog)
        self.assertIn("### Fixed", changelog)
        self.assertIn("fix: repair feature", changelog)
        self.assertNotIn("chore: initial", changelog)


if __name__ == "__main__":
    unittest.main()
