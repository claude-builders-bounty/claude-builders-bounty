import subprocess
import tempfile
import unittest
from pathlib import Path

import changelog


class ChangelogTests(unittest.TestCase):
    def test_parse_commits(self):
        commits = changelog.parse_commits("abc123\tfeat: add login\nfff999\tfix checkout total")
        self.assertEqual(commits[0], changelog.Commit(hash="abc123", subject="feat: add login"))
        self.assertEqual(commits[1].subject, "fix checkout total")

    def test_categorize_conventional_and_keyword_subjects(self):
        self.assertEqual(changelog.categorize("feat: add export button"), "Added")
        self.assertEqual(changelog.categorize("feat!: change public API"), "Added")
        self.assertEqual(changelog.categorize("fix: prevent crash"), "Fixed")
        self.assertEqual(changelog.categorize("remove deprecated flag"), "Removed")
        self.assertEqual(changelog.categorize("docs: update setup notes"), "Changed")
        self.assertEqual(changelog.categorize("tighten validation"), "Changed")

    def test_render_changelog_includes_all_sections(self):
        commits = [
            changelog.Commit("a1", "feat: add reports"),
            changelog.Commit("b2", "fix: handle empty input"),
            changelog.Commit("c3", "remove old endpoint"),
            changelog.Commit("d4", "docs: refresh README"),
        ]
        rendered = changelog.render_changelog(commits, "v1.0.0", "v1.1.0")
        self.assertIn("## v1.1.0 - ", rendered)
        self.assertIn("_Commits since: v1.0.0_", rendered)
        for heading in ("### Added", "### Fixed", "### Changed", "### Removed"):
            self.assertIn(heading, rendered)
        self.assertIn("- feat: add reports (a1)", rendered)
        self.assertIn("- fix: handle empty input (b2)", rendered)
        self.assertIn("- remove old endpoint (c3)", rendered)
        self.assertIn("- docs: refresh README (d4)", rendered)

    def test_render_empty_range(self):
        rendered = changelog.render_changelog([], "v1.0.0")
        self.assertIn("No commits found for this range.", rendered)

    def test_commit_range_uses_latest_tag_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            (repo / "file.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "feat: first"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)
            (repo / "file.txt").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "commit", "-am", "fix: second"], cwd=repo, check=True, capture_output=True)

            label, revision_range = changelog.get_commit_range(repo)
            commits = changelog.get_commits(repo, revision_range)

            self.assertEqual(label, "v1.0.0")
            self.assertEqual([commit.subject for commit in commits], ["fix: second"])

    def test_commit_range_falls_back_to_head_without_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            label, revision_range = changelog.get_commit_range(repo)
            self.assertEqual(label, "repository start")
            self.assertEqual(revision_range, "HEAD")


if __name__ == "__main__":
    unittest.main()
