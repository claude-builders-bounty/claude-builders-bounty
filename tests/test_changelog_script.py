import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "changelog.sh"


def run(command, cwd, **kwargs):
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True, **kwargs)


class ChangelogScriptTests(unittest.TestCase):
    def test_generates_categorized_changelog_since_last_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test User"], repo)

            (repo / "app.txt").write_text("initial\n", encoding="utf-8")
            run(["git", "add", "app.txt"], repo)
            run(["git", "commit", "-m", "chore: initial import"], repo)
            run(["git", "tag", "v0.1.0"], repo)

            commits = [
                ("feat: add billing dashboard", "billing\n"),
                ("fix: repair invoice total", "invoice\n"),
                ("docs: update setup notes", "docs\n"),
                ("remove: drop legacy export", "remove\n"),
            ]
            for message, content in commits:
                (repo / "app.txt").write_text(content, encoding="utf-8")
                run(["git", "add", "app.txt"], repo)
                run(["git", "commit", "-m", message], repo)

            output = repo / "CHANGELOG.md"
            result = run([str(SCRIPT), str(output)], repo)
            changelog = output.read_text(encoding="utf-8")

            self.assertIn("Wrote", result.stdout)
            self.assertIn("## Unreleased - since v0.1.0", changelog)
            self.assertIn("### Added", changelog)
            self.assertIn("feat: add billing dashboard", changelog)
            self.assertIn("### Fixed", changelog)
            self.assertIn("fix: repair invoice total", changelog)
            self.assertIn("### Changed", changelog)
            self.assertIn("docs: update setup notes", changelog)
            self.assertIn("### Removed", changelog)
            self.assertIn("remove: drop legacy export", changelog)
            self.assertNotIn("chore: initial import", changelog)


if __name__ == "__main__":
    unittest.main()
