#!/usr/bin/env python3
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_changelog.py"


def run(*args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True).strip()


def commit(repo: Path, message: str, filename: str):
    (repo / filename).write_text(message + "\n", encoding="utf-8")
    run("git", "add", filename, cwd=repo)
    run("git", "commit", "-m", message, cwd=repo)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        run("git", "init", cwd=repo)
        run("git", "config", "user.email", "test@example.com", cwd=repo)
        run("git", "config", "user.name", "Test User", cwd=repo)
        commit(repo, "initial commit", "a.txt")
        run("git", "tag", "v0.1.0", cwd=repo)
        commit(repo, "feat: add webhook support", "feature.txt")
        commit(repo, "fix: resolve webhook retry bug", "fix.txt")
        commit(repo, "remove legacy polling endpoint", "remove.txt")

        output = subprocess.check_output(
            ["python3", str(SCRIPT), "--repo", str(repo), "--output", "-"], text=True
        )
        assert "(since v0.1.0)" in output
        assert "### Added" in output
        assert "- Add webhook support" in output
        assert "### Fixed" in output
        assert "- Resolve webhook retry bug" in output
        assert "### Removed" in output
        assert "- Remove legacy polling endpoint" in output
    print("generate changelog tests passed")


if __name__ == "__main__":
    main()
