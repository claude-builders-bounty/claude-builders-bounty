from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "generate_changelog.py"


class ChangelogIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Changelog Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def commit(self, message):
        self.git("commit", "--allow-empty", "-qm", message)

    def generate(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, success, result.stderr)
        path = self.repo / "CHANGELOG.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def test_tag_boundary_and_four_categories(self):
        self.commit("feat: already released")
        self.git("tag", "v1.0.0")
        for message in ("feat(api)!: support JSON", "fix: empty input", "refactor: parser", "remove: legacy API"):
            self.commit(message)
        output = self.generate()
        self.assertNotIn("already released", output)
        for category in ("Added", "Fixed", "Changed", "Removed"):
            self.assertIn(f"### {category}\n", output)

    def test_no_tags_uses_entire_history_and_unicode(self):
        self.commit("feat: 中文输入")
        self.assertIn("中文输入", self.generate())

    def test_annotated_tag_and_no_new_commits(self):
        self.commit("feat: initial")
        self.git("tag", "-a", "v1", "-m", "release")
        self.assertIn("No changes since the latest tag.", self.generate())

    def test_released_history_and_links_survive_repeated_runs(self):
        self.commit("fix: parser")
        suffix = "## [1.0.0] - 2025-01-01\n\nHand-edited release notes.\n\n[1.0.0]: https://example.com/release\n"
        (self.repo / "CHANGELOG.md").write_text("# Project changes\n\nIntro.\n\n## [Unreleased]\n\nOld pending text.\n\n" + suffix)
        output = self.generate()
        self.assertTrue(output.endswith(suffix))
        self.assertNotIn("Old pending text", output)
        self.assertEqual(output, self.generate())

    def test_insert_before_existing_release_without_unreleased(self):
        self.commit("fix: parser")
        (self.repo / "CHANGELOG.md").write_text("# Changes\n\n## 1.0\n\nExisting note.\n")
        output = self.generate()
        self.assertLess(output.index("## [Unreleased]"), output.index("## 1.0"))
        self.assertIn("Existing note.", output)

    def test_empty_repository_does_not_overwrite_existing_file(self):
        (self.repo / "CHANGELOG.md").write_text("Preserve me")
        self.assertEqual(self.generate(success=False), "Preserve me")

    def test_unreachable_newer_tag_is_not_used(self):
        self.commit("feat: initial")
        branch = self.git("branch", "--show-current")
        self.git("tag", "v1")
        self.git("checkout", "-qb", "other")
        self.commit("feat: unrelated")
        self.git("tag", "v99")
        self.git("checkout", "-q", branch)
        self.commit("fix: current branch")
        output = self.generate()
        self.assertIn("current branch", output)
        self.assertNotIn("unrelated", output)

    def test_shallow_clone_does_not_report_truncated_history(self):
        self.commit("feat: initial")
        target = Path(self.temp.name) / "shallow"
        self.git("clone", "--quiet", "--depth", "1", self.repo.as_uri(), str(target))
        self.repo = target
        self.generate(success=False)


if __name__ == "__main__":
    unittest.main()
