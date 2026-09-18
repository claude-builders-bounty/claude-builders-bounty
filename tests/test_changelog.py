"""End-to-end tests against real temporary Git repositories, with no network."""
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "changelog.py"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog-test-")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, subject):
        self.git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", subject)
        return self.git("rev-parse", "HEAD")

    def run_script(self, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args], capture_output=True)
        self.assertEqual(result.returncode, 0 if success else 1, result.stderr.decode())
        return result

    def test_categories_and_release_boundary(self):
        released = self.commit("feat: released")
        self.git("tag", "v1")
        entries = [("feat(ui)!: new screen", "Added"), ("fix: crash", "Fixed"),
                   ("refactor: simplify", "Changed"), ("remove: legacy", "Removed")]
        for message, _ in entries:
            self.commit(message)
        output = self.run_script("--stdout").stdout.decode()
        self.assertNotIn("feat: released", output)
        self.assertIn(f"Base: `{released}`", output)
        for message, group in entries:
            section = output.split(f"### {group}\n", 1)[1].split("\n### ")[0]
            self.assertIn(message.split(": ")[1], section)

    def test_no_tags_and_empty_range(self):
        self.commit("initial setup")
        self.assertIn("initial setup", self.run_script("--stdout").stdout.decode())
        self.git("tag", "v1")
        output = self.run_script("--stdout").stdout.decode()
        self.assertNotIn("- initial setup", output)
        self.assertEqual(output.count("- None."), 4)

    def test_topic_tag_cannot_hide_unreleased_mainline(self):
        self.commit("feat: baseline")
        self.git("tag", "v1")
        self.git("switch", "-c", "topic")
        topic = self.commit("feat: topic")
        self.git("tag", "v9-topic")
        self.git("switch", "main")
        main = self.commit("fix: mainline")
        self.git("-c", "commit.gpgsign=false", "merge", "--no-ff", "topic", "-m", "merge topic")
        output = self.run_script("--stdout").stdout.decode()
        self.assertIn(f"(`{topic}`)", output)
        self.assertIn(f"(`{main}`)", output)
        self.assertIn("merge topic", output)
        self.assertNotIn("- feat: baseline", output)

    def test_annotated_tag(self):
        self.commit("feat: baseline")
        self.git("-c", "tag.gpgsign=false", "tag", "-a", "v1", "-m", "release")
        self.commit("fix: after tag")
        output = self.run_script("--stdout").stdout.decode()
        self.assertIn("fix: after tag", output)
        self.assertNotIn("- feat: baseline", output)

    def test_preserve_handwritten_bytes_and_repeatability(self):
        self.commit("feat: first")
        self.run_script()
        path = self.repo / "CHANGELOG.md"
        initial = path.read_bytes()
        self.run_script()
        self.assertEqual(initial, path.read_bytes())
        prefix = "# Manual notes — حفظ\r\n\r\n".encode()
        suffix = b"\r\n## [1.0]\r\n- Handwritten release notes.\r\n"
        path.write_bytes(prefix + initial + suffix)
        self.commit("fix: second")
        self.run_script()
        self.assertTrue(path.read_bytes().startswith(prefix))
        self.assertTrue(path.read_bytes().endswith(suffix))
        self.assertIn(b"fix: second", path.read_bytes())

    def test_unmanaged_or_ambiguous_file_not_overwritten(self):
        self.commit("feat: first")
        path = self.repo / "CHANGELOG.md"
        for old in [b"# My existing notes\n", b"<!-- generated-changelog:start -->\n",
                    b"<!-- generated-changelog:end --><!-- generated-changelog:start -->"]:
            with self.subTest(old=old):
                path.write_bytes(old)
                self.run_script(success=False)
                self.assertEqual(old, path.read_bytes())

    def test_untrusted_subject_and_unicode(self):
        self.commit("fix: <script>alert(1)</script> [click](https://example.com) `cmd` — فارسی")
        output = self.run_script("--stdout").stdout.decode()
        self.assertNotIn("<script>", output)
        self.assertNotIn("[click](", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertIn("فارسی", output)
        self.assertIn(r"\`cmd\`", output)

    def test_shallow_repository_refused(self):
        self.commit("feat: baseline")
        self.commit("fix: next")
        clone = Path(self.temp.name) / "shallow"
        subprocess.run(["git", "clone", "--depth=1", self.repo.as_uri(), str(clone)], check=True, capture_output=True)
        self.repo = clone
        result = self.run_script(success=False)
        self.assertIn(b"Shallow history", result.stderr)
        self.assertFalse((clone / "CHANGELOG.md").exists())

    def test_empty_repository_and_stdout_do_not_write(self):
        self.run_script(success=False)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
        self.commit("feat: first")
        self.run_script("--stdout")
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_bash_entry_point_from_another_directory(self):
        bash = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe") if os.name == "nt" else shutil.which("bash")
        if not bash or not Path(bash).exists():
            self.skipTest("Bash unavailable")
        self.commit("feat: through bash")
        result = subprocess.run([bash, str(SCRIPT.parents[1] / "changelog.sh"), "--repo", str(self.repo), "--stdout"],
                                cwd=self.temp.name, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(b"feat: through bash", result.stdout)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
