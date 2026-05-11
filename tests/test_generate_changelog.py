import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "generate-changelog"
    / "generate_changelog.py"
)

spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT_PATH)
changelog = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = changelog
spec.loader.exec_module(changelog)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, text=True, stdout=subprocess.PIPE)


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_conventional_and_plain_commits(self):
        cases = {
            "feat: add billing dashboard": "Added",
            "fix: repair login redirect": "Fixed",
            "refactor: update user repository": "Changed",
            "remove unused webhook secret": "Removed",
        }

        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                commit = changelog.Commit("abc123", subject, "")
                self.assertEqual(changelog.categorize(commit), expected)

    def test_generates_changelog_since_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")

            (repo / "app.txt").write_text("initial\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "chore: initial release")
            git(repo, "tag", "v1.0.0")

            (repo / "app.txt").write_text("initial\nfeature\n", encoding="utf-8")
            git(repo, "commit", "-am", "feat: add import flow")

            (repo / "app.txt").write_text("initial\nfeature\nfix\n", encoding="utf-8")
            git(repo, "commit", "-am", "fix: handle empty csv")

            tag = changelog.last_tag(repo)
            commits = changelog.commits_since(repo, tag)
            rendered = changelog.render_changelog(commits, tag)

            self.assertEqual(tag, "v1.0.0")
            self.assertEqual(len(commits), 2)
            self.assertIn("### Added", rendered)
            self.assertIn("Add import flow", rendered)
            self.assertIn("### Fixed", rendered)
            self.assertIn("Handle empty csv", rendered)


if __name__ == "__main__":
    unittest.main()
