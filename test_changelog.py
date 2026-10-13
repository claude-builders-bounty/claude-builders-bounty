"""End-to-end checks using temporary real Git repositories."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("generate_changelog.py")


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog test ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "--initial-branch=main")
        self.git("config", "user.name", "Test Contributor")
        self.git("config", "user.email", "test@example.invalid")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git("commit", "--allow-empty", "-m", message)

    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
                              capture_output=True, encoding="utf-8")

    def test_tag_boundary_categories_and_markdown(self):
        self.commit("old change")
        self.git("tag", "v1.0.0")
        self.commit("feat(cli): add output")
        self.commit("fix!: repair output")
        self.commit("refactor: simplify parser")
        self.commit("remove: legacy option")
        self.commit("Add [link](https://example.invalid) <script> & `markup`")
        result = self.run_script("--output", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("old change", result.stdout)
        for heading, subject in (("Added", "feat(cli)"), ("Fixed", "fix!"),
                                 ("Changed", "refactor"), ("Removed", "remove")):
            section = result.stdout.split(f"### {heading}\n", 1)[1].split("###", 1)[0]
            self.assertIn(subject, section)
        self.assertIn(r"\[link\]", result.stdout)
        self.assertIn("&lt;script&gt; &amp;", result.stdout)
        self.assertIn(r"\`markup\`", result.stdout)

    def test_no_tags_and_repeatable_output(self):
        self.commit("Initial commit")
        self.commit("Fix Unicode café output")
        first = self.run_script("--output", "-")
        second = self.run_script("--output", "-")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertIn("No reachable tag", first.stdout)
        self.assertIn("Initial commit", first.stdout)
        self.assertIn("café", first.stdout)

    def test_annotated_tag_at_head_and_unrelated_tag(self):
        self.commit("Initial commit")
        self.git("tag", "-a", "v1", "-m", "release")
        self.git("checkout", "--orphan", "other")
        self.commit("feat: unrelated branch")
        self.git("tag", "v999")
        self.git("checkout", "main")
        result = self.run_script("--output", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tag **v1**", result.stdout)
        self.assertEqual(result.stdout.count("_None._"), 4)
        self.assertNotIn("unrelated branch", result.stdout)

    def test_existing_output_is_preserved_until_force(self):
        self.commit("feat: new feature")
        output = self.repo / "CHANGELOG.md"
        output.write_text("Existing release history\n", encoding="utf-8")
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), "Existing release history\n")
        result = self.run_script("--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("feat: new feature", output.read_text())

    def test_empty_and_non_repository_errors_do_not_write(self):
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
        other = self.repo / "not a repo"
        other.mkdir()
        result = self.run_script("--repo", str(other / "missing"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git error", result.stderr)

    def test_shallow_clone_requires_complete_history(self):
        self.commit("feat: old feature")
        self.git("tag", "v1")
        self.commit("fix: recent fix")
        clone = self.repo / "shallow"
        self.git("clone", "--depth=1", self.repo.as_uri(), str(clone))
        result = self.run_script("--repo", str(clone), "--output", "-")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git fetch --unshallow --tags", result.stderr)


if __name__ == "__main__":
    unittest.main()
