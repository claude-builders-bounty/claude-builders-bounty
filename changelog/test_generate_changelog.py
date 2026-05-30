#!/usr/bin/env python3
"""Tests for generate_changelog.py"""

import json
import os
import subprocess
import tempfile
import unittest

from generate_changelog import (
    CATEGORY_MAP,
    CONVENTIONAL_RE,
    categorize_commit,
    generate_changelog,
    get_commits_since,
    get_last_tag,
    group_commits_by_category,
    run_git,
)


class TestCategorizeCommit(unittest.TestCase):
    """Test the categorize_commit function."""

    def test_feat(self):
        cat, desc = categorize_commit("feat: add user authentication")
        self.assertEqual(cat, "Added")
        self.assertIn("add user authentication", desc)

    def test_feat_with_scope(self):
        cat, desc = categorize_commit("feat(auth): add OAuth2 support")
        self.assertEqual(cat, "Added")
        self.assertIn("**auth**", desc)
        self.assertIn("add OAuth2 support", desc)

    def test_feat_breaking(self):
        cat, desc = categorize_commit("feat(api)!: change response format")
        self.assertEqual(cat, "Added")
        self.assertIn("**BREAKING**", desc)

    def test_fix(self):
        cat, desc = categorize_commit("fix: resolve login crash on empty password")
        self.assertEqual(cat, "Fixed")
        self.assertIn("resolve login crash on empty password", desc)

    def test_bugfix(self):
        cat, desc = categorize_commit("bugfix: patch memory leak in worker")
        self.assertEqual(cat, "Fixed")

    def test_refactor(self):
        cat, desc = categorize_commit("refactor: simplify database query builder")
        self.assertEqual(cat, "Changed")

    def test_chore(self):
        cat, desc = categorize_commit("chore: update dependencies")
        self.assertEqual(cat, "Changed")

    def test_perf(self):
        cat, desc = categorize_commit("perf: optimize render loop")
        self.assertEqual(cat, "Changed")

    def test_remove(self):
        cat, desc = categorize_commit("remove: delete deprecated API endpoint")
        self.assertEqual(cat, "Removed")

    def test_revert(self):
        cat, desc = categorize_commit("revert: undo previous commit")
        self.assertEqual(cat, "Removed")

    def test_security(self):
        cat, desc = categorize_commit("security: patch XSS vulnerability")
        self.assertEqual(cat, "Security")

    def test_keyword_fallback_add(self):
        cat, desc = categorize_commit("Add new feature for users")
        self.assertEqual(cat, "Added")

    def test_keyword_fallback_fix(self):
        cat, desc = categorize_commit("Fixed bug in payment processing")
        self.assertEqual(cat, "Fixed")

    def test_keyword_fallback_change(self):
        cat, desc = categorize_commit("Update README with better docs")
        self.assertEqual(cat, "Changed")

    def test_keyword_fallback_remove(self):
        cat, desc = categorize_commit("Remove unused import statements")
        self.assertEqual(cat, "Removed")

    def test_default_fallback(self):
        cat, desc = categorize_commit("Something completely unrelated")
        self.assertEqual(cat, "Changed")
        self.assertEqual(desc, "Something completely unrelated")

    def test_docs(self):
        cat, desc = categorize_commit("docs: update API documentation")
        self.assertEqual(cat, "Changed")


class TestGroupCommits(unittest.TestCase):
    """Test the group_commits_by_category function."""

    def test_grouping(self):
        commits = [
            {"sha": "a" * 40, "subject": "feat: add feature", "author": "Alice", "date": "2026-01-01T00:00:00Z"},
            {"sha": "b" * 40, "subject": "fix: patch bug", "author": "Bob", "date": "2026-01-02T00:00:00Z"},
            {"sha": "c" * 40, "subject": "remove: delete old code", "author": "Carol", "date": "2026-01-03T00:00:00Z"},
        ]
        grouped = group_commits_by_category(commits)
        self.assertEqual(len(grouped["Added"]), 1)
        self.assertEqual(len(grouped["Fixed"]), 1)
        self.assertEqual(len(grouped["Removed"]), 1)
        self.assertEqual(len(grouped["Changed"]), 0)

    def test_empty_commits(self):
        grouped = group_commits_by_category([])
        for cat in grouped.values():
            self.assertEqual(len(cat), 0)


