import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_changelog.py"


def run_git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)


def commit(repo, message, filename, contents):
    path = repo / filename
    path.write_text(contents, encoding="utf-8")
    run_git(repo, "add", filename)
    run_git(repo, "commit", "-m", message)


def test_generates_changelog_since_last_tag(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")

    commit(repo, "chore: initial commit", "README.md", "# Demo\n")
    run_git(repo, "tag", "v1.0.0")
    commit(repo, "feat: add billing dashboard", "billing.txt", "billing\n")
    commit(repo, "fix: patch login redirect", "login.txt", "login\n")
    commit(repo, "remove legacy exports", "legacy.txt", "legacy\n")
    commit(repo, "docs: update setup guide", "docs.txt", "docs\n")

    output = repo / "CHANGELOG.md"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo", str(repo), "--output", str(output), "--no-fetch"],
        text=True,
        capture_output=True,
        check=True,
    )

    changelog = output.read_text(encoding="utf-8")
    assert "Wrote" in result.stdout
    assert "Generated from commits since `v1.0.0`." in changelog
    assert "### Added\n\n- feat: add billing dashboard" in changelog
    assert "### Fixed\n\n- fix: patch login redirect" in changelog
    assert "### Removed\n\n- remove legacy exports" in changelog
    assert "### Changed\n\n- docs: update setup guide" in changelog
    assert "chore: initial commit" not in changelog
