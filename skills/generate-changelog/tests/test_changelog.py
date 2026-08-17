"""
Unit and integration tests for generate_changelog.py
"""

import unittest
import os
import sys
import tempfile
import shutil
import subprocess

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generate_changelog import (
    categorize_commit,
    generate_markdown,
    build_full_changelog,
    get_commits,
    get_latest_tag
)

class TestChangelogGenerator(unittest.TestCase):

    def test_categorize_conventional_commits(self):
        cat1, desc1 = categorize_commit("feat(auth): add OAuth2 login with GitHub")
        self.assertEqual(cat1, "Added")
        self.assertEqual(desc1, "**auth**: add OAuth2 login with GitHub")

        cat2, desc2 = categorize_commit("fix(api): resolve memory leak in websocket handler")
        self.assertEqual(cat2, "Fixed")
        self.assertEqual(desc2, "**api**: resolve memory leak in websocket handler")

        cat3, desc3 = categorize_commit("perf(db): optimize SQL queries with composite index")
        self.assertEqual(cat3, "Performance")

        cat4, desc4 = categorize_commit("security(jwt): sanitize expired token headers")
        self.assertEqual(cat4, "Security")

        cat5, desc5 = categorize_commit("chore: bump dependencies to latest stable")
        self.assertEqual(cat5, "Changed")

        cat6, desc6 = categorize_commit("refactor(core): simplify state machine")
        self.assertEqual(cat6, "Changed")

    def test_markdown_generation(self):
        commits = [
            {"hash": "a1b2c3d4e5f6", "short_hash": "a1b2c3d", "subject": "feat(ui): add dark mode switch", "author": "Alice", "date": "2026-08-16"},
            {"hash": "f6e5d4c3b2a1", "short_hash": "f6e5d4c", "subject": "fix: correct calculation typo in tax ledger", "author": "Bob", "date": "2026-08-16"},
            {"hash": "112233445566", "short_hash": "1122334", "subject": "perf: reduce bundle size by 35%", "author": "Charlie", "date": "2026-08-16"}
        ]

        md = generate_markdown(commits, version_title="v1.0.0", release_date="2026-08-16")
        self.assertIn("## [v1.0.0] - 2026-08-16", md)
        self.assertIn("### Added", md)
        self.assertIn("- **ui**: add dark mode switch ([`a1b2c3d`])", md)
        self.assertIn("### Fixed", md)
        self.assertIn("- correct calculation typo in tax ledger ([`f6e5d4c`])", md)
        self.assertIn("### Performance", md)
        self.assertIn("- reduce bundle size by 35% ([`1122334`])", md)

    def test_build_full_changelog_prepending(self):
        new_sec = "## [v1.1.0] - 2026-08-16\n\n### Added\n- new cool feature ([`1234567`])\n"
        existing = "# Changelog\n\nAll notable changes...\n\n## [v1.0.0] - 2026-08-01\n\n### Added\n- initial release\n"

        merged = build_full_changelog(new_sec, existing)
        self.assertTrue(merged.startswith("# Changelog"))
        self.assertIn("## [v1.1.0] - 2026-08-16", merged)
        self.assertIn("## [v1.0.0] - 2026-08-01", merged)
        # Verify v1.1.0 comes before v1.0.0
        pos_11 = merged.find("## [v1.1.0]")
        pos_10 = merged.find("## [v1.0.0]")
        self.assertLess(pos_11, pos_10)

    def test_git_integration_in_temp_repo(self):
        temp_dir = tempfile.mkdtemp()
        try:
            # Init git repo
            subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=temp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, check=True)

            # Create commit 1
            with open(os.path.join(temp_dir, "file1.txt"), "w") as f:
                f.write("hello")
            subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "feat: initial commit with basic setup"], cwd=temp_dir, check=True)
            subprocess.run(["git", "tag", "v0.1.0"], cwd=temp_dir, check=True)

            # Create commit 2
            with open(os.path.join(temp_dir, "file2.txt"), "w") as f:
                f.write("world")
            subprocess.run(["git", "add", "."], cwd=temp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "fix(core): handle null pointer in parser"], cwd=temp_dir, check=True)

            # Verify latest tag
            latest_tag = get_latest_tag(cwd=temp_dir)
            self.assertEqual(latest_tag, "v0.1.0")

            # Verify commits since tag
            commits = get_commits(since_ref="v0.1.0", cwd=temp_dir)
            self.assertEqual(len(commits), 1)
            self.assertIn("fix(core): handle null pointer in parser", commits[0]["subject"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main(verbosity=2)
