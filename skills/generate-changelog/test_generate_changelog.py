import subprocess
import tempfile
import unittest
from pathlib import Path

from generate_changelog import Commit, categorize, commits_since, last_tag, render


class ChangelogTests(unittest.TestCase):
    def test_conventional_commit_categories(self):
        self.assertEqual(categorize("feat(cli): add export"), ("Added", "add export"))
        self.assertEqual(categorize("fix: prevent crash"), ("Fixed", "prevent crash"))
        self.assertEqual(categorize("remove: legacy API"), ("Removed", "legacy API"))
        self.assertEqual(categorize("refactor!: rename API"), ("Changed", "**Breaking:** rename API"))

    def test_render_has_required_sections_and_short_sha(self):
        text = render([Commit("1234567890", "feat: add CLI"), Commit("abcdef1234", "fix: quote paths")], "v1.0.0")
        self.assertIn("### Added", text)
        self.assertIn("### Fixed", text)
        self.assertIn("`1234567`", text)
        self.assertIn("Changes since `v1.0.0`", text)

    def test_reads_only_commits_after_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", repo], check=True)
            subprocess.run(["git", "-C", repo, "config", "user.email", "test@example.com"], check=True)
            subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
            (repo / "a.txt").write_text("one")
            subprocess.run(["git", "-C", repo, "add", "a.txt"], check=True)
            subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "feat: initial"], check=True)
            subprocess.run(["git", "-C", repo, "tag", "v1.0.0"], check=True)
            (repo / "a.txt").write_text("two")
            subprocess.run(["git", "-C", repo, "commit", "-q", "-am", "fix: update file"], check=True)
            self.assertEqual(last_tag(repo), "v1.0.0")
            commits = commits_since(repo, "v1.0.0")
            self.assertEqual(len(commits), 1)
            self.assertEqual(commits[0].subject, "fix: update file")


if __name__ == "__main__":
    unittest.main()
