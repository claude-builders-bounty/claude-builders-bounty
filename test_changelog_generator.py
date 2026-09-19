import os
import subprocess
import tempfile
import unittest


SCRIPT_PATH = os.path.join(os.getcwd(), "changelog.sh")


def init_repo(path: str):
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=path, check=True)


class ChangelogScriptTest(unittest.TestCase):
    def test_generates_changelog_since_tag(self):
        tempdir = tempfile.mkdtemp()
        init_repo(tempdir)

        file_path = os.path.join(tempdir, "file.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("initial")
        subprocess.run(["git", "add", "file.txt"], cwd=tempdir, check=True)
        subprocess.run(["git", "commit", "-m", "Add initial file"], cwd=tempdir, check=True)
        subprocess.run(["git", "tag", "v0.1.0"], cwd=tempdir, check=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write("\nchange")
        subprocess.run(["git", "add", "file.txt"], cwd=tempdir, check=True)
        subprocess.run(["git", "commit", "-m", "Fix typo in docs"], cwd=tempdir, check=True)

        subprocess.run(["bash", SCRIPT_PATH], cwd=tempdir, check=True)

        changelog_path = os.path.join(tempdir, "CHANGELOG.md")
        with open(changelog_path, "r", encoding="utf-8") as f:
            changelog = f.read()

        self.assertIn("## Unreleased (since v0.1.0)", changelog)
        self.assertIn("### Added", changelog)
        self.assertIn("### Fixed", changelog)
        self.assertIn("- None", changelog)  # Added and others are at least populated
        self.assertIn("Fix typo in docs", changelog)

    def test_no_tag_uses_all_commits(self):
        tempdir = tempfile.mkdtemp()
        init_repo(tempdir)

        path = os.path.join(tempdir, "main.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write("print('hi')\n")
        subprocess.run(["git", "add", "main.py"], cwd=tempdir, check=True)
        subprocess.run(["git", "commit", "-m", "Add greeting script"], cwd=tempdir, check=True)

        with open(path, "a", encoding="utf-8") as f:
            f.write("print('bye')\n")
        subprocess.run(["git", "add", "main.py"], cwd=tempdir, check=True)
        subprocess.run(["git", "commit", "-m", "Remove noisy log"], cwd=tempdir, check=True)

        subprocess.run(["bash", SCRIPT_PATH], cwd=tempdir, check=True)

        changelog_path = os.path.join(tempdir, "CHANGELOG.md")
        with open(changelog_path, "r", encoding="utf-8") as f:
            changelog = f.read()

        self.assertIn("## Unreleased (since start)", changelog)
        # Both commits should be present under their categories
        self.assertIn("Add greeting script", changelog)
        self.assertIn("Remove noisy log", changelog)
        self.assertIn("### Added", changelog)
        self.assertIn("### Removed", changelog)


if __name__ == "__main__":
    unittest.main()
