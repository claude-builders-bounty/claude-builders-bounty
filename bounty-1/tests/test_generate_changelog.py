import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "generate_changelog.py"
SPEC = importlib.util.spec_from_file_location("generate_changelog", MODULE_PATH)
gc = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = gc
SPEC.loader.exec_module(gc)


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    )
    return result.stdout


class RepoFixture:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        run_git(self.path, "init", "-q")
        run_git(self.path, "config", "user.email", "test@example.com")
        run_git(self.path, "config", "user.name", "Test User")
    def commit(self, message: str, body: str = "") -> None:
        marker = self.path / "history.txt"
        old = marker.read_text() if marker.exists() else ""
        marker.write_text(old + message + "\n")
        run_git(self.path, "add", "history.txt")
        cmd = ["commit", "-q", "-m", message]
        if body:
            cmd.extend(["-m", body])
        run_git(self.path, *cmd)

    def close(self):
        self.tmp.cleanup()


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.repo = RepoFixture()

    def tearDown(self):
        self.repo.close()

    def test_categories_and_breaking_not_duplicated(self):
        commits = [
            gc.Commit("a" * 40, "feat(api)!: add endpoint", "BREAKING CHANGE: v2"),
            gc.Commit("b" * 40, "fix: repair parser", ""),
            gc.Commit("c" * 40, "remove: legacy switch", ""),
            gc.Commit("d" * 40, "docs: explain usage", ""),
        ]
        text = gc.render(commits, date="2026-09-21", heading="Unreleased")
        self.assertIn("### Added", text)
        self.assertIn("add endpoint **BREAKING**", text)
        self.assertIn("### Fixed", text)
        self.assertIn("### Removed", text)
        self.assertIn("### Changed", text)
        self.assertEqual(text.count("add endpoint"), 1)

    def test_default_range_starts_after_latest_tag(self):
        self.repo.commit("feat: before tag")
        run_git(self.repo.path, "tag", "v1.0.0")
        self.repo.commit("fix: after tag")
        since = gc.latest_tag(self.repo.path)
        commits = gc.read_commits(self.repo.path, since, "HEAD")
        self.assertEqual([c.subject for c in commits], ["fix: after tag"])

    def test_pipe_in_subject_does_not_corrupt_commit(self):
        self.repo.commit("fix: preserve a | pipe")
        commits = gc.read_commits(self.repo.path, None, "HEAD")
        self.assertEqual(commits[0].subject, "fix: preserve a | pipe")

    def test_update_file_preserves_previous_entries(self):
        path = self.repo.path / "CHANGELOG.md"
        path.write_text("# Changelog\n\n## v1.0.0\n\n### Added\n- old\n")
        gc.update_file(path, "## Unreleased - 2026-09-21\n\n### Fixed\n- new\n")
        text = path.read_text()
        self.assertLess(text.index("## Unreleased"), text.index("## v1.0.0"))
        self.assertIn("- old", text)

    def test_main_writes_changelog(self):
        self.repo.commit("feat: first feature")
        code = gc.main(["--repo", str(self.repo.path), "--date", "2026-09-21"])
        self.assertEqual(code, 0)
        text = (self.repo.path / "CHANGELOG.md").read_text()
        self.assertIn("### Added", text)
        self.assertIn("first feature", text)


if __name__ == "__main__":
    unittest.main()
