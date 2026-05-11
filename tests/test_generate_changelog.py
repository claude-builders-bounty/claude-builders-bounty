import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_changelog.py"


class GenerateChangelogTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit_file(self, repo: Path, filename: str, content: str, message: str) -> None:
        path = repo / filename
        path.write_text(content, encoding="utf-8")
        self.git(repo, "add", filename)
        self.git(repo, "commit", "-m", message)

    def test_generates_sections_from_commits_since_latest_tag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            self.git(repo, "init")
            self.git(repo, "config", "user.email", "test@example.com")
            self.git(repo, "config", "user.name", "Test User")

            self.commit_file(repo, "app.txt", "initial\n", "chore: initial setup")
            self.git(repo, "tag", "v1.0.0")
            self.commit_file(repo, "feature.txt", "feature\n", "feat: add dashboard")
            self.commit_file(repo, "fix.txt", "fix\n", "fix(auth): handle bad token")
            self.commit_file(repo, "refactor.txt", "refactor\n", "refactor: simplify migrations")
            self.commit_file(repo, "remove.txt", "remove\n", "remove legacy billing flag")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--stdout"],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = result.stdout

            self.assertIn("_Generated for", output)
            self.assertIn("changes since `v1.0.0`", output)
            self.assertIn("### Added", output)
            self.assertIn("- Add dashboard", output)
            self.assertIn("### Fixed", output)
            self.assertIn("- Handle bad token", output)
            self.assertIn("### Changed", output)
            self.assertIn("- Simplify migrations", output)
            self.assertIn("### Removed", output)
            self.assertIn("- Remove legacy billing flag", output)
            self.assertNotIn("Initial setup", output)


if __name__ == "__main__":
    unittest.main()
