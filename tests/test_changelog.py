from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "changelog.sh"


class ChangelogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog tests ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.commit("Initial release")
        self.git("tag", "v1.0.0")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True, stderr=subprocess.PIPE).strip()

    def commit(self, message):
        self.git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", message)

    def run_script(self, *args, ok=True):
        result = subprocess.run(["bash", str(SCRIPT), "--repo", str(self.repo), *args], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        return result

    def test_categories_boundary_and_scope(self):
        messages = ["feat(api): add pagination", "fix: close retry loop", "perf: reduce allocation", "feat!: remove obsolete API", "Remove unused helper", "Add documentation", "Fix example", "chore: update dependencies"]
        for message in messages:
            self.commit(message)
        text = self.run_script("--stdout").stdout
        self.assertNotIn("Initial release", text)
        positions = [text.index("### " + category) for category in ("Added", "Fixed", "Changed", "Removed")]
        self.assertEqual(positions, sorted(positions))
        for category, message in [("Added", messages[0]), ("Added", messages[5]), ("Fixed", messages[1]), ("Changed", messages[2]), ("Removed", messages[3])]:
            section = text.split("### " + category + "\n", 1)[1].split("### ", 1)[0]
            self.assertIn(message, section)
        self.assertEqual(text.count(" (`"), len(messages))

    def test_reachable_tag_instead_of_newer_unrelated_tag(self):
        self.git("switch", "-c", "other")
        self.commit("Other branch")
        self.git("tag", "v99")
        self.git("switch", "main")
        self.commit("feat: current branch")
        text = self.run_script("--stdout").stdout
        self.assertIn("since tag v1.0.0", text)
        self.assertNotIn("Other branch", text)

    def test_annotated_tag_and_empty_range(self):
        self.commit("feat: released")
        self.git("-c", "tag.gpgsign=false", "tag", "-a", "v2", "-m", "release")
        text = self.run_script("--stdout").stdout
        self.assertIn("since tag v2", text)
        self.assertNotIn("feat: released", text)
        self.assertEqual(text.count("_No changes._"), 4)

    def test_untagged_history(self):
        self.git("tag", "-d", "v1.0.0")
        self.assertIn("Initial release", self.run_script("--stdout").stdout)

    def test_preserves_history_and_handwritten_notes_idempotently(self):
        target = self.repo / "CHANGELOG.md"
        previous = "# Project history\n\nIntroduction.\n\n## [Unreleased]\n\nManual note.\n\n## [1.0.0]\n\n- Old release.\n"
        target.write_text(previous)
        self.commit("feat: new entry")
        self.run_script()
        first = target.read_bytes()
        self.run_script()
        self.assertEqual(first, target.read_bytes())
        self.assertIn("Manual note.\n\n## [1.0.0]\n\n- Old release.\n", target.read_text())
        self.commit("fix: additional entry")
        self.run_script()
        self.assertEqual(target.read_text().count("feat: new entry"), 1)
        self.assertIn("fix: additional entry", target.read_text())

    def test_inserts_unreleased_before_existing_release(self):
        target = self.repo / "CHANGELOG.md"
        target.write_text("# History\n\n## v1\n\nOld notes.\n")
        self.run_script()
        self.assertLess(target.read_text().index("## [Unreleased]"), target.read_text().index("## v1"))
        self.assertTrue(target.read_text().endswith("Old notes.\n"))

    def test_new_tag_replaces_previous_generated_range(self):
        self.commit("feat: now released")
        self.run_script()
        self.git("tag", "v2")
        self.commit("fix: next release")
        self.run_script()
        text = (self.repo / "CHANGELOG.md").read_text()
        self.assertNotIn("feat: now released", text)
        self.assertIn("fix: next release", text)
        self.assertEqual(text.count("git-changelog:begin"), 1)

    def test_default_repository_from_subdirectory(self):
        directory = self.repo / "nested"
        directory.mkdir()
        result = subprocess.run(["bash", str(SCRIPT)], cwd=directory, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / "CHANGELOG.md").is_file())
        self.assertFalse((directory / "CHANGELOG.md").exists())

    def test_malformed_markers_leave_file_unchanged(self):
        for text in ["<!-- git-changelog:begin -->", "<!-- git-changelog:end --><!-- git-changelog:begin -->", "## Unreleased\n\n## [Unreleased]\n"]:
            with self.subTest(text=text):
                target = self.repo / "CHANGELOG.md"
                target.write_text(text)
                self.run_script(ok=False)
                self.assertEqual(target.read_text(), text)

    def test_markdown_and_shell_metacharacters_are_literal(self):
        self.commit("fix: <script> & [link](https://example.invalid) `code` $(touch PWNED) | back\\slash")
        text = self.run_script("--stdout").stdout
        self.assertIn("&lt;script&gt; &amp; \\[link\\]", text)
        self.assertIn("\\`code\\`", text)
        self.assertIn("$(touch PWNED)", text)
        self.assertFalse((self.repo / "PWNED").exists())

    def test_stdout_does_not_write_and_custom_path_preserves_mode(self):
        self.run_script("--stdout")
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
        target = self.repo / "custom.md"
        target.touch(mode=0o600)
        self.run_script("--output", "custom.md")
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_symlink_is_not_followed(self):
        outside = Path(self.temp.name) / "outside.md"
        outside.write_text("keep")
        (self.repo / "CHANGELOG.md").symlink_to(outside)
        self.run_script(ok=False)
        self.assertEqual(outside.read_text(), "keep")

    def test_shallow_clone_is_not_presented_as_complete_history(self):
        clone = Path(self.temp.name) / "shallow"
        subprocess.run(["git", "clone", "--depth=1", self.repo.as_uri(), str(clone)], check=True, capture_output=True)
        self.repo = clone
        self.assertIn("git fetch --unshallow --tags", self.run_script(ok=False).stderr)
        self.assertFalse((clone / "CHANGELOG.md").exists())

    def test_empty_or_non_repository_leaves_output_untouched(self):
        empty = Path(self.temp.name) / "empty"
        empty.mkdir()
        self.repo = empty
        self.run_script(ok=False)
        self.git("init", "-b", "main")
        self.run_script(ok=False)
        self.assertFalse((empty / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
