import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "generate_changelog.py"


def run(command, cwd):
    return subprocess.run(command, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def commit(repo, message):
    path = repo / "app.txt"
    path.write_text(path.read_text(encoding="utf-8") + f"{message}\n", encoding="utf-8")
    run(["git", "add", "app.txt"], repo)
    run(["git", "commit", "-qm", message], repo)


class GenerateChangelogTest(unittest.TestCase):
    def test_generates_changelog_from_commits_after_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            run(["git", "init", "-q"], repo)
            run(["git", "config", "user.email", "test@example.com"], repo)
            run(["git", "config", "user.name", "Changelog Test"], repo)

            (repo / "app.txt").write_text("base\n", encoding="utf-8")
            run(["git", "add", "app.txt"], repo)
            run(["git", "commit", "-qm", "chore: initial release"], repo)
            run(["git", "tag", "v1.0.0"], repo)

            commit(repo, "feat(ui): add export button")
            commit(repo, "fix: handle empty export list")
            commit(repo, "update export labels")
            commit(repo, "remove(config): deprecated export flag")

            output = repo / "CHANGELOG.md"
            run([sys.executable, str(SCRIPT), str(output)], repo)
            changelog = output.read_text(encoding="utf-8")

            self.assertIn("Generated from commits since `v1.0.0`.", changelog)
            self.assertIn("### Added", changelog)
            self.assertIn("feat(ui): add export button", changelog)
            self.assertIn("### Fixed", changelog)
            self.assertIn("fix: handle empty export list", changelog)
            self.assertIn("### Changed", changelog)
            self.assertIn("update export labels", changelog)
            self.assertIn("### Removed", changelog)
            self.assertIn("remove(config): deprecated export flag", changelog)
            self.assertNotIn("chore: initial release", changelog)


if __name__ == "__main__":
    unittest.main()
