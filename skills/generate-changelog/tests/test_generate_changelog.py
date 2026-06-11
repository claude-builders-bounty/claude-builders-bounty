from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_changelog.py"


def git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return result.stdout


def commit(repo: Path, filename: str, content: str, message: str) -> None:
    (repo / filename).write_text(content, encoding="utf-8")
    git(repo, "add", filename)
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
        }
    )
    git(repo, "commit", "-m", message, env=env)


class GenerateChangelogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        git(self.repo, "init")
        git(self.repo, "config", "user.email", "test@example.com")
        git(self.repo, "config", "user.name", "Test User")
        commit(self.repo, "README.md", "initial\n", "chore: initial release")
        git(self.repo, "tag", "v1.0.0")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_script(self, *args: str) -> str:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--stdout", *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.stdout

    def test_uses_latest_tag_and_groups_commits(self) -> None:
        commit(self.repo, "feature.txt", "feature\n", "feat: add export button")
        commit(self.repo, "bug.txt", "bug\n", "fix(parser): handle empty history")
        commit(self.repo, "old.txt", "gone\n", "remove legacy changelog task")
        commit(self.repo, "docs.txt", "docs\n", "docs: explain setup")

        changelog = self.run_script()

        self.assertIn("Generated from commits since `v1.0.0` through `HEAD`.", changelog)
        self.assertIn("### Added\n\n- Add export button", changelog)
        self.assertIn("### Fixed\n\n- Handle empty history", changelog)
        self.assertIn("### Changed\n\n- Explain setup", changelog)
        self.assertIn("### Removed\n\n- Remove legacy changelog task", changelog)
        self.assertNotIn("Initial release", changelog)

    def test_writes_changelog_file(self) -> None:
        commit(self.repo, "feature.txt", "feature\n", "feat: add cli flag")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo)],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertIn("Wrote CHANGELOG.md with 1 commits", result.stdout)
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.startswith("# Changelog"))
        self.assertIn("- Add cli flag", changelog)

    def test_explicit_from_ref_overrides_latest_tag(self) -> None:
        commit(self.repo, "feature.txt", "feature\n", "feat: add cli flag")
        git(self.repo, "tag", "v1.1.0")
        commit(self.repo, "fix.txt", "fix\n", "fix: repair output path")

        changelog = self.run_script("--from-ref", "v1.0.0")

        self.assertIn("- Add cli flag", changelog)
        self.assertIn("- Repair output path", changelog)


if __name__ == "__main__":
    unittest.main()
