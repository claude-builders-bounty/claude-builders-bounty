import subprocess
import tempfile
import unittest
from pathlib import Path
from changelog import category, render


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, message):
        self.git("commit", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def test_release_boundary_and_all_categories(self):
        old = self.commit("feat: old")
        self.git("tag", "v1")
        hashes = [self.commit(x) for x in ("feat(ui): add panel", "fix!: prevent crash", "refactor: simplify", "chore: remove legacy")]
        output = render(self.repo)
        self.assertNotIn(old[:12], output)
        for sha in hashes:
            self.assertEqual(output.count(f"(`{sha[:12]}`)"), 1)
        for name in ("Added", "Fixed", "Changed", "Removed"):
            self.assertIn(f"### {name}", output)

    def test_no_tag_and_markdown_escape(self):
        self.commit("fix: [unsafe](javascript:test) <script> `text`")
        output = render(self.repo)
        self.assertIn("includes all commits", output)
        self.assertIn(r"\[unsafe\]", output)
        self.assertIn(r"\<script\>", output)

    def test_side_branch_tag_does_not_hide_changes(self):
        self.commit("base")
        self.git("tag", "release-1")
        self.git("checkout", "-b", "topic")
        topic = self.commit("feat: topic")
        self.git("tag", "topic-preview")
        self.git("checkout", "main")
        main = self.commit("fix: main")
        self.git("merge", "--no-ff", "topic", "-m", "merge topic")
        output = render(self.repo)
        self.assertIn("Changes since release-1.", output)
        self.assertIn(topic[:12], output)
        self.assertIn(main[:12], output)

    def test_tagged_head_has_empty_sections(self):
        self.commit("base")
        self.git("tag", "v1")
        self.assertEqual(render(self.repo).count("- None."), 4)

    def test_existing_output_preserved(self):
        self.commit("base")
        target = self.repo / "CHANGELOG.md"
        target.write_text("hand maintained")
        result = subprocess.run(["bash", str(Path(__file__).with_name("changelog.sh")), "--repo", str(self.repo), "--output", str(target)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), "hand maintained")

    def test_shallow_clone_rejected(self):
        self.commit("base")
        clone = self.repo / "shallow"
        subprocess.run(["git", "clone", "--depth", "1", self.repo.as_uri(), str(clone)], check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, "Shallow history"):
            render(clone)


if __name__ == "__main__":
    unittest.main()
