"""
Automated Unit and Integration Tests for CHANGELOG Generator (#1).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add script directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from changelog import (
    categorize_commit,
    format_changelog_section,
    update_changelog_file,
    CATEGORIES,
    HEADER
)

def test_categorize_commit():
    assert categorize_commit("feat(auth): add OAuth2 provider support") == "Added"
    assert categorize_commit("feat: initial release") == "Added"
    assert categorize_commit("add new billing dashboard") == "Added"
    assert categorize_commit("fix(api): handle null pointer on missing token") == "Fixed"
    assert categorize_commit("bugfix: resolve race condition in pool") == "Fixed"
    assert categorize_commit("refactor: extract token validation into middleware") == "Changed"
    assert categorize_commit("perf: accelerate SQLite index scan") == "Changed"
    assert categorize_commit("chore: bump dependencies to latest") == "Changed"
    assert categorize_commit("remove deprecated v1 REST endpoints") == "Removed"
    assert categorize_commit("deprecate legacy crypto signing module") == "Removed"
    assert categorize_commit("sec(crypto): sanitize input to prevent timing attacks") == "Security"
    assert categorize_commit("fix CVE-2026-1192 vulnerability") == "Security"

def test_format_changelog_section():
    commits = [
        ("abc1234", "feat(auth): add multi-tenant SSO", "Dev"),
        ("def5678", "fix(db): close idle connection leak", "Dev"),
        ("789abcd", "chore: upgrade React to 19.0", "Dev"),
        ("0123456", "remove legacy cookie fallback", "Dev")
    ]
    section = format_changelog_section("v1.2.0", "2026-11-01", commits)
    assert "## [v1.2.0] - 2026-11-01" in section
    assert "### Added" in section
    assert "add multi-tenant SSO (`abc1234`)" in section
    assert "### Fixed" in section
    assert "close idle connection leak (`def5678`)" in section
    assert "### Changed" in section
    assert "### Removed" in section

def test_update_changelog_file_create_and_prepend():
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_file = os.path.join(tmp_dir, "CHANGELOG.md")

        # 1. First release
        section_v1 = "## [v1.0.0] - 2026-10-01\n\n### Added\n- Initial release (`1111111`)"
        update_changelog_file(target_file, section_v1)

        with open(target_file, "r", encoding="utf-8") as f:
            content1 = f.read()

        assert "# Changelog" in content1
        assert "## [v1.0.0] - 2026-10-01" in content1

        # 2. Second release (prepend)
        section_v2 = "## [v1.1.0] - 2026-11-01\n\n### Added\n- New dark mode theme (`2222222`)"
        update_changelog_file(target_file, section_v2)

        with open(target_file, "r", encoding="utf-8") as f:
            content2 = f.read()

        assert "## [v1.1.0] - 2026-11-01" in content2
        assert "## [v1.0.0] - 2026-10-01" in content2
        # Verify v1.1.0 appears before v1.0.0
        assert content2.index("## [v1.1.0]") < content2.index("## [v1.0.0]")
