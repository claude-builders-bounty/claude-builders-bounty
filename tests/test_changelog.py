"""Exercise the command in a disposable real Git worktree (stdlib only)."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "changelog.sh"
BASH = os.environ.get("CHANGELOG_TEST_BASH", "bash")


class ChangelogTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.git("init", "-q")

    def git(self, *args):
        subprocess.run(["git", "-c", "user.name=Tester", "-c",
                        "user.email=test@example.invalid", *args],
                       cwd=self.repo, check=True, capture_output=True)

    def commit(self, subject):
        self.git("commit", "-q", "--allow-empty", "-m", subject)

    def generate(self, *args, check=True):
        return subprocess.run([BASH, str(SCRIPT), *args], cwd=self.repo,
                              capture_output=True, check=check)

    def test_categories_and_tag_boundary(self):
        self.commit("Old change")
        self.git("tag", "v1")
        for subject in ("feat(ui): output a file", "fix: correct count", "Update schema", "Drop v0"):
            self.commit(subject)
        text = self.generate("--stdout").stdout.decode()
        self.assertNotIn("Old change", text)
        for section, start in (("Added", "feat(ui)"), ("Fixed", "fix:"),
                               ("Changed", "Update"), ("Removed", "Drop")):
            self.assertIn(f"### {section}\n\n- {start}", text)
        self.git("tag", "-a", "v2", "-m", "release")
        self.assertIn(b"No changes since the latest tag.", self.generate("--stdout").stdout)

    def test_no_tag_idempotence_and_handwritten_notes(self):
        self.commit("Add <details> [demo]")
        self.generate()
        path = self.repo / "CHANGELOG.md"
        original = path.read_bytes()
        self.assertIn(b"Add &lt;details&gt; \\[demo\\]", original)
        self.assertEqual(original, self.generate("--stdout").stdout)
        notes = b"\r\n## v0\r\n\r\nA handwritten note.\r\n"
        path.write_bytes(original.replace(b"\n", b"\r\n") + notes)
        self.commit("fix: second change")
        self.generate()
        updated = path.read_bytes()
        self.assertIn(b"### Fixed\r\n", updated)
        self.assertTrue(updated.endswith(notes))
        self.generate()
        self.assertEqual(path.read_bytes(), updated)

    def test_preserves_unmanaged_existing_file(self):
        self.commit("Initial release")
        path = self.repo / "CHANGELOG.md"
        path.write_bytes(b"# Release notes\n")
        rejected = self.generate(check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn(b"--stdout", rejected.stderr)
        self.assertEqual(path.read_bytes(), b"# Release notes\n")


if __name__ == "__main__":
    unittest.main()
