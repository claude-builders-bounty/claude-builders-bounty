import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "skills" / "generate-changelog" / "generate_changelog.py"


class GenerateChangelogTest(unittest.TestCase):
    def run_git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)

    def commit_file(self, repo, name, content, message):
        path = repo / name
        path.write_text(content, encoding="utf-8")
        self.run_git(repo, "add", name)
        self.run_git(repo, "commit", "-m", message)

    def test_generates_changelog_since_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.run_git(repo, "init")
            self.run_git(repo, "config", "user.name", "Test User")
            self.run_git(repo, "config", "user.email", "test@example.com")

            self.commit_file(repo, "README.md", "initial\n", "chore: initial commit")
            self.run_git(repo, "tag", "v1.0.0")
            self.commit_file(repo, "feature.txt", "feature\n", "feat: add dashboard")
            self.commit_file(repo, "bug.txt", "bug\n", "fix: repair login redirect")
            self.commit_file(repo, "old.txt", "removed\n", "remove deprecated route")

            output = repo / "CHANGELOG.md"
            subprocess.run(
                [sys.executable, str(GENERATOR), "--repo", str(repo), "--output", str(output)],
                check=True,
                capture_output=True,
                text=True,
            )

            changelog = output.read_text(encoding="utf-8")
            self.assertIn("using commits since `v1.0.0`", changelog)
            self.assertIn("### Added", changelog)
            self.assertIn("feat: add dashboard", changelog)
            self.assertIn("### Fixed", changelog)
            self.assertIn("fix: repair login redirect", changelog)
            self.assertIn("### Removed", changelog)
            self.assertIn("remove deprecated route", changelog)
            self.assertNotIn("chore: initial commit", changelog)


if __name__ == "__main__":
    unittest.main()
