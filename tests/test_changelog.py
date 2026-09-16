import os
import shutil
import tempfile
import unittest
import subprocess
import sys

# Make the skill module importable regardless of where tests run from
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "skills", "generate-changelog"))

from generate_changelog import categorize_commit, build_changelog_section, generate_full_changelog


class TestGenerateChangelog(unittest.TestCase):

    def test_categorize_commit(self):
        self.assertEqual(categorize_commit("feat: add user authentication")[0], "Added")
        self.assertEqual(categorize_commit("fix(api): resolve timeout on login")[0], "Fixed")
        self.assertEqual(categorize_commit("refactor: clean up database query")[0], "Changed")
        self.assertEqual(categorize_commit("docs: update README with setup instructions")[0], "Changed")
        self.assertEqual(categorize_commit("remove: drop legacy v1 endpoints")[0], "Removed")
        self.assertEqual(categorize_commit("security: patch SQL injection vulnerability")[0], "Security")

    def test_build_changelog_section(self):
        commits = [
            {"hash": "abc1234", "author": "Alice", "date": "2026-03-27", "subject": "feat: add dark mode"},
            {"hash": "def5678", "author": "Bob", "date": "2026-03-27", "subject": "fix: resolve crash on startup"},
        ]
        section = build_changelog_section("1.0.0", commits, release_date="2026-03-27")
        self.assertIn("## [1.0.0] - 2026-03-27", section)
        self.assertIn("### Added", section)
        self.assertIn("- Add dark mode (`abc1234`)", section)
        self.assertIn("### Fixed", section)
        self.assertIn("- Resolve crash on startup (`def5678`)", section)

    def test_git_integration(self):
        tmp_dir = tempfile.mkdtemp()
        try:
            # Init git repo
            subprocess.run(["git", "init"], cwd=tmp_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            subprocess.run(["git", "config", "user.name", "Tester"], cwd=tmp_dir, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_dir, check=True)

            # Create commit 1
            f1 = os.path.join(tmp_dir, "file1.txt")
            with open(f1, "w") as f: f.write("hello")
            subprocess.run(["git", "add", "."], cwd=tmp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "feat: initial commit with file1"], cwd=tmp_dir, check=True)
            subprocess.run(["git", "tag", "v0.1.0"], cwd=tmp_dir, check=True)

            # Create commit 2
            f2 = os.path.join(tmp_dir, "file2.txt")
            with open(f2, "w") as f: f.write("world")
            subprocess.run(["git", "add", "."], cwd=tmp_dir, check=True)
            subprocess.run(["git", "commit", "-m", "fix: resolve file2 loading bug"], cwd=tmp_dir, check=True)

            # Generate changelog
            out_file, count = generate_full_changelog(version="v0.2.0", cwd=tmp_dir)
            self.assertEqual(count, 1)

            with open(out_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("## [v0.2.0]", content)
            self.assertIn("### Fixed", content)
            self.assertIn("Resolve file2 loading bug", content)

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
