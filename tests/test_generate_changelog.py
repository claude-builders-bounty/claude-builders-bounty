import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "changelog.sh"


def run(cmd, cwd, env=None):
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=cwd, env=merged, text=True, capture_output=True, check=True)


class GenerateChangelogTests(unittest.TestCase):
    def test_generates_expected_sections_since_last_tag(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Tester"], repo)
            (repo / "file.txt").write_text("base\n")
            run(["git", "add", "."], repo)
            run(["git", "commit", "-m", "chore: initial release"], repo)
            run(["git", "tag", "v1.0.0"], repo)

            commits = [
                ("feat: add export button", "add\n"),
                ("fix: correct login redirect", "fix\n"),
                ("refactor: simplify billing service", "change\n"),
                ("remove: legacy webhook handler", "remove\n"),
            ]
            for message, content in commits:
                (repo / "file.txt").write_text(content)
                run(["git", "add", "."], repo)
                run(["git", "commit", "-m", message], repo)

            run([str(SCRIPT)], repo)
            changelog = (repo / "CHANGELOG.md").read_text()
            self.assertIn("### Added", changelog)
            self.assertIn("- add export button", changelog)
            self.assertIn("### Fixed", changelog)
            self.assertIn("- correct login redirect", changelog)
            self.assertIn("### Changed", changelog)
            self.assertIn("- simplify billing service", changelog)
            self.assertIn("### Removed", changelog)
            self.assertIn("- legacy webhook handler", changelog)
            self.assertNotIn("initial release", changelog)

    def test_custom_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Tester"], repo)
            (repo / "file.txt").write_text("content\n")
            run(["git", "add", "."], repo)
            run(["git", "commit", "-m", "feat: add first thing"], repo)
            run([str(SCRIPT)], repo, env={"CHANGELOG_FILE": "RELEASE-NOTES.md"})
            self.assertTrue((repo / "RELEASE-NOTES.md").exists())
            self.assertFalse((repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
