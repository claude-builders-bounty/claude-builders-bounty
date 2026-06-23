import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_changelog.py"


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)
    return result.stdout.strip()


def commit(repo: Path, filename: str, content: str, message: str) -> None:
    (repo / filename).write_text(content, encoding="utf-8")
    git(repo, "add", filename)
    git(repo, "commit", "-m", message)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    commit(repo, "base.txt", "base", "chore: initial commit")
    git(repo, "tag", "v0.1.0")
    commit(repo, "feature.txt", "feature", "feat: add report export")
    commit(repo, "fix.txt", "fix", "fix: handle empty response")
    commit(repo, "docs.txt", "docs", "docs: explain setup")
    commit(repo, "removed.txt", "removed", "remove deprecated flag")
    return repo


def test_generates_categorized_changelog_since_latest_tag(tmp_path):
    repo = make_repo(tmp_path)

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--stdout"],
        text=True,
        capture_output=True,
        check=True,
    )

    output = result.stdout
    assert "Commits since `v0.1.0`." in output
    assert "### Added" in output
    assert "feat: add report export" in output
    assert "### Fixed" in output
    assert "fix: handle empty response" in output
    assert "### Changed" in output
    assert "docs: explain setup" in output
    assert "### Removed" in output
    assert "remove deprecated flag" in output
    assert "chore: initial commit" not in output


def test_writes_changelog_file(tmp_path):
    repo = make_repo(tmp_path)
    output_path = repo / "CHANGELOG.md"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--output", str(output_path)],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Wrote" in result.stdout
    assert output_path.exists()
    assert "# Changelog" in output_path.read_text(encoding="utf-8")
