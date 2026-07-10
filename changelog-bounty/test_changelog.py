"""Tests for changelog.py — run with: python3 -m pytest test_changelog.py -v"""
import subprocess
import sys
from pathlib import Path

PY = str(Path(__file__).parent / "changelog.py")
REPO = str(Path(__file__).parent / "_fixture")


def _setup_repo(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "config", "user.email", "t@t.com"], check=True)
    subprocess.run(["git", "-C", str(r), "config", "user.name", "t"], check=True)
    (r / "a.txt").write_text("a")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-qm", "feat: add a"], check=True)
    (r / "b.txt").write_text("b")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-qm", "fix: repair b"], check=True)
    subprocess.run(["git", "-C", str(r), "tag", "v0.1"], check=True)
    (r / "c.txt").write_text("c")
    subprocess.run(["git", "-C", str(r), "add", "."], check=True)
    subprocess.run(["git", "-C", str(r), "commit", "-qm", "docs: note c"], check=True)
    return str(r)


def test_unreleased_groups(tmp_path):
    r = _setup_repo(tmp_path)
    out = tmp_path / "out.md"
    subprocess.run([sys.executable, PY, "--repo", r, "--title", "U", "--output", str(out)], check=True)
    text = out.read_text()
    assert "### Added" in text and "- feat: add a" in text
    assert "### Fixed" in text and "- fix: repair b" in text
    assert "### Documentation" in text and "- docs: note c" in text


def test_tag_range(tmp_path):
    r = _setup_repo(tmp_path)
    out = tmp_path / "out.md"
    subprocess.run([sys.executable, PY, "--repo", r, "--from-tag", "v0.1",
                    "--to-tag", "HEAD", "--title", "v0.2", "--output", str(out)], check=True)
    text = out.read_text()
    assert "docs: note c" in text
    assert "feat: add a" not in text  # before the tag


def test_no_commits(tmp_path):
    r = tmp_path / "empty"
    r.mkdir()
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    res = subprocess.run([sys.executable, PY, "--repo", str(r), "--title", "X", "--output", str(tmp_path / "x.md")])
    assert res.returncode == 1
