"""CLI integration tests; all histories here are synthetic disposable fixtures."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]
PYTHON_ONLY = os.environ.get("CHANGELOG_TEST_PYTHON_ONLY") == "1"
ENTRY = [sys.executable, str(SOURCE / "changelog.py")] if PYTHON_ONLY else ["bash", str(SOURCE / "changelog.sh")]


class ChangelogCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog-tests-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo with spaces & café"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Fixture Author")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", "-C", str(cwd or self.repo), *args], capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        return result.stdout.decode("utf-8", "replace").strip()

    def commit(self, message):
        self.git("-c", "core.hooksPath=", "commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def run_cli(self, *args, cwd=None, env=None, success=True):
        result = subprocess.run([*ENTRY, *args], cwd=cwd or self.repo, env=env,
                                capture_output=True, check=False)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        else:
            self.assertNotEqual(result.returncode, 0, "Expected a real CLI failure")
        return result

    def output(self):
        return (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")

    def section(self, output, name):
        return output.split("### " + name + "\n", 1)[1].split("\n### ", 1)[0]

    def test_exclusive_tag_boundary_and_four_categories(self):
        old = self.commit("add old content")
        self.git("tag", "v1.0.0")
        values = {"Added": "feat(ui): new panel", "Fixed": "fix: save failure",
                  "Changed": "refactor: simplify state", "Removed": "remove: obsolete switch"}
        for subject in values.values():
            self.commit(subject)
        self.run_cli()
        output = self.output()
        self.assertNotIn(old[:12], output)
        self.assertIn("4 commit(s)", output)
        for section, subject in values.items():
            self.assertIn(subject, self.section(output, section))

    def test_scopes_breaking_markers_and_plain_words(self):
        for subject in ["feat(core)!: behavior", "FIX(cache): bug", "Added a file", "Drop legacy flag"]:
            self.commit(subject)
        self.run_cli()
        output = self.output()
        self.assertIn("behavior", self.section(output, "Added"))
        self.assertIn("Added a file", self.section(output, "Added"))
        self.assertIn("bug", self.section(output, "Fixed"))
        self.assertIn("legacy flag", self.section(output, "Removed"))

    def test_unknown_subject_and_revert_remain_changed(self):
        for subject in ['Revert "remove feature"', "fixture: not a fix", "address not an add", "docs: help"]:
            self.commit(subject)
        self.run_cli()
        self.assertEqual(self.section(self.output(), "Changed").count("(`"), 4)

    def test_no_tag_includes_all_commits(self):
        first = self.commit("add first")
        second = self.commit("fix second")
        self.run_cli()
        self.assertIn("No reachable tag", self.output())
        self.assertIn(first[:12], self.output())
        self.assertIn(second[:12], self.output())

    def test_empty_repository(self):
        self.run_cli()
        self.assertIn("no commits yet", self.output())
        self.assertEqual(self.output().count("- None."), 4)

    def test_head_at_tag_has_no_changes(self):
        self.commit("feat: already released")
        self.git("tag", "-a", "v2", "-m", "release")
        self.run_cli()
        self.assertIn("0 commit(s)", self.output())
        self.assertNotIn("already released", self.output())

    def test_nearest_reachable_tag_not_highest_version(self):
        self.commit("before")
        self.git("tag", "v999")
        self.commit("fix: released")
        self.git("tag", "-a", "v2", "-m", "release")
        last = self.commit("feat: after nearest")
        self.run_cli()
        self.assertIn("Since tag **v2**", self.output())
        self.assertIn("1 commit(s)", self.output())
        self.assertIn(last[:12], self.output())

    def test_unreachable_tag_is_ignored(self):
        self.commit("base")
        self.git("switch", "-q", "-c", "other")
        self.commit("other tagged work")
        self.git("tag", "v1000")
        self.git("switch", "-q", "main")
        self.commit("fix: main")
        self.run_cli()
        self.assertIn("No reachable tag", self.output())
        self.assertNotIn("other tagged work", self.output())

    def test_merge_and_side_commits_are_retained(self):
        self.commit("base")
        self.git("tag", "v1")
        self.git("switch", "-q", "-c", "side")
        side = self.commit("feat: side feature")
        self.git("switch", "-q", "main")
        main = self.commit("fix: main correction")
        self.git("merge", "-q", "--no-ff", "side", "-m", "Merge side")
        merge = self.git("rev-parse", "HEAD")
        self.run_cli()
        for commit in [side, main, merge]:
            self.assertIn(commit[:12], self.output())
        self.assertIn("3 commit(s)", self.output())

    def test_detached_head(self):
        self.commit("base")
        self.git("tag", "v1")
        commit = self.commit("add detached content")
        self.git("switch", "-q", "--detach", commit)
        self.run_cli()
        self.assertIn(commit, self.output())

    def test_multiline_unicode_and_markup_are_plain_text(self):
        self.commit("feat: café 日本語 <script> [click](bad) `code`\n\nremove: body is not another entry")
        self.run_cli()
        output = self.output()
        self.assertIn("café 日本語", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<script>", output)
        self.assertIn(r"\[click\]", output)
        self.assertIn(r"\`code\`", output)
        self.assertNotIn("body is not", output)
        self.assertIn("1 commit(s)", output)

    def test_shell_metacharacters_are_never_executed(self):
        self.commit("base")
        self.git("tag", "v1;$(touch-PWNED)")
        self.commit('fix: $(touch PWNED) `touch PWNED` ; echo bad')
        self.run_cli()
        self.assertFalse((self.repo / "PWNED").exists())
        self.assertIn("touch PWNED", self.output())
        self.assertIn("1 commit(s)", self.output())

    def test_nested_cwd_writes_at_repository_root(self):
        self.commit("add content")
        nested = self.repo / "a" / "nested folder"
        nested.mkdir(parents=True)
        self.run_cli(cwd=nested)
        self.assertTrue((self.repo / "CHANGELOG.md").is_file())
        self.assertFalse((nested / "CHANGELOG.md").exists())

    def test_explicit_repo_and_output_with_unusual_path(self):
        self.commit("fix: path")
        self.run_cli("--repo", str(self.repo), "--output", "release & notes.md", cwd=self.base)
        self.assertIn("fix: path", (self.repo / "release & notes.md").read_text())

    def test_rerun_identical_and_history_unchanged(self):
        self.commit("feat: stable")
        self.git("tag", "v1")
        self.commit("fix: repeat")
        before = (self.git("rev-parse", "HEAD"), self.git("show-ref"))
        self.run_cli()
        one = (self.repo / "CHANGELOG.md").read_bytes()
        self.run_cli()
        self.assertEqual(one, (self.repo / "CHANGELOG.md").read_bytes())
        self.assertEqual(before, (self.git("rev-parse", "HEAD"), self.git("show-ref")))
        self.assertFalse(list(self.repo.glob(".changelog-*")))

    def test_invalid_repository_preserves_output(self):
        target = self.base / "existing.md"
        target.write_text("keep me")
        result = self.run_cli("--repo", str(self.base), "--output", str(target), success=False)
        self.assertIn(b"changelog:", result.stderr)
        self.assertEqual(target.read_text(), "keep me")

    def test_unwritable_destination_fails_and_cleans_temp(self):
        self.commit("add content")
        target = self.repo / "directory.md"
        target.mkdir()
        self.run_cli("--output", "directory.md", success=False)
        self.assertTrue(target.is_dir())
        self.assertFalse(list(self.repo.glob(".changelog-*")))

    def test_output_cannot_overwrite_git_metadata(self):
        self.commit("base")
        before = (self.repo / ".git" / "HEAD").read_bytes()
        self.run_cli("--output", ".git/HEAD", success=False)
        self.assertEqual(before, (self.repo / ".git" / "HEAD").read_bytes())

    def test_shallow_history_is_rejected_without_replacing_output(self):
        self.commit("base")
        self.git("tag", "v1")
        self.commit("fix: next")
        shallow = self.base / "shallow"
        self.git("clone", "-q", "--depth", "1", self.repo.as_uri(), str(shallow))
        (shallow / "CHANGELOG.md").write_text("old history")
        result = self.run_cli("--repo", str(shallow), success=False)
        self.assertIn(b"Shallow history", result.stderr)
        self.assertEqual((shallow / "CHANGELOG.md").read_text(), "old history")

    def test_new_output_is_not_owner_only(self):
        self.commit("add content")
        self.run_cli()
        mode = (self.repo / "CHANGELOG.md").stat().st_mode & 0o777
        umask = os.umask(0)
        os.umask(umask)
        self.assertEqual(mode, 0o666 & ~umask)

    def test_replaced_output_keeps_existing_mode(self):
        self.commit("add content")
        target = self.repo / "CHANGELOG.md"
        target.write_text("old")
        target.chmod(0o640)
        self.run_cli()
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_missing_git_is_a_nonzero_error(self):
        env = os.environ.copy()
        env["PATH"] = str(self.base / "nonexistent")
        result = subprocess.run([sys.executable, str(SOURCE / "changelog.py"), "--repo", str(self.repo)],
                                env=env, capture_output=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"changelog:", result.stderr)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    print("Entry point: " + ("Python helper (local control)" if PYTHON_ONLY else "actual bash changelog.sh"), flush=True)
    unittest.main(verbosity=2)
