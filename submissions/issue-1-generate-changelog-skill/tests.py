#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "changelog.sh"


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "GIT_AUTHOR_NAME": "Test Author",
            "GIT_AUTHOR_EMAIL": "test@example.com",
            "GIT_COMMITTER_NAME": "Test Author",
            "GIT_COMMITTER_EMAIL": "test@example.com",
        }
    )
    return subprocess.run(args, cwd=repo, env=env, text=True, capture_output=True, check=True)


def commit(repo: Path, filename: str, content: str, message: str) -> None:
    path = repo / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    run(repo, "git", "add", filename)
    run(repo, "git", "commit", "-m", message)


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        repo = Path(temp_dir)
        run(repo, "git", "init")
        commit(repo, "README.md", "initial\n", "initial commit")
        run(repo, "git", "tag", "v0.1.0")
        commit(repo, "feature.txt", "feature\n", "feat: add lead scoring")
        commit(repo, "bug.txt", "fix\n", "fix: repair router bug")
        commit(repo, "config.txt", "config\n", "chore: update config")
        commit(repo, "old.txt", "removed\n", "remove deprecated endpoint")

        result = subprocess.run(
            ["bash", str(SCRIPT), "--repo", str(repo)],
            text=True,
            capture_output=True,
            check=True,
        )
        assert "latest_tag=v0.1.0" in result.stdout
        changelog = (repo / "CHANGELOG.md").read_text()
        assert "Changes since `v0.1.0`." in changelog
        assert "### Added" in changelog
        assert "feat: add lead scoring" in changelog
        assert "### Fixed" in changelog
        assert "fix: repair router bug" in changelog
        assert "### Changed" in changelog
        assert "chore: update config" in changelog
        assert "### Removed" in changelog
        assert "remove deprecated endpoint" in changelog

    print("tests_ok=true")


if __name__ == "__main__":
    main()