class TestGenerateChangelog(unittest.TestCase):
    """Test the generate_changelog output function."""

    def test_markdown_output(self):
        grouped = {
            "Added": [{"description": "new feature", "sha": "a" * 40, "author": "Alice", "date": "2026-01-01T00:00:00Z"}],
            "Fixed": [],
            "Changed": [],
            "Removed": [],
            "Security": [],
        }
        output = generate_changelog(grouped, version="1.0.0")
        self.assertIn("## 1.0.0", output)
        self.assertIn("### Added", output)
        self.assertIn("new feature", output)
        self.assertNotIn("### Fixed", output)  # empty categories are omitted
        self.assertIn("1 commits", output)

    def test_since_ref(self):
        grouped = {
            "Added": [{"description": "new feature", "sha": "a" * 40, "author": "Alice", "date": "2026-01-01T00:00:00Z"}],
            "Fixed": [],
            "Changed": [],
            "Removed": [],
            "Security": [],
        }
        output = generate_changelog(grouped, since_ref="v0.9.0")
        self.assertIn("v0.9.0", output)


class TestGitIntegration(unittest.TestCase):
    """Integration tests with a real git repository."""

    def setUp(self):
        """Create a temporary git repo with test commits."""
        self.tmpdir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.tmpdir], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.tmpdir, "config", "user.email", "test@test.com"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.tmpdir, "config", "user.name", "Test User"], capture_output=True, check=True)

        # Create initial commit
        filepath = os.path.join(self.tmpdir, "README.md")
        with open(filepath, "w") as f:
            f.write("# Test\n")
        subprocess.run(["git", "-C", self.tmpdir, "add", "."], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.tmpdir, "commit", "-m", "chore: initial commit"], capture_output=True, check=True)

        # Tag the initial commit
        subprocess.run(["git", "-C", self.tmpdir, "tag", "v0.1.0"], capture_output=True, check=True)

        # Add more commits
        for msg in [
            "feat: add user model",
            "fix: resolve null pointer in auth",
            "feat(api): add pagination support",
            "refactor: clean up service layer",
            "remove: delete legacy migration script",
        ]:
            with open(filepath, "a") as f:
                f.write(f"{msg}\n")
            subprocess.run(["git", "-C", self.tmpdir, "add", "."], capture_output=True, check=True)
            subprocess.run(["git", "-C", self.tmpdir, "commit", "-m", msg], capture_output=True, check=True)

    def tearDown(self):
        """Clean up the temporary directory."""
        subprocess.run(["rm", "-rf", self.tmpdir], capture_output=True)

    def test_get_last_tag(self):
        tag = get_last_tag(repo_path=self.tmpdir)
        self.assertEqual(tag, "v0.1.0")

    def test_get_commits_since_tag(self):
        commits = get_commits_since(since_ref="v0.1.0", repo_path=self.tmpdir)
        self.assertEqual(len(commits), 5)
        # Commits are in reverse chronological order
        self.assertEqual(commits[0]["subject"], "remove: delete legacy migration script")

    def test_get_all_commits(self):
        commits = get_commits_since(since_ref=None, repo_path=self.tmpdir)
        self.assertEqual(len(commits), 6)  # 1 initial + 5 new

    def test_categorization_integration(self):
        commits = get_commits_since(since_ref="v0.1.0", repo_path=self.tmpdir)
        grouped = group_commits_by_category(commits)
        self.assertEqual(len(grouped["Added"]), 2)  # feat: add user model, feat(api): add pagination
        self.assertEqual(len(grouped["Fixed"]), 1)  # fix: resolve null pointer
        self.assertEqual(len(grouped["Changed"]), 1)  # refactor: clean up service layer
        self.assertEqual(len(grouped["Removed"]), 1)  # remove: delete legacy migration script

    def test_full_dry_run(self):
        """Test the full pipeline via command line."""
        result = subprocess.run(
            ["python3", "generate_changelog.py", "--repo", self.tmpdir, "--dry-run"],
            capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("### Added", result.stdout)
        self.assertIn("### Fixed", result.stdout)
        self.assertIn("### Removed", result.stdout)

    def test_json_output(self):
        """Test JSON output mode."""
        result = subprocess.run(
            ["python3", "generate_changelog.py", "--repo", self.tmpdir, "--json"],
            capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("Added", data["categories"])
        self.assertEqual(len(data["categories"]["Added"]), 2)

    def test_output_file(self):
        """Test writing to a file."""
        output_file = os.path.join(self.tmpdir, "CHANGELOG.md")
        result = subprocess.run(
            ["python3", "generate_changelog.py", "--repo", self.tmpdir, "--output", output_file],
            capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_file))
        with open(output_file) as f:
            content = f.read()
        self.assertIn("# Changelog", content)
        self.assertIn("### Added", content)


if __name__ == "__main__":
    unittest.main()
