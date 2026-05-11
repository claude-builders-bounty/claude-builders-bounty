#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR = REPO_ROOT / "tools" / "generate-changelog" / "generate_changelog.py"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=True)


def write_file(repo: Path, name: str, content: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def commit(repo: Path, message: str) -> None:
    run(["git", "add", "."], repo)
    run(["git", "commit", "-m", message], repo)


def init_repo(repo: Path) -> None:
    run(["git", "init"], repo)
    run(["git", "config", "user.email", "test@example.com"], repo)
    run(["git", "config", "user.name", "Test User"], repo)


class GenerateChangelogTests(unittest.TestCase):
    def test_generates_sections_from_commits_since_latest_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_file(repo, "app.txt", "initial\n")
            commit(repo, "chore: initial commit")
            run(["git", "tag", "v0.1.0"], repo)

            write_file(repo, "feature.txt", "new\n")
            commit(repo, "feat: add export button")
            write_file(repo, "bug.txt", "fixed\n")
            commit(repo, "fix: handle empty response")
            write_file(repo, "docs.txt", "docs\n")
            commit(repo, "docs: update setup notes")
            run(["git", "rm", "feature.txt"], repo)
            commit(repo, "remove deprecated export fixture")

            run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--repo",
                    str(repo),
                    "--output",
                    "CHANGELOG.md",
                    "--date",
                    "2026-05-11",
                ],
                REPO_ROOT,
            )

            changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("Generated from commits since `v0.1.0`.", changelog)
            self.assertIn("### Added\n- add export button", changelog)
            self.assertIn("### Fixed\n- handle empty response", changelog)
            self.assertIn("### Changed\n- update setup notes", changelog)
            self.assertIn("### Removed\n- remove deprecated export fixture", changelog)
            self.assertNotIn("initial commit", changelog)

    def test_no_tag_uses_full_history_and_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)
            write_file(repo, "app.txt", "initial\n")
            commit(repo, "add first file")

            result = run(
                [
                    sys.executable,
                    str(GENERATOR),
                    "--repo",
                    str(repo),
                    "--stdout",
                    "--date",
                    "2026-05-11",
                ],
                REPO_ROOT,
            )

            self.assertIn("Generated from the full repository history because no git tags were found.", result.stdout)
            self.assertIn("### Added\n- add first file", result.stdout)


if __name__ == "__main__":
    unittest.main()
