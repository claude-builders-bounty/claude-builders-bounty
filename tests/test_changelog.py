import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "changelog.sh"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "a repository with spaces"
        self.repo.mkdir()
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_AUTHOR_DATE": "2001-01-01T00:00:00Z", "GIT_COMMITTER_DATE": "2001-01-01T00:00:00Z"}
        self.git("init", "-q")
        self.git("config", "user.name", "Test Maintainer")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "core.hooksPath", "/dev/null")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], env=self.env,
                              capture_output=True, text=True, check=True).stdout.strip()

    def commit(self, subject):
        self.git("commit", "-q", "--allow-empty", "-m", subject)
        return self.git("rev-parse", "HEAD")[:12]

    def run_tool(self, *args, cwd=None):
        return subprocess.run(["bash", str(SCRIPT), *args], cwd=cwd or self.repo,
                              env=self.env, capture_output=True, text=True)

    def generate(self, *args):
        result = self.run_tool(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertIn("Wrote ", result.stdout)
        return (self.repo / "CHANGELOG.md").read_text()

    def test_four_conventional_categories_and_fallback(self):
        self.commit("feat(api)!: Introduce search")
        self.commit("fix(parser): Accept empty input")
        self.commit("refactor: Simplify storage")
        self.commit("remove: Retire legacy API")
        self.commit("Update translations")
        output = self.generate()
        self.assertIn("### Added\n\n- Introduce search", output)
        self.assertIn("### Fixed\n\n- Accept empty input", output)
        self.assertIn("### Changed\n\n- Simplify storage", output)
        self.assertIn("- Update translations", output)
        self.assertIn("### Removed\n\n- Retire legacy API", output)

    def test_imperative_and_past_tense_subjects(self):
        for subject in ["Added parser", "Fix empty input", "Removed legacy API", "Changed timeout"]:
            self.commit(subject)
        output = self.generate()
        for category, subject in [("Added", "Added parser"), ("Fixed", "Fix empty input"),
                                  ("Removed", "Removed legacy API"), ("Changed", "Changed timeout")]:
            self.assertIn(f"### {category}\n\n- {subject}", output)

    def test_plain_add_is_added_and_unrelated_word_is_changed(self):
        self.commit("Add parser")
        self.commit("Address parser warnings")
        output = self.generate()
        self.assertIn("### Added\n\n- Add parser", output)
        self.assertIn("### Changed\n\n- Address parser warnings", output)

    def test_significant_repository_path_whitespace_is_preserved(self):
        self.commit("Add whitespace support")
        original = self.repo
        for name in ["trailing space ", "trailing tab\t", "trailing newline\n", "carriage return\r", " leading space"]:
            with self.subTest(name=repr(name)):
                destination = Path(self.temp.name) / name
                self.repo.rename(destination)
                self.repo = destination
                output = self.generate()
                self.assertIn("### Added\n\n- Add whitespace support", output)
                (self.repo / "CHANGELOG.md").unlink()
        self.repo.rename(original)
        self.repo = original

    def test_lightweight_tag_excludes_tagged_history(self):
        self.commit("feat: old feature")
        self.git("tag", "v1.0")
        commit = self.commit("fix: new fix")
        output = self.generate()
        self.assertNotIn("old feature", output)
        self.assertIn(f"- new fix (`{commit}`)", output)
        self.assertIn("Changes since `v1.0`.", output)

    def test_annotated_tag_and_unreachable_tag(self):
        self.commit("feat: baseline")
        self.git("tag", "-a", "v1.0", "-m", "release")
        main = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "--orphan", "unrelated")
        self.commit("feat: unrelated")
        self.git("tag", "v999")
        self.git("checkout", "-q", "--detach", main)
        self.commit("fix: relevant fix")
        output = self.generate()
        self.assertIn("Changes since `v1.0`.", output)
        self.assertNotIn("unrelated", output)
        self.assertIn("relevant fix", output)

    def test_nearest_tag_instead_of_lexical_version(self):
        self.commit("initial")
        self.git("tag", "v99")
        self.commit("feat: earlier")
        self.git("tag", "v2")
        self.commit("fix: latest")
        output = self.generate()
        self.assertIn("Changes since `v2`.", output)
        self.assertNotIn("earlier", output)

    def test_head_at_tag_has_no_fabricated_changes(self):
        self.commit("feat: already released")
        self.git("tag", "release")
        output = self.generate()
        self.assertNotIn("already released", output)
        self.assertEqual(output.count("_No changes._"), 4)

    def test_no_tags_uses_all_history(self):
        self.commit("feat: first")
        self.commit("fix: second")
        output = self.generate()
        self.assertIn("no reachable tag", output)
        self.assertIn("first", output)
        self.assertIn("second", output)

    def test_rerun_refuses_existing_file_and_explicit_overwrite_is_deterministic(self):
        self.commit("feat: one")
        first = self.generate()
        result = self.run_tool()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("already exists", result.stderr)
        self.assertEqual((self.repo / "CHANGELOG.md").read_text(), first)
        self.assertEqual(self.generate("--overwrite"), first)

    def test_authored_changelog_is_preserved(self):
        self.commit("fix: one")
        path = self.repo / "CHANGELOG.md"
        path.write_text("My curated release history\n")
        result = self.run_tool()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(path.read_text(), "My curated release history\n")

    def test_symlink_is_refused_and_overwrite_replaces_link_without_touching_target(self):
        self.commit("fix: one")
        target = Path(self.temp.name) / "authored.txt"
        target.write_text("keep me")
        (self.repo / "CHANGELOG.md").symlink_to(target)
        self.assertEqual(self.run_tool().returncode, 1)
        self.generate("--overwrite")
        self.assertEqual(target.read_text(), "keep me")
        self.assertFalse((self.repo / "CHANGELOG.md").is_symlink())

    def test_non_git_and_empty_repository_fail_without_output(self):
        empty = self.run_tool()
        self.assertEqual(empty.returncode, 1)
        self.assertIn("no commits", empty.stderr)
        outside = Path(self.temp.name) / "not git"
        outside.mkdir()
        result = self.run_tool("--repo", str(outside))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not a git repository", result.stderr)
        self.assertFalse((outside / "CHANGELOG.md").exists())

    def test_unicode_markup_and_shell_metacharacters_are_data(self):
        self.commit("feat: café $(touch PWNED) `touch OTHER` [link](javascript:x) <script> & _bold_")
        output = self.generate()
        self.assertIn("café $(touch PWNED)", output)
        self.assertIn(r"\`touch OTHER\`", output)
        self.assertIn(r"\[link\]", output)
        self.assertIn("&lt;script&gt; &amp;", output)
        self.assertIn(r"\_bold\_", output)
        self.assertFalse((self.repo / "PWNED").exists())
        self.assertFalse((self.repo / "OTHER").exists())

    def test_repo_option_and_explicit_output_with_spaces(self):
        self.commit("add: convenient invocation")
        target = Path(self.temp.name) / "release draft.md"
        result = self.run_tool("--repo", str(self.repo), "--output", str(target), cwd=Path(self.temp.name))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("convenient invocation", target.read_text())
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_help_and_invalid_option(self):
        self.assertEqual(self.run_tool("--help").returncode, 0)
        self.assertEqual(self.run_tool("--not-an-option").returncode, 2)


if __name__ == "__main__":
    unittest.main()
