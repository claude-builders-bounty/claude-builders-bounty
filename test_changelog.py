"""Tests for CHANGELOG generator skill (bounty #1)."""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import changelog  # noqa: E402


def test_categorize():
    assert changelog.categorize("fix login timeout") == "Fixed"
    assert changelog.categorize("bug: crash on startup") == "Fixed"
    assert changelog.categorize("remove deprecated API") == "Removed"
    assert changelog.categorize("delete legacy endpoint") == "Removed"
    assert changelog.categorize("update dependencies") == "Changed"
    assert changelog.categorize("add dark mode") == "Added"
    assert changelog.categorize("docs: refresh README") == "Changed"
    assert changelog.categorize("patch null pointer") == "Fixed"


def test_generates_structured_changelog():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        (repo / "README.md").write_text("# test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add readme"],
            cwd=repo,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "fix typo in docs"],
            cwd=repo,
            capture_output=True,
            check=True,
        )

        out = repo / "CHANGELOG.md"
        sys.argv = ["changelog.py", str(repo), str(out)]
        changelog.main()

        text = out.read_text(encoding="utf-8")
        assert "# Changelog" in text
        assert "### Added" in text
        assert "### Fixed" in text
        assert "add readme" in text
        assert "fix typo" in text


def test_since_last_tag():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=repo, capture_output=True, check=True)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        subprocess.run(["git", "add", "a.txt"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "add feature a"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "tag", "v0.1.0"], cwd=repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "fix crash after tag"], cwd=repo, capture_output=True, check=True)

        out = repo / "CHANGELOG.md"
        sys.argv = ["changelog.py", str(repo), str(out)]
        changelog.main()

        text = out.read_text(encoding="utf-8")
        assert "v0.1.0" in text
        assert "Changes since v0.1.0" in text
        assert "fix crash after tag" in text
        assert "add feature a" not in text


if __name__ == "__main__":
    test_categorize()
    test_generates_structured_changelog()
    test_since_last_tag()
    print("all tests passed")
