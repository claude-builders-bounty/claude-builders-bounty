"""Tests for CHANGELOG generator skill"""
import pytest
from changelog_generator import parse_commits, categorize_commit, generate_changelog

class TestChangelogGenerator:
    def test_parse_commits_empty(self):
        commits = parse_commits([])
        assert commits == []

    def test_categorize_fix_commit(self):
        cat = categorize_commit("fix: resolve login bug")
        assert cat == "Fixed"

    def test_categorize_feat_commit(self):
        cat = categorize_commit("feat: add dark mode")
        assert cat == "Added"

    def test_generate_changelog_structure(self):
        commits = [{"message": "feat: new feature", "hash": "abc123"}]
        output = generate_changelog(commits, "v1.0.0")
        assert "v1.0.0" in output
        assert "new feature" in output

    def test_generate_changelog_multiple_categories(self):
        commits = [
            {"message": "feat: add export", "hash": "a1"},
            {"message": "fix: typo", "hash": "b2"},
        ]
        output = generate_changelog(commits, "v2.0.0")
        assert "Added" in output
        assert "Fixed" in output
