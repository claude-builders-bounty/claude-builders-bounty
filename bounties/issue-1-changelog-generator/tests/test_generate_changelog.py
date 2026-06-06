from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


GENERATOR_DIR = Path(__file__).resolve().parents[1]
GENERATOR_PATH = GENERATOR_DIR / "generate_changelog.py"

spec = importlib.util.spec_from_file_location("generate_changelog", GENERATOR_PATH)
generator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = generator
spec.loader.exec_module(generator)


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, text=True, capture_output=True)


def commit(repo: Path, filename: str, content: str, message: str) -> None:
    (repo / filename).write_text(content, encoding="utf-8")
    run(repo, "add", filename)
    run(repo, "commit", "-m", message)


class GenerateChangelogTest(unittest.TestCase):
    def test_categorizes_commits_since_latest_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            run(repo, "init")
            run(repo, "config", "user.name", "Test User")
            run(repo, "config", "user.email", "test@example.com")

            commit(repo, "README.md", "initial", "chore: initial commit")
            run(repo, "tag", "v1.0.0")
            commit(repo, "feature.txt", "feature", "feat: add webhook endpoint")
            commit(repo, "fix.txt", "fix", "fix: handle empty payloads")
            commit(repo, "change.txt", "change", "chore: update release notes")
            commit(repo, "remove.txt", "remove", "remove deprecated config flag")

            output = repo / "CHANGELOG.md"
            changelog = generator.generate(repo, output)

            self.assertIn("since `v1.0.0`", changelog)
            self.assertIn("### Added", changelog)
            self.assertIn("feat: add webhook endpoint", changelog)
            self.assertIn("### Fixed", changelog)
            self.assertIn("fix: handle empty payloads", changelog)
            self.assertIn("### Changed", changelog)
            self.assertIn("chore: update release notes", changelog)
            self.assertIn("### Removed", changelog)
            self.assertIn("remove deprecated config flag", changelog)
            self.assertNotIn("chore: initial commit", changelog)
            self.assertEqual(output.read_text(encoding="utf-8"), changelog)

    def test_uses_all_commits_when_no_tag_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo = Path(tmp_dir)
            run(repo, "init")
            run(repo, "config", "user.name", "Test User")
            run(repo, "config", "user.email", "test@example.com")
            commit(repo, "README.md", "initial", "feat: first release")

            changelog = generator.generate(repo, repo / "CHANGELOG.md")

            self.assertIn("from all commits", changelog)
            self.assertIn("feat: first release", changelog)


if __name__ == "__main__":
    unittest.main()
