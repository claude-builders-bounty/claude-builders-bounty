#!/usr/bin/env python3
"""Tests for generate-changelog script."""

import os
import shutil
import subprocess
import tempfile
import unittest

# Import target module
import generate_changelog


class TestParseCommit(unittest.TestCase):
    def test_conventional_added(self):
        cat, msg = generate_changelog.parse_commit_message("feat: add login page")
        self.assertEqual(cat, "Added")
        self.assertEqual(msg, "add login page")

    def test_conventional_fixed(self):
        cat, msg = generate_changelog.parse_commit_message("fix(auth): resolve token expiration bug")
        self.assertEqual(cat, "Fixed")
        self.assertEqual(msg, "resolve token expiration bug")

    def test_conventional_changed(self):
        cat, msg = generate_changelog.parse_commit_message("refactor: update routing logic")
        self.assertEqual(cat, "Changed")
        self.assertEqual(msg, "update routing logic")

    def test_conventional_removed(self):
        cat, msg = generate_changelog.parse_commit_message("deprecate: drop legacy api endpoint")
        self.assertEqual(cat, "Removed")
        self.assertEqual(msg, "drop legacy api endpoint")

    def test_keyword_added(self):
        cat, msg = generate_changelog.parse_commit_message("add new search filter")
        self.assertEqual(cat, "Added")
        self.assertEqual(msg, "add new search filter")

    def test_keyword_fixed(self):
        cat, msg = generate_changelog.parse_commit_message("fixed crash on startup")
        self.assertEqual(cat, "Fixed")
        self.assertEqual(msg, "fixed crash on startup")

    def test_keyword_removed(self):
        cat, msg = generate_changelog.parse_commit_message("remove obsolete test cases")
        self.assertEqual(cat, "Removed")
        self.assertEqual(msg, "remove obsolete test cases")

    def test_uncategorized_defaults_to_changed(self):
        cat, msg = generate_changelog.parse_commit_message("bump version to 1.2.0")
        self.assertEqual(cat, "Changed")
        self.assertEqual(msg, "bump version to 1.2.0")

    def test_merge_commits_ignored(self):
        cat, msg = generate_changelog.parse_commit_message("Merge pull request #42 from feature/foo")
        self.assertIsNone(cat)
        self.assertIsNone(msg)

    def test_empty_or_whitespace_message(self):
        cat, msg = generate_changelog.parse_commit_message("   ")
        self.assertIsNone(cat)
        self.assertIsNone(msg)


class TestFormatChangelog(unittest.TestCase):
    def test_format_empty_categories(self):
        commits_by_cat = {"Added": [], "Fixed": [], "Changed": [], "Removed": []}
        output = generate_changelog.format_markdown(commits_by_cat, tag_name="v1.0.0", date_str="2026-11-13")
        self.assertIn("## [v1.0.0] - 2026-11-13", output)
        self.assertIn("No changes recorded.", output)

    def test_format_with_entries(self):
        commits_by_cat = {
            "Added": [("1a2b3c4", "new cool feature")],
            "Fixed": [("5d6e7f8", "fix memory leak")],
            "Changed": [],
            "Removed": [("9a0b1c2", "remove legacy flag")],
        }
        output = generate_changelog.format_markdown(commits_by_cat, tag_name="Unreleased", date_str="2026-11-13")
        self.assertIn("## [Unreleased] - 2026-11-13", output)
        self.assertIn("### Added", output)
        self.assertIn("- new cool feature (1a2b3c4)", output)
        self.assertIn("### Fixed", output)
        self.assertIn("- fix memory leak (5d6e7f8)", output)
        self.assertNotIn("### Changed", output)
        self.assertIn("### Removed", output)
        self.assertIn("- remove legacy flag (9a0b1c2)", output)


class TestGitIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.run_git(["init"])
        self.run_git(["config", "user.name", "Test User"])
        self.run_git(["config", "user.email", "test@example.com"])

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def run_git(self, args):
        subprocess.run(["git"] + args, cwd=self.test_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def make_commit(self, msg, filename="file.txt"):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, "a") as f:
            f.write(msg + "\n")
        self.run_git(["add", filename])
        self.run_git(["commit", "-m", msg])

    def test_repo_with_no_tags(self):
        self.make_commit("feat: initial commit")
        self.make_commit("fix: quick patch")
        commits = generate_changelog.get_commits_since_last_tag(repo_path=self.test_dir)
        self.assertEqual(len(commits), 2)

    def test_repo_with_tag(self):
        self.make_commit("feat: initial release")
        self.run_git(["tag", "-a", "v1.0.0", "-m", "v1.0.0"])
        self.make_commit("feat: feature after tag")
        self.make_commit("fix: fix after tag")
        commits = generate_changelog.get_commits_since_last_tag(repo_path=self.test_dir)
        self.assertEqual(len(commits), 2)
        messages = [c[1] for c in commits]
        self.assertIn("feat: feature after tag", messages)
        self.assertIn("fix: fix after tag", messages)
        self.assertNotIn("feat: initial release", messages)

    def test_repo_with_no_commits_since_tag(self):
        self.make_commit("feat: initial release")
        self.run_git(["tag", "-a", "v1.0.0", "-m", "v1.0.0"])
        commits = generate_changelog.get_commits_since_last_tag(repo_path=self.test_dir)
        self.assertEqual(len(commits), 0)

    def test_repo_with_no_tag_flag_returns_all_commits(self):
        self.make_commit("feat: initial release")
        self.run_git(["tag", "-a", "v1.0.0", "-m", "v1.0.0"])
        self.make_commit("fix: post-release bugfix")
        # With default behavior, only commits after tag v1.0.0 are returned
        commits_default = generate_changelog.get_commits_since_last_tag(repo_path=self.test_dir)
        self.assertEqual(len(commits_default), 1)
        # With no_tag=True, full history is returned regardless of existing tags
        commits_no_tag = generate_changelog.get_commits_since_last_tag(repo_path=self.test_dir, no_tag=True)
        self.assertEqual(len(commits_no_tag), 2)

    def test_cli_execution_generates_file(self):
        self.make_commit("feat: add exciting widget")
        out_file = os.path.join(self.test_dir, "CHANGELOG.md")
        generate_changelog.generate_changelog(repo_path=self.test_dir, output_path=out_file)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file) as f:
            content = f.read()
        self.assertIn("### Added", content)
        self.assertIn("add exciting widget", content)

    def test_prepend_does_not_duplicate_header(self):
        self.make_commit("feat: initial release")
        out_file = os.path.join(self.test_dir, "CHANGELOG.md")
        with open(out_file, "w") as f:
            f.write("# Changelog\n\nSome older intro text.\n\n## [v0.1.0] - 2026-01-01\n\n### Added\n\n- old entry (abc1234)\n")
        self.make_commit("feat: brand new thing")
        generate_changelog.generate_changelog(repo_path=self.test_dir, output_path=out_file)
        with open(out_file) as f:
            content = f.read()
        self.assertEqual(content.count("# Changelog"), 1)
        self.assertIn("brand new thing", content)
        self.assertIn("Some older intro text", content)
        self.assertIn("old entry", content)

    def test_prepend_keeps_exact_header_once(self):
        self.make_commit("feat: first feature")
        out_file = os.path.join(self.test_dir, "CHANGELOG.md")
        generate_changelog.generate_changelog(repo_path=self.test_dir, output_path=out_file)
        self.make_commit("fix: second fix")
        generate_changelog.generate_changelog(repo_path=self.test_dir, output_path=out_file)
        with open(out_file) as f:
            content = f.read()
        self.assertEqual(content.count("# Changelog"), 1)
        self.assertIn("first feature", content)
        self.assertIn("second fix", content)


if __name__ == "__main__":
    unittest.main()
