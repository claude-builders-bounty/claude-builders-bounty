import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "changelog.py"


def git(repo, *args):
    return subprocess.run(
        ["git", *args], cwd=repo, text=True, capture_output=True, check=True
    ).stdout.strip()


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")

    def tearDown(self):
        self.tempdir.cleanup()

    def commit(self, message, filename):
        (self.repo / filename).write_text(message, encoding="utf-8")
        git(self.repo, "add", filename)
        git(self.repo, "commit", "-q", "-m", message)

    def generate(self):
        return subprocess.run(
            ["python3", str(SCRIPT), "--repo", str(self.repo), "--stdout"],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_uses_only_commits_after_latest_tag_and_categorizes_them(self):
        self.commit("feat: old tagged feature", "old.txt")
        git(self.repo, "tag", "v1.0.0")
        self.commit("feat: add export button", "feature.txt")
        self.commit("fix: prevent duplicate rows", "fix.txt")
        self.commit("remove: obsolete flag", "remove.txt")
        self.commit("docs: explain exports", "docs.txt")

        result = self.generate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("old tagged feature", result.stdout)
        self.assertIn("## Added\n- add export button", result.stdout)
        self.assertIn("## Fixed\n- prevent duplicate rows", result.stdout)
        self.assertIn("## Changed\n- explain exports", result.stdout)
        self.assertIn("## Removed\n- obsolete flag", result.stdout)

    def test_repository_without_tags_includes_full_history(self):
        self.commit("feat: first feature", "one.txt")
        self.commit("fix: second commit", "two.txt")

        result = self.generate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("first feature", result.stdout)
        self.assertIn("second commit", result.stdout)
        self.assertNotIn("\n- \n", result.stdout)

    def test_empty_repository_produces_a_valid_changelog(self):
        result = self.generate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Changelog", result.stdout)
        self.assertIn("## Added", result.stdout)
        self.assertIn("## Fixed", result.stdout)
        self.assertIn("## Changed\n- No changes.", result.stdout)
        self.assertIn("## Removed", result.stdout)

    def test_bash_entrypoint_forwards_repository_and_stdout_arguments(self):
        self.commit("feat: forwarded feature", "feature.txt")

        result = subprocess.run(
            ["bash", str(ROOT / "changelog.sh"), "--repo", str(self.repo), "--stdout"],
            cwd=self.repo.parent,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Added\n- forwarded feature", result.stdout)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_invalid_repository_fails_without_replacing_existing_changelog(self):
        with tempfile.TemporaryDirectory(prefix="changelog-invalid-") as directory:
            repo = Path(directory)
            output = repo / "CHANGELOG.md"
            original = "# Handwritten releases\n\nKeep previous release notes.\n"
            output.write_text(original, encoding="utf-8")

            result = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo)],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertEqual(output.read_text(encoding="utf-8"), original)

    def test_commit_subject_is_data_not_a_shell_command(self):
        marker = self.repo / "PWNED"
        self.commit("feat: $(touch PWNED); `touch PWNED`", "safe.txt")

        result = self.generate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("$(touch PWNED); `touch PWNED`", result.stdout)
        self.assertFalse(marker.exists())



    def test_tag_name_does_not_collide_with_orig_head_pseudoref(self):
        self.commit("chore: tagged baseline", "old.txt")
        git(self.repo, "tag", "ORIG_HEAD")
        self.commit("feat: should be in changelog", "new.txt")
        git(self.repo, "update-ref", "ORIG_HEAD", "HEAD")

        result = self.generate()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## Added\n- should be in changelog", result.stdout)
        self.assertNotIn("tagged baseline", result.stdout)

if __name__ == "__main__":
    unittest.main()
