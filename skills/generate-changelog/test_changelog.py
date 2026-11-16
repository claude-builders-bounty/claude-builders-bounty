from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from changelog import classify_commit, fetch_commits, get_latest_tag, render_changelog


def test_classify_commit_categories():
    assert classify_commit("feat(router): add LiteLLM load balancer")[0] == "Added"
    assert classify_commit("Add new CLI flag for JSON output")[0] == "Added"
    assert classify_commit("fix(auth): resolve token refresh race condition")[0] == "Fixed"
    assert classify_commit("Fixed crash when git tag is missing")[0] == "Fixed"
    assert classify_commit("refactor(core): simplify retry backoff loop")[0] == "Changed"
    assert classify_commit("docs: update installation guide")[0] == "Changed"
    assert classify_commit("remove: drop deprecated v1 endpoint")[0] == "Removed"
    assert classify_commit("Delete legacy python 2 compatibility shim")[0] == "Removed"


def test_git_tag_and_changelog_generation(tmp_path: Path):
    repo = tmp_path / "demo_repo"
    repo.mkdir()

    def git(*args: str):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)

    git("init")
    git("config", "user.email", "builder@example.com")
    git("config", "user.name", "Claude Builder")

    (repo / "app.py").write_text("print('v1.0.0')\n", encoding="utf-8")
    git("add", "app.py")
    git("commit", "-m", "feat: initial release")
    git("tag", "v1.0.0")

    # Commits after v1.0.0 tag
    (repo / "app.py").write_text("print('v1.1.0')\n", encoding="utf-8")
    git("commit", "-am", "feat(cli): add --since-tag option (#12)")

    (repo / "bug.py").write_text("x = 1\n", encoding="utf-8")
    git("add", "bug.py")
    git("commit", "-m", "fix(parser): handle empty commit body gracefully (#15)")

    (repo / "app.py").write_text("print('v1.1.0-refactored')\n", encoding="utf-8")
    git("commit", "-am", "refactor(output): align markdown headers with Keep-a-Changelog")

    git("rm", "bug.py")
    git("commit", "-m", "remove: drop obsolete bug.py helper")

    latest_tag = get_latest_tag(repo)
    assert latest_tag == "v1.0.0"

    commits = fetch_commits(repo, since_tag=latest_tag)
    assert len(commits) == 4

    md = render_changelog(
        commits=commits,
        version="1.1.0",
        since_tag=latest_tag,
        repo_url="https://github.com/claude-builders-bounty/claude-builders-bounty",
        date_str="2026-11-16",
    )

    assert "## [1.1.0] - 2026-11-16" in md
    assert "### Added" in md
    assert "**cli**: add --since-tag option (#12)" in md
    assert "### Fixed" in md
    assert "**parser**: handle empty commit body gracefully (#15)" in md
    assert "### Changed" in md
    assert "**output**: align markdown headers with Keep-a-Changelog" in md
    assert "### Removed" in md
    assert "**None**" not in md
    assert "drop obsolete bug.py helper" in md


if __name__ == "__main__":
    import tempfile
    test_classify_commit_categories()
    with tempfile.TemporaryDirectory() as td:
        test_git_tag_and_changelog_generation(Path(td))
    print("[PASS] All test_changelog.py assertions succeeded!")
