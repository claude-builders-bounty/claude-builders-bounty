#!/usr/bin/env python3
"""Tests for changelog.py. Run: python3 tests/test_changelog.py"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import changelog as cg  # noqa: E402

ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_COUNT": "2",
    "GIT_CONFIG_KEY_0": "commit.gpgsign", "GIT_CONFIG_VALUE_0": "false",
    "GIT_CONFIG_KEY_1": "tag.gpgsign", "GIT_CONFIG_VALUE_1": "false",
}


def sh(cwd, *args):
    subprocess.run(args, cwd=cwd, env=ENV, check=True,
                   capture_output=True, text=True)


def commit(repo, message, files):
    """files: {path: content} to write, or {path: None} to delete."""
    for path, content in files.items():
        full = os.path.join(repo, path)
        if content is None:
            os.remove(full)
        else:
            os.makedirs(os.path.dirname(full), exist_ok=True) \
                if os.path.dirname(full) else None
            with open(full, "w") as fh:
                fh.write(content)
    sh(repo, "git", "add", "-A")
    sh(repo, "git", "commit", "-q", "-m", message)


def make_repo():
    repo = tempfile.mkdtemp(prefix="changelog-test-")
    sh(repo, "git", "init", "-q", "-b", "main")
    # Commit + tag BEFORE the range we generate for.
    commit(repo, "feat: initial import", {"app.py": "v0\n", "old.py": "x\n"})
    sh(repo, "git", "tag", "v1.0.0")
    # Commits AFTER the tag, one per category plus edge cases.
    commit(repo, "feat: add user login", {"login.py": "x\n"})
    commit(repo, "fix(auth): correct token refresh", {"login.py": "y\n"})
    commit(repo, "docs: update installation guide", {"README.md": "hi\n"})
    commit(repo, "remove legacy parser", {"old.py": None})
    commit(repo, "fix: remove broken cache layer", {"login.py": "z\n"})
    commit(repo, "Bump dependency versions", {"README.md": "hi2\n"})
    return repo


class CategorizeTests(unittest.TestCase):
    def test_conventional_types(self):
        self.assertEqual(cg.categorize("feat: add export", [])[0], "Added")
        self.assertEqual(cg.categorize("fix: crash on save", [])[0], "Fixed")
        self.assertEqual(cg.categorize("refactor: split store", [])[0],
                         "Changed")
        self.assertEqual(cg.categorize("chore: bump deps", [])[0], "Changed")

    def test_removal_verb_beats_fix_type(self):
        self.assertEqual(cg.categorize("fix: remove broken cache", [])[0],
                         "Removed")
        self.assertEqual(cg.categorize("Drop Python 2 support", [])[0],
                         "Removed")

    def test_keyword_fallback_and_scope(self):
        cat, text, scope = cg.categorize("Add dark mode", [])
        self.assertEqual((cat, text), ("Added", "Add dark mode"))
        cat, text, scope = cg.categorize("feat(ui): add dark mode", [])
        self.assertEqual((cat, text, scope),
                         ("Added", "Add dark mode", "ui"))

    def test_pure_deletion_commit(self):
        self.assertEqual(cg.categorize("Clean up workspace", ["D"])[0],
                         "Removed")
        self.assertEqual(cg.categorize("Clean up workspace", ["D", "M"])[0],
                         "Changed")


class RepoIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = make_repo()
        cls.section = cg.build_section(cls.repo, None, "HEAD",
                                       "1.1.0", "2026-11-09")

    def test_last_tag_is_used(self):
        # "Initial import" was committed before the tag: excluded.
        self.assertEqual(cg.last_tag(self.repo), "v1.0.0")
        self.assertNotIn("Initial import", self.section)

    def test_title_and_categories_present(self):
        self.assertIn("## [1.1.0] - 2026-11-09", self.section)
        for cat in ("### Added", "### Fixed", "### Changed", "### Removed"):
            self.assertIn(cat, self.section)

    def test_entries_land_in_the_right_category(self):
        added = self.section.split("### Added")[1].split("###")[0]
        fixed = self.section.split("### Fixed")[1].split("###")[0]
        changed = self.section.split("### Changed")[1].split("###")[0]
        removed = self.section.split("### Removed")[1]
        self.assertIn("Add user login", added)
        self.assertIn("**auth:** Correct token refresh", fixed)
        self.assertIn("Update installation guide", changed)
        self.assertIn("Bump dependency versions", changed)
        self.assertIn("Remove legacy parser", removed)
        self.assertIn("Remove broken cache layer", removed)
        self.assertNotIn("Remove broken cache layer", fixed)

    def test_category_order(self):
        order = [self.section.index(f"### {c}") for c in cg.CATEGORIES]
        self.assertEqual(order, sorted(order))

    def test_explicit_range(self):
        section = cg.build_section(self.repo, "v1.0.0", "HEAD",
                                   "Unreleased", "2026-11-09")
        self.assertIn("Add user login", section)

    def test_prepend_creates_and_inserts(self):
        target = os.path.join(self.repo, "CHANGELOG.md")
        cg.prepend_to_file(target, self.section)
        with open(target) as fh:
            first = fh.read()
        self.assertTrue(first.startswith("# Changelog"))
        self.assertIn("## [1.1.0]", first)
        older = "## [1.0.0] - 2026-01-01\n\n### Added\n\n- Initial import\n"
        with open(target, "w") as fh:
            fh.write("# Changelog\n\n" + older)
        cg.prepend_to_file(target, self.section)
        with open(target) as fh:
            merged = fh.read()
        self.assertLess(merged.index("## [1.1.0]"), merged.index("## [1.0.0]"))

    def test_cli_end_to_end(self):
        proc = subprocess.run(
            [sys.executable,
             os.path.join(os.path.dirname(__file__), "..", "changelog.py"),
             "--repo", self.repo, "--version", "9.9.9"],
            capture_output=True, text=True, env=ENV)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("## [9.9.9]", proc.stdout)


class NoTagRepoTests(unittest.TestCase):
    def test_repo_without_tags_uses_all_commits(self):
        repo = tempfile.mkdtemp(prefix="changelog-notag-")
        sh(repo, "git", "init", "-q", "-b", "main")
        commit(repo, "feat: first feature", {"a.py": "1\n"})
        self.assertIsNone(cg.last_tag(repo))
        section = cg.build_section(repo, None, "HEAD",
                                   "Unreleased", "2026-11-09")
        self.assertIn("First feature", section)


if __name__ == "__main__":
    unittest.main(verbosity=2)
