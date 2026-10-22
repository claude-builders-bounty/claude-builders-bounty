import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "generate_changelog.py"
spec = importlib.util.spec_from_file_location("changelog", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.git("init")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode("utf-8").strip()

    def commit(self, subject):
        self.git("commit", "--allow-empty", "-m", subject)

    def test_tag_range_and_four_categories(self):
        self.commit("feat: old release")
        self.git("tag", "v1.0")
        for subject in ["feat(ui): add dialog", "fix: repair crash", "refactor!: new API", "remove: old flag", "unclassified work"]:
            self.commit(subject)
        result = module.generate(self.repo)
        self.assertNotIn("old release", result)
        for section, subject in [("Added", "feat"), ("Fixed", "fix"), ("Changed", "refactor"), ("Removed", "remove")]:
            block = result.split("### " + section)[1].split("### ")[0]
            self.assertIn(subject, block)
        self.assertIn("unclassified work", result)

    def test_no_tag_unicode_and_markdown(self):
        self.commit("Add: 中文 <script> [link](https://example.invalid)")
        result = module.generate(self.repo)
        self.assertIn("中文", result)
        self.assertIn("&lt;script&gt;", result)
        self.assertIn(r"\[link\]", result)
        self.assertIn("all commits", result)

    def test_head_tag_empty_and_repeatable(self):
        self.commit("initial")
        self.git("tag", "release")
        result = module.generate(self.repo)
        self.assertEqual(result.count("- None."), 4)
        self.assertEqual(result, module.generate(self.repo))

    def test_unreachable_tag_is_ignored(self):
        self.commit("initial")
        original = self.git("rev-parse", "HEAD")
        self.git("checkout", "-b", "other")
        self.commit("feat: unrelated")
        self.git("tag", "v99")
        self.git("checkout", "--detach", original)
        self.commit("fix: current")
        self.assertNotIn("unrelated", module.generate(self.repo))
        with self.assertRaises(ValueError):
            module.generate(self.repo, "v99")

    def test_explicit_base_and_invalid_base(self):
        self.commit("initial")
        base = self.git("rev-parse", "HEAD")
        self.commit("Delete deprecated helper")
        self.assertIn("Delete deprecated helper", module.generate(self.repo, base))
        with self.assertRaises(ValueError):
            module.generate(self.repo, "--all")

    def test_cli_preserves_existing_file_and_force(self):
        self.commit("fix: regression")
        output = Path(self.temp.name) / "CHANGELOG.md"
        output.write_text("release history", encoding="utf-8")
        cmd = [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--output", str(output)]
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)
        self.assertEqual(output.read_text(), "release history")
        self.assertEqual(subprocess.run(cmd + ["--force"], capture_output=True).returncode, 0)
        self.assertIn("regression", output.read_text())

    def test_empty_repo_fails_without_output(self):
        output = Path(self.temp.name) / "CHANGELOG.md"
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), "--output", str(output)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
