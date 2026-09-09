import pathlib
import subprocess
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "changelog.sh"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = pathlib.Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "user.name", "Fixture")

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True).strip()

    def commit(self, subject):
        self.git("commit", "-q", "--allow-empty", "-m", subject)
        return self.git("rev-parse", "--short", "HEAD")

    def run_script(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], cwd=self.repo,
                              text=True, capture_output=True)

    def generate(self, *args):
        result = self.run_script(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return (self.repo / "CHANGELOG.md").read_text()

    def test_no_tags_and_categories(self):
        cases = [("feat(api)!: add endpoint", "Added"),
                 ("feat!: new API", "Added"),
                 ("fix!: repair startup", "Fixed"),
                 ("Fixed timeout", "Fixed"),
                 ("remove!: retire API", "Removed"),
                 ("delete obsolete file", "Removed"),
                 ("docs: explain setup", "Changed")]
        ids = [(self.commit(subject), subject, category)
               for subject, category in cases]
        output = self.generate()
        for short_id, subject, category in ids:
            section = output.split("### " + category + "\n\n")[1].split("### ")[0]
            self.assertIn(f"- {subject} ({short_id})", section)
        self.assertEqual(output.count("\n- "), len(cases))

    def test_tag_boundary(self):
        self.commit("feat: before tag")
        self.git("tag", "v1.0.0")
        self.commit("fix: after tag")
        output = self.generate()
        self.assertIn("since v1.0.0", output)
        self.assertNotIn("before tag", output)
        self.assertIn("after tag", output)

    def test_annotated_tag_and_no_new_commits(self):
        self.commit("initial")
        self.git("tag", "-a", "v1", "-m", "release")
        output = self.generate()
        self.assertIn("since v1", output)
        self.assertEqual(output.count("_None._"), 4)
        self.assertNotIn("- initial", output)

    def test_empty_repository_preserves_output(self):
        path = self.repo / "CHANGELOG.md"
        path.write_text("keep this")
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertEqual(path.read_text(), "keep this")

    def test_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(["bash", str(SCRIPT)], cwd=directory,
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((pathlib.Path(directory) / "CHANGELOG.md").exists())

    def test_custom_output_and_repeatability(self):
        self.commit("Add support")
        args = ("-o", "docs with spaces/changes.md")
        self.assertEqual(self.run_script(*args).returncode, 0)
        path = self.repo / args[1]
        first = path.read_bytes()
        self.assertEqual(self.run_script(*args).returncode, 0)
        self.assertEqual(first, path.read_bytes())
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_invalid_arguments(self):
        for args in [("-o",), ("-x",), ("unexpected",)]:
            with self.subTest(args=args):
                self.assertEqual(self.run_script(*args).returncode, 2)
        self.assertEqual(self.run_script("-h").returncode, 0)


if __name__ == "__main__":
    unittest.main()
