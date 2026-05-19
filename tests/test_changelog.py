import unittest
import os
import subprocess
import tempfile
import shutil

class TestChangelogGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_dir)
        
        subprocess.run(["git", "init"], cwd=self.repo_dir, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_dir)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_dir)
        
        with open(os.path.join(self.repo_dir, "file.txt"), "w") as f:
            f.write("hello")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir)
        subprocess.run(["git", "commit", "-m", "feat: initial commit"], cwd=self.repo_dir)
        subprocess.run(["git", "tag", "v0.1.0"], cwd=self.repo_dir)
        
        with open(os.path.join(self.repo_dir, "file.txt"), "a") as f:
            f.write("world")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir)
        subprocess.run(["git", "commit", "-m", "fix: fix a bug"], cwd=self.repo_dir)
        
        with open(os.path.join(self.repo_dir, "README.md"), "w") as f:
            f.write("# Docs")
        subprocess.run(["git", "add", "."], cwd=self.repo_dir)
        subprocess.run(["git", "commit", "-m", "docs: update readme"], cwd=self.repo_dir)

        self.script_path = os.path.abspath("generate_changelog.py")
        shutil.copy(self.script_path, os.path.join(self.repo_dir, "generate_changelog.py"))

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_changelog_generation(self):
        result = subprocess.run(["python3", "generate_changelog.py"], cwd=self.repo_dir, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        
        changelog_path = os.path.join(self.repo_dir, "CHANGELOG.md")
        self.assertTrue(os.path.exists(changelog_path))
        
        with open(changelog_path, "r") as f:
            content = f.read()
            
        self.assertIn("### Fixed", content)
        self.assertIn("- fix: fix a bug", content)
        self.assertIn("### Docs", content)
        self.assertIn("- docs: update readme", content)
        self.assertNotIn("feat: initial commit", content)

if __name__ == "__main__":
    unittest.main()
