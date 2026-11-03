"""Self-check for generate_changelog.py: builds a temp git repo with sample
Conventional Commits and asserts every category lands correctly.

Run with pytest or directly: python test_generate_changelog.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).parent / "generate_changelog.py"

SAMPLE_COMMITS = [
    ("chore: init project", None),          # before the tag -> excluded
    ("TAG v0.1.0", None),
    ("feat: add user login", ""),
    ("fix(auth): null pointer in login", ""),
    ("refactor: simplify parser", ""),
    ("chore: remove legacy scripts", ""),
    ("feat!: drop python 3.8 support", ""),
    ("docs: rework README", "BREAKING CHANGE: new layout"),
    ("Update CI runners", None),            # non-conventional -> Changed
]


def make_repo(tmp):
    def run(*args, tag=False):
        if tag:
            subprocess.run(("git", "tag", *args), cwd=tmp, check=True)
            return
        subprocess.run(
            ("git", "-c", "user.name=T", "-c", "user.email=t@example.com", *args),
            cwd=tmp, check=True,
        )

    run("init")
    for subject, body in SAMPLE_COMMITS:
        if subject.startswith("TAG "):
            run(subject.split()[1], tag=True)
            continue
        args = ("commit", "--allow-empty", "-m", subject)
        if body:
            args += ("-m", body)
        run(*args)


def test_categories(tmp_path=None):
    with tempfile.TemporaryDirectory() as tmp:
        make_repo(tmp)
        out = Path(tmp) / "CHANGELOG.md"
        subprocess.run(
            (sys.executable, str(SCRIPT), tmp, "-o", str(out)), check=True,
            stdout=subprocess.DEVNULL,
        )
        text = out.read_text(encoding="utf-8")

    assert text.startswith("# Changelog\n")
    for expected in (
        "## [Unreleased]",
        "### Added", "- add user login",
        "### Fixed", "- **auth**: null pointer in login",
        "### Changed", "- simplify parser", "- Update CI runners",
        "### Removed", "- remove legacy scripts",
        "### Breaking Changes", "- drop python 3.8 support", "- rework README",
        "since `v0.1.0`",
    ):
        assert expected in text, f"missing: {expected!r}"
    assert "init project" not in text, "commits before the last tag must be excluded"


if __name__ == "__main__":
    test_categories()
    print("OK")
