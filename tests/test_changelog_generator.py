import os
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "changelog.sh"


def run(cmd, cwd, check=True):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {cmd}\nexit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def commit_file(repo: Path, filename: str, content: str, message: str):
    path = repo / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    run(f"git add {filename}", repo)
    run(f"git commit -m {message!r}", repo)


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample-repo"
    repo.mkdir()
    run("git init", repo)
    run("git config user.email tests@example.com", repo)
    run("git config user.name Tests", repo)
    commit_file(repo, "README.md", "# sample\n", "chore: initial commit")
    run("git tag v0.1.0", repo)
    return repo


def copy_script(repo: Path):
    shutil.copy2(SCRIPT, repo / "changelog.sh")
    os.chmod(repo / "changelog.sh", 0o755)


def test_generates_changelog_since_latest_tag_with_keepachangelog_categories(tmp_path):
    repo = make_repo(tmp_path)
    commit_file(repo, "src/feature.txt", "feature\n", "feat: add webhook ingestion")
    commit_file(repo, "src/bug.txt", "bug\n", "fix(api): handle empty payloads")
    commit_file(repo, "src/change.txt", "change\n", "refactor: simplify parser internals")
    commit_file(repo, "src/remove.txt", "remove\n", "remove legacy CSV exporter")
    commit_file(repo, "docs/usage.md", "docs\n", "docs: document CLI usage")
    copy_script(repo)

    result = run("bash changelog.sh", repo)
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "# Changelog" in changelog
    assert "## [Unreleased]" in changelog
    assert "### Added" in changelog
    assert "- add webhook ingestion" in changelog
    assert "### Fixed" in changelog
    assert "- handle empty payloads" in changelog
    assert "### Changed" in changelog
    assert "- simplify parser internals" in changelog
    assert "- document CLI usage" in changelog
    assert "### Removed" in changelog
    assert "- legacy CSV exporter" in changelog
    assert "initial commit" not in changelog


def test_supports_custom_output_file_and_no_tags(tmp_path):
    repo = tmp_path / "untagged-repo"
    repo.mkdir()
    run("git init", repo)
    run("git config user.email tests@example.com", repo)
    run("git config user.name Tests", repo)
    commit_file(repo, "README.md", "# sample\n", "feat: create project scaffold")
    commit_file(repo, "bug.txt", "bug\n", "bugfix: repair install command")
    copy_script(repo)

    result = run("bash changelog.sh RELEASE_NOTES.md", repo)
    output = (repo / "RELEASE_NOTES.md").read_text(encoding="utf-8")

    assert result.returncode == 0
    assert "No git tags found; using complete history." in result.stdout
    assert "- create project scaffold" in output
    assert "- repair install command" in output


def test_skips_merge_noise_and_duplicate_subjects(tmp_path):
    repo = make_repo(tmp_path)
    commit_file(repo, "one.txt", "one\n", "chore: update dependencies")
    commit_file(repo, "two.txt", "two\n", "chore: update dependencies")
    commit_file(repo, "merge.txt", "merge\n", "Merge branch 'main'")
    copy_script(repo)

    run("bash changelog.sh", repo)
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

    assert changelog.count("- update dependencies") == 1
    assert "Merge branch" not in changelog


def test_preserves_existing_changelog_by_prepending_new_unreleased_section(tmp_path):
    repo = make_repo(tmp_path)
    existing = textwrap.dedent(
        """\
        # Changelog

        ## [0.1.0] - 2026-01-01
        ### Added
        - initial release
        """
    )
    (repo / "CHANGELOG.md").write_text(existing, encoding="utf-8")
    commit_file(repo, "new.txt", "new\n", "feat: add export command")
    copy_script(repo)

    run("bash changelog.sh", repo)
    changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")

    assert changelog.count("# Changelog") == 1
    assert changelog.index("## [Unreleased]") < changelog.index("## [0.1.0] - 2026-01-01")
    assert "- add export command" in changelog
    assert "- initial release" in changelog
