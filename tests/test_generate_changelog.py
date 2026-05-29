import datetime as dt
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "skills" / "generate-changelog" / "generate_changelog.py"
SPEC = importlib.util.spec_from_file_location("generate_changelog", MODULE_PATH)
generate_changelog = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = generate_changelog
SPEC.loader.exec_module(generate_changelog)


class GenerateChangelogTests(unittest.TestCase):
    def test_categorizes_conventional_commits(self):
        commits = [
            generate_changelog.Commit("a1b2c3d", "feat: add export button"),
            generate_changelog.Commit("b2c3d4e", "fix(parser): handle empty logs"),
            generate_changelog.Commit("c3d4e5f", "docs: update install notes"),
            generate_changelog.Commit("d4e5f6a", "remove: legacy changelog task"),
        ]

        grouped = generate_changelog.categorize(commits)

        self.assertEqual(["Add export button"], [c.subject for c in grouped["Added"]])
        self.assertEqual(["Handle empty logs"], [c.subject for c in grouped["Fixed"]])
        self.assertEqual(["Update install notes"], [c.subject for c in grouped["Changed"]])
        self.assertEqual(["Legacy changelog task"], [c.subject for c in grouped["Removed"]])

    def test_renders_markdown(self):
        grouped = {
            "Added": [generate_changelog.Commit("abc1234", "Add changelog skill")],
            "Fixed": [],
            "Changed": [generate_changelog.Commit("def5678", "Update README")],
            "Removed": [],
        }

        output = generate_changelog.render_changelog(
            grouped,
            version="v1.0.0",
            since_tag="v0.9.0",
            date=dt.date(2026, 5, 29),
        )

        self.assertIn("## v1.0.0 - 2026-05-29", output)
        self.assertIn("Changes since `v0.9.0`.", output)
        self.assertIn("### Added\n\n- Add changelog skill (abc1234)", output)
        self.assertIn("### Changed\n\n- Update README (def5678)", output)
        self.assertNotIn("### Fixed", output)

    def test_reads_commits_since_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self.git(repo, "init")
            self.git(repo, "config", "user.email", "test@example.com")
            self.git(repo, "config", "user.name", "Test User")
            (repo / "file.txt").write_text("base\n", encoding="utf-8")
            self.git(repo, "add", "file.txt")
            self.git(repo, "commit", "-m", "feat: initial release")
            self.git(repo, "tag", "v0.1.0")
            (repo / "file.txt").write_text("base\nfix\n", encoding="utf-8")
            self.git(repo, "commit", "-am", "fix: repair tagged range")

            tag = generate_changelog.latest_tag(cwd=repo)
            commits = generate_changelog.read_commits(tag=tag, cwd=repo)

        self.assertEqual("v0.1.0", tag)
        self.assertEqual(1, len(commits))
        self.assertEqual("fix: repair tagged range", commits[0].subject)

    @staticmethod
    def git(cwd, *args):
        subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


if __name__ == "__main__":
    unittest.main()
