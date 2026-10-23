import subprocess
import tempfile
from pathlib import Path
import unittest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from changelog import entries, render, main

def cmd(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)

class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        cmd(self.repo, "init", "-q")
        cmd(self.repo, "config", "user.email", "fixture@example.invalid")
        cmd(self.repo, "config", "user.name", "Fixture")
        (self.repo / "demo.txt").write_text("one")
        cmd(self.repo, "add", ".")
        cmd(self.repo, "commit", "-qm", "initial commit")
        cmd(self.repo, "tag", "v1.0.0")
    def tearDown(self):
        self.tmp.cleanup()
    def commit(self, message):
        with (self.repo / "demo.txt").open("a") as f:
            f.write("more")
        cmd(self.repo, "add", ".")
        cmd(self.repo, "commit", "-qm", message)
    def test_categories_and_tag_range(self):
        for message in ("feat: add search", "fix(ui): correct layout", "refactor: simplify cache", "remove deprecated API"):
            self.commit(message)
        tag, data = entries(self.repo)
        self.assertEqual(tag, "v1.0.0")
        self.assertEqual([len(data[x]) for x in ("Added","Fixed","Changed","Removed")], [1,1,1,1])
        text = render(tag, data, "2026-10-23")
        self.assertIn("### Removed", text)
        self.assertNotIn("initial commit", text)
    def test_no_new_commits(self):
        tag, data = entries(self.repo)
        self.assertIn("No new commits", render(tag,data))
    def test_writes_file(self):
        self.commit("feat: a thing")
        self.assertEqual(main(["--repo", str(self.repo)]), 0)
        self.assertIn("a thing", (self.repo / "CHANGELOG.md").read_text())
    def test_untagged_repo(self):
        cmd(self.repo, "tag", "-d", "v1.0.0")
        tag, data = entries(self.repo)
        self.assertIsNone(tag)
        self.assertEqual(len(data["Changed"]), 1)

class AdditionalChangelogTests(ChangelogTests):
    def test_preview_does_not_write_file(self):
        self.commit("feat: preview")
        from contextlib import redirect_stdout
        from io import StringIO
        output = StringIO()
        with redirect_stdout(output):
            status = main(["--repo", str(self.repo), "--stdout"])
        self.assertEqual(status, 0)
        self.assertIn("preview", output.getvalue())
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
    def test_uses_nearest_ancestor_tag_not_tag_timestamp(self):
        self.commit("feat: first")
        cmd(self.repo, "tag", "v1.1.0")
        self.commit("fix: later")
        tag, data = entries(self.repo)
        self.assertEqual(tag, "v1.1.0")
        self.assertEqual(len(data["Fixed"]), 1)
        self.assertEqual(len(data["Added"]), 0)

if __name__ == "__main__":
    unittest.main()
