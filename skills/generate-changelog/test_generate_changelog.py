import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run(command, cwd):
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class GenerateChangelogTests(unittest.TestCase):
    def make_repo(self):
        temp_dir = tempfile.TemporaryDirectory()
        repo = Path(temp_dir.name)
        run(["git", "init"], repo)
        run(["git", "config", "user.email", "test@example.com"], repo)
        run(["git", "config", "user.name", "Test User"], repo)

        (repo / "app.txt").write_text("initial\n", encoding="utf-8")
        run(["git", "add", "app.txt"], repo)
        run(["git", "commit", "-m", "feat: initial tracked feature"], repo)
        run(["git", "tag", "v0.1.0"], repo)

        commits = [
            ("feat: add export command", "export\n"),
            ("fix: repair empty repo handling", "fix\n"),
            ("refactor: simplify release notes formatter", "refactor\n"),
            ("remove: drop legacy parser flag", "remove\n"),
        ]
        for message, line in commits:
            with (repo / "app.txt").open("a", encoding="utf-8") as handle:
                handle.write(line)
            run(["git", "add", "app.txt"], repo)
            run(["git", "commit", "-m", message], repo)

        return temp_dir, repo

    def test_generates_changelog_since_last_tag_with_categories(self):
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        output = repo / "CHANGELOG.md"

        result = run(["bash", "changelog.sh", "--repo", str(repo), "--output", str(output)], ROOT)

        self.assertEqual(result.returncode, 0, result.stderr)
        changelog = output.read_text(encoding="utf-8")
        self.assertIn("# Changelog", changelog)
        self.assertIn("## Unreleased", changelog)
        self.assertIn("Changes since `v0.1.0`", changelog)
        self.assertIn("### Added", changelog)
        self.assertIn("- add export command", changelog)
        self.assertIn("### Fixed", changelog)
        self.assertIn("- repair empty repo handling", changelog)
        self.assertIn("### Changed", changelog)
        self.assertIn("- simplify release notes formatter", changelog)
        self.assertIn("### Removed", changelog)
        self.assertIn("- drop legacy parser flag", changelog)
        self.assertNotIn("initial tracked feature", changelog)

    def test_relative_output_is_written_inside_target_repo(self):
        temp_dir, repo = self.make_repo()
        self.addCleanup(temp_dir.cleanup)
        misplaced_output = ROOT / "RELEASE_NOTES.md"
        self.addCleanup(lambda: misplaced_output.exists() and misplaced_output.unlink())

        result = run(["bash", "changelog.sh", "--repo", str(repo), "--output", "RELEASE_NOTES.md"], ROOT)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((repo / "RELEASE_NOTES.md").exists())
        self.assertFalse(misplaced_output.exists())


if __name__ == "__main__":
    unittest.main()
