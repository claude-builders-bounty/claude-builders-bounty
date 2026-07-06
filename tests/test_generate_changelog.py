import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_changelog.py"


def run(command, cwd):
    subprocess.run(command, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def commit_file(repo: Path, filename: str, content: str, message: str):
    path = repo / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run(["git", "add", filename], repo)
    run(["git", "commit", "-m", message], repo)


class GenerateChangelogTest(unittest.TestCase):
    def test_generates_changelog_from_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test User"], repo)

            commit_file(repo, "README.md", "initial\n", "chore: initial commit")
            run(["git", "tag", "v1.0.0"], repo)
            commit_file(repo, "feature.txt", "login\n", "feat(auth): add login flow")
            commit_file(repo, "fix.txt", "timeout\n", "fix(api): handle timeout")
            commit_file(repo, "ui.txt", "button\n", "refactor(ui): change button layout")
            commit_file(repo, "legacy.txt", "gone\n", "remove obsolete flag")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--version",
                    "v1.1.0",
                    "--dry-run",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            output = result.stdout
            self.assertIn("## v1.1.0 -", output)
            self.assertIn("Generated from commits since `v1.0.0`.", output)
            self.assertIn("### Added\n- Add login flow", output)
            self.assertIn("### Fixed\n- Handle timeout", output)
            self.assertIn("### Changed\n- Change button layout", output)
            self.assertIn("### Removed\n- Remove obsolete flag", output)
            self.assertNotIn("initial commit", output.lower())

    def test_writes_changelog_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run(["git", "init"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Test User"], repo)
            commit_file(repo, "README.md", "initial\n", "feat: add readme")

            output_path = repo / "CHANGELOG.md"
            subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--output", str(output_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            self.assertTrue(output_path.exists())
            self.assertIn("from full history", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
