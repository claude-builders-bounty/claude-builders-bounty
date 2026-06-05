import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_changelog.py"
SPEC = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
changelog = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = changelog
SPEC.loader.exec_module(changelog)


class GenerateChangelogTest(unittest.TestCase):
    def test_categories_conventional_commits(self):
        self.assertEqual(changelog.category_for("feat: add search page"), "Added")
        self.assertEqual(changelog.category_for("fix(api): handle 404 responses"), "Fixed")
        self.assertEqual(changelog.category_for("refactor: simplify client"), "Changed")
        self.assertEqual(changelog.category_for("remove legacy config"), "Removed")

    def test_categories_keyword_fallbacks(self):
        self.assertEqual(changelog.category_for("Implement upload support"), "Added")
        self.assertEqual(changelog.category_for("Correct timezone parsing"), "Fixed")
        self.assertEqual(changelog.category_for("Drop unused adapter"), "Removed")
        self.assertEqual(changelog.category_for("Update docs"), "Changed")

    def test_render_includes_all_sections(self):
        commits = [
            changelog.Commit(hash="1111111", subject="feat: add reporting"),
            changelog.Commit(hash="2222222", subject="fix: correct export"),
        ]
        rendered = changelog.render_changelog(changelog.grouped_commits(commits), "v1.0.0")

        self.assertIn("Changes since `v1.0.0`.", rendered)
        self.assertIn("### Added", rendered)
        self.assertIn("- feat: add reporting (`1111111`)", rendered)
        self.assertIn("### Fixed", rendered)
        self.assertIn("- fix: correct export (`2222222`)", rendered)
        self.assertIn("### Changed", rendered)
        self.assertIn("### Removed", rendered)

    def test_script_generates_commits_since_tag(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)

            (repo / "file.txt").write_text("one\n", encoding="utf-8")
            subprocess.run(["git", "add", "file.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "feat: initial release"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)

            (repo / "file.txt").write_text("two\n", encoding="utf-8")
            subprocess.run(["git", "commit", "-am", "fix: correct export"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            (repo / "old.txt").write_text("legacy\n", encoding="utf-8")
            subprocess.run(["git", "add", "old.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "remove legacy file"], cwd=repo, check=True, stdout=subprocess.DEVNULL)

            output = repo / "CHANGELOG.md"
            subprocess.run(
                [sys.executable, str(SCRIPT), "--repo", str(repo), "--output", str(output)],
                check=True,
                stdout=subprocess.DEVNULL,
            )

            generated = output.read_text(encoding="utf-8")
            self.assertIn("Changes since `v1.0.0`.", generated)
            self.assertIn("- fix: correct export", generated)
            self.assertIn("- remove legacy file", generated)
            self.assertNotIn("feat: initial release", generated)


if __name__ == "__main__":
    unittest.main()
