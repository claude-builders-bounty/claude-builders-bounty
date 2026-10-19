import importlib.util
import pathlib
import shutil
import subprocess
import tempfile
import unittest

BASE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("changelog", BASE / "changelog.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")

    def git(self, *args):
        return module.git(self.repo, *args).stdout

    def commit(self, subject):
        self.git("commit", "--allow-empty", "-qm", subject)

    def test_tag_boundary_categories_and_empty_sections(self):
        self.commit("feat: excluded old feature")
        self.git("tag", "-am", "release", "v1.0")
        for subject in ("feat(ui): new feature", "fix(api): repair", "refactor!: new design", "remove: old option"):
            self.commit(subject)
        _, output = module.render(self.repo)
        self.assertNotIn("excluded old feature", output)
        self.assertIn("since `v1.0`", output)
        for section, entry in (("Added", "new feature"), ("Fixed", "repair"), ("Changed", "**Breaking:** new design"), ("Removed", "old option")):
            self.assertIn(f"### {section}\n\n- {entry}", output)

    def test_no_tags_and_deterministic_regeneration(self):
        self.commit("initial work")
        first = module.render(self.repo)[1]
        self.assertEqual(first, module.render(self.repo)[1])
        self.assertIn("no tag", first)
        self.assertIn("### Added\n\n- None.", first)
        self.assertIn("### Changed\n\n- initial work", first)

    def test_unreachable_tag_is_not_used(self):
        self.commit("initial")
        branch = self.git("branch", "--show-current").strip()
        self.git("checkout", "-qb", "side")
        self.commit("feat: side feature")
        self.git("tag", "v99")
        self.git("checkout", "-q", branch)
        self.commit("fix: main fix")
        output = module.render(self.repo)[1]
        self.assertIn("no tag", output)
        self.assertNotIn("side feature", output)

    def test_html_and_markdown_are_escaped(self):
        self.commit("feat: <img> [danger](url) *star*")
        output = module.render(self.repo)[1]
        self.assertIn("&lt;img&gt;", output)
        self.assertIn("\\[danger\\]", output)
        self.assertIn("\\*star\\*", output)

    @unittest.skipUnless(shutil.which('bash'), 'Bash is not installed on this host; the Bash entry point is exercised on Linux CI')
    def test_bash_entrypoint_preserves_existing_output(self):
        self.commit("feat: first")
        command = ["bash", str(BASE / "changelog.sh"), "--repo", str(self.repo)]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        output = self.repo / "CHANGELOG.md"
        original = output.read_bytes()
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.commit("fix: second")
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(original, output.read_bytes())
        self.assertEqual(subprocess.run(command + ["--overwrite"], capture_output=True).returncode, 0)
        self.assertIn("second", output.read_text())

    def test_shallow_history_is_refused(self):
        self.commit("first")
        self.commit("second")
        clone = pathlib.Path(self.temp.name) / "shallow"
        subprocess.run(["git", "clone", "-q", "--depth", "1", self.repo.as_uri(), str(clone)], check=True)
        with self.assertRaisesRegex(ValueError, "shallow"):
            module.render(clone)


if __name__ == "__main__":
    unittest.main()
