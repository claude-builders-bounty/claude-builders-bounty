#!/usr/bin/env python3
import sys
import os
import unittest

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from generate_changelog import categorize_commit, generate_section

class TestGenerateChangelog(unittest.TestCase):
    
    def test_categorize_commit_added(self):
        added_commits = [
            "feat: Add destructive command guard hook",
            "feat(auth): add user registration",
            "Added support for Windows 11",
            "Create new pipeline",
            "Introduce new layout feature"
        ]
        for msg in added_commits:
            self.assertEqual(categorize_commit(msg), 'Added', f"Failed for: {msg}")
            
    def test_categorize_commit_fixed(self):
        fixed_commits = [
            "fix: Resolve index out of bounds in loop",
            "fix(ui): Fix color contrast on dark mode",
            "Bugfix for remote push error",
            "Resolved security vulnerability in parser",
            "Patch memory leak in session manager"
        ]
        for msg in fixed_commits:
            self.assertEqual(categorize_commit(msg), 'Fixed', f"Failed for: {msg}")
            
    def test_categorize_commit_removed(self):
        removed_commits = [
            "remove deprecated config options",
            "Delete unused assets",
            "Removed backup system"
        ]
        for msg in removed_commits:
            self.assertEqual(categorize_commit(msg), 'Removed', f"Failed for: {msg}")
            
    def test_categorize_commit_changed(self):
        changed_commits = [
            "update readme structure",
            "refactor core authentication logic",
            "Style changes in profile page",
            "git status check updates"
        ]
        for msg in changed_commits:
            self.assertEqual(categorize_commit(msg), 'Changed', f"Failed for: {msg}")
            
    def test_generate_section(self):
        commits = [
            {'hash': 'a1b2c3d', 'subject': 'feat: Add hook', 'date': '2026-06-25'},
            {'hash': 'e5f6g7h', 'subject': 'fix: Patch leak', 'date': '2026-06-25'}
        ]
        section = generate_section(commits)
        self.assertIn("### Added", section)
        self.assertIn("- feat: Add hook (a1b2c3d)", section)
        self.assertIn("### Fixed", section)
        self.assertIn("- fix: Patch leak (e5f6g7h)", section)

if __name__ == '__main__':
    unittest.main()
