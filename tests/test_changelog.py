"""
Unit tests for changelog generator.
"""

import os
import subprocess
import tempfile
import unittest


class TestChangelogGenerator(unittest.TestCase):
    def setUp(self):
        self.script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "changelog.sh")
        )

    def test_non_git_directory_fails(self):
        with tempfile.TemporaryDirectory() as non_git_dir:
            result = subprocess.run(
                ["bash", self.script_path],
                cwd=non_git_dir,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not a git repository", result.stderr.lower())

    def test_conventional_commits_categorization(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            # Init repo
            subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.email", "user@test.com"], cwd=repo_dir, check=True)

            # Create test commits
            with open(os.path.join(repo_dir, "f1.txt"), "w") as f:
                f.write("feat")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "feat(api): add webhook events"], cwd=repo_dir, check=True)

            with open(os.path.join(repo_dir, "f2.txt"), "w") as f:
                f.write("fix")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "fix: handle null pointer in parser"], cwd=repo_dir, check=True)

            with open(os.path.join(repo_dir, "f3.txt"), "w") as f:
                f.write("docs")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "docs: update integration guide"], cwd=repo_dir, check=True)

            with open(os.path.join(repo_dir, "f4.txt"), "w") as f:
                f.write("remove")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "remove: drop legacy python 2 support"], cwd=repo_dir, check=True)

            # Run script
            output_file = os.path.join(repo_dir, "CHANGELOG.md")
            res = subprocess.run(
                ["bash", self.script_path, "-o", output_file],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Changelog", content)
            self.assertIn("### Added", content)
            self.assertIn("add webhook events", content)
            self.assertIn("### Fixed", content)
            self.assertIn("handle null pointer in parser", content)
            self.assertIn("### Changed", content)
            self.assertIn("update integration guide", content)
            self.assertIn("### Removed", content)
            self.assertIn("drop legacy python 2 support", content)

    def test_git_tag_range_and_merge_commit_filtering(self):
        with tempfile.TemporaryDirectory() as repo_dir:
            subprocess.run(["git", "init", "-b", "main"], cwd=repo_dir, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.email", "user@test.com"], cwd=repo_dir, check=True)

            # v1.0.0
            with open(os.path.join(repo_dir, "f1.txt"), "w") as f:
                f.write("v1")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "feat: initial release"], cwd=repo_dir, check=True)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=repo_dir, check=True)

            # v1.1.0 changes
            with open(os.path.join(repo_dir, "f2.txt"), "w") as f:
                f.write("v1.1")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "feat: add oauth provider"], cwd=repo_dir, check=True)

            # Merge commit
            subprocess.run(["git", "checkout", "-b", "feat-branch"], cwd=repo_dir, check=True, capture_output=True)
            with open(os.path.join(repo_dir, "f3.txt"), "w") as f:
                f.write("branch")
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            subprocess.run(["git", "commit", "-m", "chore: branch commit"], cwd=repo_dir, check=True)
            subprocess.run(["git", "checkout", "main"], cwd=repo_dir, check=True, capture_output=True)
            subprocess.run(["git", "merge", "--no-ff", "feat-branch", "-m", "Merge branch 'feat-branch' into main"], cwd=repo_dir, check=True, capture_output=True)

            output_file = os.path.join(repo_dir, "CHANGELOG.md")
            res = subprocess.run(
                ["bash", self.script_path, "-v", "v1.1.0", "-o", output_file],
                cwd=repo_dir,
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("## [v1.1.0]", content)
            self.assertIn("add oauth provider", content)
            self.assertNotIn("Merge branch", content)


if __name__ == "__main__":
    unittest.main()
