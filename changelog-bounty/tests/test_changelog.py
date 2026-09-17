import subprocess
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from changelog import render  # noqa: E402


def run(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


class ChangelogTest(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        repo = Path(temp.name)
        run(repo, "init", "-q")
        run(repo, "config", "user.email", "test@example.com")
        run(repo, "config", "user.name", "Test")
        return temp, repo

    def commit(self, repo, subject):
        (repo / "file.txt").write_text(subject, encoding="utf-8")
        run(repo, "add", "file.txt")
        run(repo, "commit", "-qm", subject)

    def test_since_latest_tag_and_categories(self):
        temp, repo = self.make_repo()
        with temp:
            self.commit(repo, "feat: add export")
            run(repo, "tag", "v1.0.0")
            self.commit(repo, "fix: repair export")
            self.commit(repo, "remove: drop legacy flag")
            self.commit(repo, "refresh wording")
            output = repo / "CHANGELOG.md"
            text = render(repo, output)
            self.assertIn("since v1.0.0", text)
            self.assertIn("### Fixed\n- fix: repair export", text)
            self.assertIn("### Removed\n- remove: drop legacy flag", text)
            self.assertIn("### Changed\n- refresh wording", text)
            self.assertNotIn("add export", text.split("Unreleased", 1)[1].split("##", 1)[0])

    def test_no_tag_fallback(self):
        temp, repo = self.make_repo()
        with temp:
            self.commit(repo, "feat: add first item")
            text = render(repo, repo / "CHANGELOG.md")
            self.assertIn("all commits; no git tag found", text)
            self.assertIn("### Added\n- feat: add first item", text)


if __name__ == "__main__":
    unittest.main()
