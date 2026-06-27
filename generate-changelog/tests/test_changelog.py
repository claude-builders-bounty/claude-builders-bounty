"""Tests for changelog.py generation logic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from changelog import _categorize, _clean_title, _build_sections, generate_markdown


# ---------------------------------------------------------------------------
# _categorize
# ---------------------------------------------------------------------------

class TestCategorize:
    def test_feat_prefix(self):
        assert _categorize("feat: add login page") == "Added"

    def test_feature_prefix(self):
        assert _categorize("feature: new dark mode") == "Added"

    def test_fix_prefix(self):
        assert _categorize("fix: null pointer in handler") == "Fixed"

    def test_bug_prefix(self):
        assert _categorize("bug: fix broken redirect") == "Fixed"

    def test_refactor_prefix(self):
        assert _categorize("refactor: simplify auth flow") == "Changed"

    def test_remove_prefix(self):
        assert _categorize("remove: delete legacy endpoints") == "Removed"

    def test_docs_prefix(self):
        assert _categorize("docs: update API reference") == "Docs"

    def test_conventional_with_scope(self):
        assert _categorize("feat(api): add rate limiting") == "Added"

    def test_breaking_change(self):
        assert _categorize("remove!: drop Python 3.8 support") == "Removed"

    def test_keyword_in_title(self):
        assert _categorize("Update README with new examples") == "Changed"

    def test_label_overrides_title(self):
        assert _categorize("some change", labels=["bug", "fix"]) == "Fixed"

    def test_feature_label(self):
        assert _categorize("do thing", labels=["enhancement"]) == "Added"

    def test_unknown_falls_back_to_changed(self):
        assert _categorize("random commit message") == "Changed"

    def test_chore_is_changed(self):
        assert _categorize("chore: update dependencies") == "Changed"

    def test_perf_is_changed(self):
        assert _categorize("perf: optimize db queries") == "Changed"


# ---------------------------------------------------------------------------
# _clean_title
# ---------------------------------------------------------------------------

class TestCleanTitle:
    def test_strips_feat_prefix(self):
        assert _clean_title("feat: add login") == "add login"

    def test_strips_fix_with_scope(self):
        assert _clean_title("fix(auth): handle expired tokens") == "handle expired tokens"

    def test_no_prefix_unchanged(self):
        result = _clean_title("Update README with examples")
        assert "Update README" in result

    def test_strips_breaking_prefix(self):
        assert _clean_title("feat!: breaking API change") == "breaking API change"


# ---------------------------------------------------------------------------
# _build_sections
# ---------------------------------------------------------------------------

class TestBuildSections:
    def test_groups_by_category(self):
        entries = [
            {"category": "Added", "line": "new feature"},
            {"category": "Fixed", "line": "bug fix"},
            {"category": "Added", "line": "another feature"},
        ]
        sections = _build_sections(entries)
        assert len(sections["Added"]) == 2
        assert len(sections["Fixed"]) == 1

    def test_empty_entries(self):
        assert _build_sections([]) == {}


# ---------------------------------------------------------------------------
# generate_markdown
# ---------------------------------------------------------------------------

class TestGenerateMarkdown:
    def _entries(self):
        return [
            {"category": "Added", "line": "add rate limiting (abc1234)"},
            {"category": "Fixed", "line": "fix null pointer (def5678)"},
            {"category": "Changed", "line": "refactor auth flow (ghi9012)"},
        ]

    def test_contains_changelog_header(self):
        md = generate_markdown("myrepo", "v1.0", "HEAD", self._entries(), "2026-06-27")
        assert "# Changelog" in md

    def test_contains_unreleased_or_ref(self):
        md = generate_markdown("myrepo", "v1.0", "Unreleased", self._entries(), "2026-06-27")
        assert "[Unreleased]" in md

    def test_contains_added_section(self):
        md = generate_markdown("myrepo", "v1.0", "HEAD", self._entries(), "2026-06-27")
        assert "### Added" in md
        assert "add rate limiting" in md

    def test_contains_fixed_section(self):
        md = generate_markdown("myrepo", "v1.0", "HEAD", self._entries(), "2026-06-27")
        assert "### Fixed" in md

    def test_date_in_output(self):
        md = generate_markdown("myrepo", "v1.0", "HEAD", self._entries(), "2026-06-27")
        assert "2026-06-27" in md

    def test_no_duplicate_sections(self):
        entries = [
            {"category": "Changed", "line": "refactor a"},
            {"category": "Changed", "line": "refactor b"},
        ]
        md = generate_markdown("myrepo", "v1.0", "HEAD", entries, "2026-06-27")
        assert md.count("### Changed") == 1

    def test_empty_entries_message(self):
        md = generate_markdown("myrepo", "v1.0", "HEAD", [], "2026-06-27")
        assert "No changes found" in md

    def test_repo_name_in_output(self):
        md = generate_markdown("psf/requests", "v1.0", "HEAD", self._entries(), "2026-06-27")
        assert "psf/requests" in md
