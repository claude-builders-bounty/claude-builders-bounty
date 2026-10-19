import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from changelog import classify, generate, last_reachable_tag


SCRIPT = Path(__file__).with_name("changelog.sh").resolve()


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.commit_file("seed.txt", "seed\n", "chore: seed repository")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout.strip()

    def commit_file(self, name, content, message):
        (self.repo / name).write_text(content, encoding="utf-8")
        self.git("add", name)
        self.git("commit", "-q", "-m", message)

    def test_no_tag_scans_history_and_handles_all_categories_and_unicode(self):
        self.commit_file("new.txt", "new\n", "feat(parser)!: add café support")
        self.commit_file("bug.txt", "fixed\n", "fix(api): repair bad response")
        self.commit_file("change.txt", "changed\n", "refactor(core): simplify flow")
        self.commit_file("old.txt", "removed\n", "remove: drop legacy mode")
        output = generate(self.repo)
        self.assertIn("## Unreleased", output)
        self.assertIn("- seed repository", output)
        self.assertIn("### Added\n\n- **BREAKING:** add café support", output)
        self.assertIn("### Fixed\n\n- repair bad response", output)
        self.assertIn("### Changed\n\n- simplify flow", output)
        self.assertIn("### Removed\n\n- drop legacy mode", output)

    def test_uses_latest_reachable_tag_and_empty_range_is_valid(self):
        self.git("tag", "v1.0")
        self.assertEqual(last_reachable_tag(self.repo), "v1.0")
        self.assertIn("No changes since the last tag.", generate(self.repo))
        self.commit_file("feature.txt", "feature\n", "feat: new widget")
        self.git("tag", "v2.0")
        self.commit_file("fix.txt", "fix\n", "fix: newest fix")
        output = generate(self.repo)
        self.assertIn("since v2\\.0", output)
        self.assertIn("- newest fix", output)
        self.assertNotIn("new widget", output)

    def test_unicode_is_preserved_with_non_utf8_git_log_output_encoding(self):
        self.git("tag", "v1.0")
        self.commit_file("feature.txt", "feature\n", "feat: add café support")
        self.git("config", "i18n.logOutputEncoding", "ISO-8859-1")
        output = generate(self.repo)
        self.assertIn("### Added\n\n- add café support", output)
        self.assertNotIn("\ufffd", output)

    def test_classifier_defaults_untyped_and_categorizes_aliases(self):
        self.assertEqual(classify("just a message"), ("Changed", "just a message"))
        self.assertEqual(classify("bug: crash"), ("Fixed", "crash"))
        self.assertEqual(classify("deprecate: old api"), ("Removed", "old api"))

    def test_tag_boundary_does_not_resolve_as_a_pseudoref(self):
        self.git("tag", "ORIG_HEAD")
        self.commit_file("feature.txt", "new\n", "feat: unreleased feature")
        # ORIG_HEAD can also be set by Git operations such as merge and reset.
        self.git("update-ref", "ORIG_HEAD", "HEAD")
        self.assertEqual(last_reachable_tag(self.repo), "ORIG_HEAD")
        output = generate(self.repo)
        self.assertIn("- unreleased feature", output)
        self.assertNotIn("seed repository", output)

    def test_tag_boundary_does_not_resolve_as_a_branch(self):
        self.git("tag", "refs/heads/release")
        self.commit_file("feature.txt", "new\n", "feat: unreleased feature")
        self.git("branch", "release")
        self.assertEqual(last_reachable_tag(self.repo), "refs/heads/release")
        output = generate(self.repo)
        self.assertIn("- unreleased feature", output)
        self.assertNotIn("seed repository", output)

    def test_no_tag_history_is_not_ambiguous_with_a_head_named_file(self):
        self.commit_file("HEAD", "ordinary project file\n", "feat: support HEAD filename")
        output = generate(self.repo)
        self.assertIn("- support HEAD filename", output)
        self.assertIn("- seed repository", output)

    def test_markdown_and_html_in_subjects_are_rendered_as_text(self):
        self.commit_file("malicious.txt", "text\n", 'feat: <img src="https://example.invalid/x"> [link](javascript:alert(1))')
        output = generate(self.repo)
        self.assertNotIn("<img", output)
        self.assertNotIn("javascript:", output)
        self.assertIn("&lt;img", output)
        self.assertIn("\\[link\\]", output)

    def test_describe_failure_is_only_no_tag_if_git_confirms_no_reachable_tags(self):
        error = subprocess.CalledProcessError(128, ["git", "describe"], stderr="fatal: damaged repository")
        with patch("changelog.git", side_effect=[""]):
            self.assertIsNone(last_reachable_tag(self.repo))
        with patch("changelog.git", side_effect=["v1.0\n", error]):
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                last_reachable_tag(self.repo)
        self.assertIs(raised.exception, error)

    def test_bash_cli_path_spaces_overwrite_protection_and_force(self):
        spaced_repo = self.repo / "repo with spaces"
        spaced_repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=spaced_repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=spaced_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=spaced_repo, check=True)
        (spaced_repo / "seed.txt").write_text("seed\n", encoding="utf-8")
        subprocess.run(["git", "add", "seed.txt"], cwd=spaced_repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "feat: first entry"], cwd=spaced_repo, check=True)

        first = subprocess.run(["bash", str(SCRIPT), "--repo", str(spaced_repo)], text=True, capture_output=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        changelog = spaced_repo / "CHANGELOG.md"
        first_content = changelog.read_text(encoding="utf-8")
        second = subprocess.run(["bash", str(SCRIPT), "--repo", str(spaced_repo)], text=True, capture_output=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(changelog.read_text(encoding="utf-8"), first_content)

        changelog.write_text("preserve unless forced\n", encoding="utf-8")
        forced = subprocess.run(["bash", str(SCRIPT), "--repo", str(spaced_repo), "--force"], text=True, capture_output=True)
        self.assertEqual(forced.returncode, 0, forced.stderr)
        self.assertEqual(changelog.read_text(encoding="utf-8"), first_content)

    def test_empty_repository_fails_clearly_without_creating_output(self):
        empty_repo = self.repo / "empty repo"
        empty_repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=empty_repo, check=True)
        result = subprocess.run(["bash", str(SCRIPT), "--repo", str(empty_repo)], text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fatal:", result.stderr)
        self.assertFalse((empty_repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
