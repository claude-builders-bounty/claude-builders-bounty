"""
Unit tests for Issue #1: Structured CHANGELOG generator.
Validates commit categorization, Keep-a-Changelog formatting, and prepending logic.
"""

from pathlib import Path
import tempfile
import sys

# Add script directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "generate-changelog" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from changelog import categorize_commit, update_changelog_file


def test_categorize_commit_conventional_prefixes():
    # Feat -> Added
    cat, msg, scope = categorize_commit("feat(auth): add passkey support")
    assert cat == "Added"
    assert msg == "add passkey support"
    assert scope == "auth"

    # Fix -> Fixed
    cat, msg, scope = categorize_commit("fix: resolve race condition in pool")
    assert cat == "Fixed"
    assert msg == "resolve race condition in pool"
    assert scope is None

    # Refactor/Perf -> Changed
    cat, msg, scope = categorize_commit("perf(db): optimize user index")
    assert cat == "Changed"
    assert scope == "db"

    # Remove -> Removed
    cat, msg, scope = categorize_commit("remove(v1): drop legacy routes")
    assert cat == "Removed"

    # Security -> Security
    cat, msg, scope = categorize_commit("security: update crypto library")
    assert cat == "Security"

    # Unprefixed -> Other
    cat, msg, scope = categorize_commit("update readme")
    assert cat == "Other"


def test_update_changelog_file_prepends_to_existing():
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog = Path(tmpdir) / "CHANGELOG.md"
        initial_content = "# Changelog\n\n## [v1.0.0] - 2026-01-01\n### Added\n- Initial release\n"
        changelog.write_text(initial_content, encoding="utf-8")

        new_entry = "## [v1.1.0] - 2026-10-17\n### Added\n- New feature\n"
        update_changelog_file(changelog, new_entry)

        result = changelog.read_text(encoding="utf-8")
        assert "## [v1.1.0] - 2026-10-17" in result
        assert "## [v1.0.0] - 2026-01-01" in result
        # v1.1.0 must appear before v1.0.0
        assert result.index("v1.1.0") < result.index("v1.0.0")


def test_deliverables_exist():
    skill_root = Path(__file__).resolve().parent.parent / "skills" / "generate-changelog"
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "README.md").exists()
    assert (skill_root / "scripts" / "changelog.py").exists()
    assert (skill_root / "scripts" / "changelog.sh").exists()
    assert (skill_root / "examples" / "SAMPLE_CHANGELOG.md").exists()
