"""
Unit tests for generate_changelog skill.
"""

import sys
from pathlib import Path

# Add skill directory to sys.path
SKILL_DIR = Path(__file__).parent.parent / "skills" / "generate-changelog"
sys.path.insert(0, str(SKILL_DIR))

from generate_changelog import categorize_commit, build_changelog_markdown, generate_changelog


def test_categorize_commit():
    assert categorize_commit("feat: add user authentication") == "Added"
    assert categorize_commit("fix(auth): resolve JWT expiration crash") == "Fixed"
    assert categorize_commit("remove deprecated v1 endpoint") == "Removed"
    assert categorize_commit("refactor logging utility") == "Changed"


def test_build_changelog_markdown():
    categorized = {
        "Added": [("a1b2c3d", "Alice", "feat: add user auth")],
        "Fixed": [("e5f6g7h", "Bob", "fix: memory leak")],
        "Changed": [],
        "Removed": []
    }
    content = build_changelog_markdown(categorized, version="v1.0.0")
    assert "# Changelog" in content
    assert "## [v1.0.0]" in content
    assert "### Added" in content
    assert "- feat: add user auth (`a1b2c3d` by Alice)" in content
    assert "### Fixed" in content
    assert "- fix: memory leak (`e5f6g7h` by Bob)" in content


def test_generate_changelog(tmp_path):
    output_file = tmp_path / "TEST_CHANGELOG.md"
    content = generate_changelog(output_file=str(output_file))
    assert output_file.exists()
    assert "# Changelog" in content
