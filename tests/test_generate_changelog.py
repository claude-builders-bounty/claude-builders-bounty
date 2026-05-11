import tempfile
import unittest
from pathlib import Path

from changelog_import import load_module


generate_changelog = load_module()


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_conventional_commits(self):
        commits = [
            generate_changelog.Commit("1111111", "feat: add billing page"),
            generate_changelog.Commit("2222222", "fix(auth): reject expired sessions"),
            generate_changelog.Commit("3333333", "refactor: split dashboard queries"),
            generate_changelog.Commit("4444444", "remove old webhook handler"),
        ]
        grouped = generate_changelog.group_commits(commits)
        self.assertEqual(grouped["Added"][0].sha, "1111111")
        self.assertEqual(grouped["Fixed"][0].sha, "2222222")
        self.assertEqual(grouped["Changed"][0].sha, "3333333")
        self.assertEqual(grouped["Removed"][0].sha, "4444444")

    def test_renders_required_sections(self):
        commits = [generate_changelog.Commit("abc1234", "feat: add workspace invites")]
        output = generate_changelog.render_changelog(commits, start_ref="v1.0.0", version="v1.1.0")
        self.assertIn("# Changelog", output)
        self.assertIn("## v1.1.0", output)
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Changed", output)
        self.assertIn("### Removed", output)
        self.assertIn("Add workspace invites", output)

    def test_writes_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(generate_changelog.render_changelog([], "v0.1.0"), encoding="utf-8")
            self.assertIn("No commits found", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
