"""Offline unit and integration tests; every Git repository is disposable."""

import contextlib
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import changelog


SCRIPT = Path(__file__).resolve().with_name("changelog.sh")


class CategoryTests(unittest.TestCase):
    def test_conventional_types_scopes_and_breaking_changes(self):
        cases = {
            "feat: new API": "Added", "feat(api)!: replace API": "Added",
            "FEAT!: breaking change": "Added", "feature: export": "Added",
            "fix(parser): unicode": "Fixed", "hotfix: crash": "Fixed",
            "remove(api): obsolete endpoint": "Removed", "delete!: old flag": "Removed",
            "refactor: simplify": "Changed", "docs: examples": "Changed",
            "chore(deps): update": "Changed", "perf: faster": "Changed",
            "revert: undo change": "Changed", "": "Changed",
        }
        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(changelog.category(subject), expected)

    def test_plain_language_uses_first_word_not_substrings(self):
        cases = {
            "Add a route": "Added", "Fixed regression": "Fixed",
            "Remove legacy CLI": "Removed", "Drop old flag": "Removed",
            "Address the fix proposal": "Changed", "Update added examples": "Changed",
            "Prefix cleanup": "Changed", "Fixes tests": "Fixed",
        }
        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(changelog.category(subject), expected)

    def test_markdown_and_controls_are_escaped(self):
        escaped = changelog.markdown_text("[link](javascript:x) <script>& `code` *x*\t\x1b")
        self.assertEqual(escaped, r"\[link\]\(javascript:x\) &lt;script&gt;&amp; \`code\` \*x\*  ")


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repository with spaces"
        clean_environment = {key: value for key, value in os.environ.items()
                             if not key.startswith("GIT_")}
        clean_environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                                  "GIT_TERMINAL_PROMPT": "0"})
        environment_patch = mock.patch.dict(os.environ, clean_environment, clear=True)
        environment_patch.start()
        self.addCleanup(environment_patch.stop)
        self.repo.mkdir()
        self.command("init", "-q", "-b", "main")
        self.command("config", "user.name", "Changelog Tests")
        self.command("config", "user.email", "test@example.invalid")
        self.command("config", "commit.gpgsign", "false")
        self.command("config", "tag.gpgsign", "false")

    def command(self, *args):
        result = subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                                capture_output=True, text=True, timeout=15)
        return result.stdout.strip()

    def commit(self, subject):
        self.command("commit", "--allow-empty", "-q", "-m", subject)
        return self.command("rev-parse", "HEAD")

    def cli(self, *args, cwd=None):
        return subprocess.run(["bash", str(SCRIPT), "--repo", str(self.repo), *args],
                              cwd=cwd or self.base, capture_output=True, text=True, timeout=15)

    def test_latest_reachable_tag_is_exclusive_and_categories_present(self):
        old = self.commit("feat: old release")
        self.command("tag", "v1.0.0")
        new = [self.commit(subject) for subject in (
            "feat(cli): export", "fix: crash", "docs: clarify", "remove: old API")]
        root, document, count = changelog.generate(self.repo)
        self.assertEqual(root, self.repo)
        self.assertEqual(count, 4)
        self.assertNotIn("old release", document)
        self.assertIn(old, document)
        self.assertIn(new[-1], document)
        self.assertIn("### Added\n\n- feat", document)
        self.assertIn("### Fixed\n\n- fix", document)
        self.assertIn("### Changed\n\n- docs", document)
        self.assertIn("### Removed\n\n- remove", document)

    def test_no_tags_includes_all_history(self):
        first = self.commit("Initial commit")
        second = self.commit("feat: one")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 2)
        self.assertIn("No reachable tags", document)
        self.assertIn(first[:12], document)
        self.assertIn(second, document)

    def test_tag_at_head_produces_empty_sections(self):
        self.commit("feat: released")
        self.command("tag", "v1")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 0)
        self.assertEqual(document.count("_No changes._"), 4)
        self.assertNotIn("feat: released", document)

    def test_empty_repository_has_actionable_error(self):
        result = self.cli("--output", "-")
        self.assertEqual(result.returncode, 1)
        self.assertIn("Cannot resolve revision", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_non_repository_is_rejected(self):
        with self.assertRaisesRegex(changelog.ChangelogError, "working tree"):
            changelog.generate(self.base)

    def test_bare_repository_is_rejected(self):
        bare = self.base / "bare.git"
        self.command("init", "--bare", "-q", str(bare))
        with self.assertRaisesRegex(changelog.ChangelogError, "working tree"):
            changelog.generate(bare)

    def test_annotated_tag_is_supported(self):
        self.commit("feat: before")
        self.command("tag", "-a", "v1", "-m", "Release")
        self.commit("fix: after")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn("after **v1**", document)

    def test_nearest_lightweight_tag_beats_older_annotated_tag(self):
        self.commit("feat: first")
        self.command("tag", "-a", "v9", "-m", "Older release")
        self.commit("feat: second")
        self.command("tag", "v2")
        self.commit("fix: third")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn("after **v2**", document)

    def test_unmerged_tag_is_ignored(self):
        self.commit("feat: base")
        self.command("tag", "v1")
        self.command("checkout", "-q", "-b", "other")
        self.commit("feat: unrelated")
        self.command("tag", "v99")
        self.command("checkout", "-q", "main")
        self.commit("fix: main branch")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn("after **v1**", document)
        self.assertNotIn("unrelated", document)

    def test_only_unreachable_tags_fall_back_to_all_history(self):
        self.commit("Initial commit")
        self.command("checkout", "-q", "-b", "other")
        self.commit("feat: other")
        self.command("tag", "v1")
        self.command("checkout", "-q", "main")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn("No reachable tags", document)

    def test_tag_and_branch_name_collision_uses_tag(self):
        tag_sha = self.commit("feat: released")
        self.command("tag", "release")
        self.commit("fix: after tag")
        self.command("branch", "release")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn(tag_sha, document)

    def test_explicit_since_and_until_are_respected(self):
        first = self.commit("feat: first")
        second = self.commit("fix: second")
        self.commit("feat: third")
        _, document, count = changelog.generate(self.repo, since=first, until=second)
        self.assertEqual(count, 1)
        self.assertIn("fix: second", document)
        self.assertNotIn("feat: first", document)
        self.assertNotIn("feat: third", document)
        self.assertIn(second, document)

    def test_until_controls_automatic_tag_selection(self):
        first = self.commit("feat: first")
        self.command("tag", "v1")
        second = self.commit("fix: second")
        self.commit("feat: third")
        self.command("tag", "v2")
        _, document, count = changelog.generate(self.repo, until=second)
        self.assertEqual(count, 1)
        self.assertIn(first, document)
        self.assertIn("after **v1**", document)

    def test_equal_since_until_is_empty(self):
        sha = self.commit("feat: one")
        self.assertEqual(changelog.generate(self.repo, since=sha, until=sha)[2], 0)

    def test_non_ancestor_since_is_rejected(self):
        self.commit("Initial commit")
        self.command("checkout", "-q", "-b", "other")
        other = self.commit("feat: other")
        self.command("checkout", "-q", "main")
        self.commit("feat: main")
        with self.assertRaisesRegex(changelog.ChangelogError, "ancestor"):
            changelog.generate(self.repo, since=other)

    def test_invalid_and_option_like_revisions_do_not_execute(self):
        self.commit("Initial commit")
        for ref in ("does-not-exist", "--help", "HEAD; touch INJECTED", "$(touch INJECTED)"):
            with self.subTest(ref=ref):
                with self.assertRaisesRegex(changelog.ChangelogError, "Cannot resolve revision"):
                    changelog.generate(self.repo, since=ref)
        self.assertFalse((self.repo / "INJECTED").exists())
        self.assertFalse((Path.cwd() / "INJECTED").exists())

    def test_merge_subjects_excluded_by_default_and_opt_in(self):
        self.commit("Initial commit")
        self.command("tag", "v1")
        self.command("checkout", "-q", "-b", "feature")
        self.commit("feat: topic")
        self.command("checkout", "-q", "main")
        self.commit("fix: main")
        self.command("merge", "--no-ff", "--no-edit", "-m", "Merge feature", "feature")
        _, default, default_count = changelog.generate(self.repo)
        _, included, included_count = changelog.generate(self.repo, include_merges=True)
        self.assertEqual(default_count, 2)
        self.assertEqual(included_count, 3)
        self.assertNotIn("- Merge feature", default)
        self.assertIn("- Merge feature", included)

    def test_subjects_are_not_shell_or_markdown_code(self):
        sentinel = self.base / "EXECUTED"
        self.commit("feat: $(touch '{}') <script>alert(1)</script> [x](https://x.invalid)".format(sentinel))
        result = self.cli("--output", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(sentinel.exists())
        self.assertNotIn("<script>", result.stdout)
        self.assertIn("&lt;script&gt;", result.stdout)
        self.assertIn(r"\[x\]\(https://x.invalid\)", result.stdout)

    def test_unicode_and_commit_bodies(self):
        self.commit("feat: café 日本語 🚀\n\nBody with fake fix: should not be an entry")
        _, document, count = changelog.generate(self.repo)
        self.assertEqual(count, 1)
        self.assertIn("café 日本語 🚀", document)
        self.assertNotIn("Body with", document)

    def test_long_subject_is_not_truncated(self):
        subject = "fix: " + "x" * 20000
        self.commit(subject)
        self.assertIn(subject, changelog.generate(self.repo)[1])

    def test_deterministic_output_and_oldest_first_order(self):
        self.commit("feat: first")
        self.commit("feat: second")
        first = changelog.generate(self.repo)[1]
        self.assertEqual(first, changelog.generate(self.repo)[1])
        self.assertLess(first.index("feat: first"), first.index("feat: second"))
        self.assertTrue(first.endswith("\n"))

    def test_default_output_is_in_repository_root_from_any_cwd(self):
        self.commit("feat: works")
        subdirectory = self.repo / "nested"
        subdirectory.mkdir()
        result = self.cli(cwd=subdirectory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo / "CHANGELOG.md").is_file())
        self.assertFalse((subdirectory / "CHANGELOG.md").exists())
        self.assertIn("1 commits", result.stderr)

    def test_stdout_does_not_write_a_file(self):
        self.commit("feat: preview")
        result = self.cli("--output", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.startswith("# Changelog\n"))
        self.assertEqual(result.stderr, "")
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_existing_output_unchanged_without_force(self):
        self.commit("feat: one")
        output = self.repo / "CHANGELOG.md"
        output.write_text("Existing release notes\n", encoding="utf-8")
        result = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertIn("--force", result.stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "Existing release notes\n")

    def test_force_replaces_existing_output(self):
        self.commit("feat: one")
        output = self.repo / "CHANGELOG.md"
        output.write_text("Existing release notes\n", encoding="utf-8")
        result = self.cli("--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("feat: one", output.read_text(encoding="utf-8"))
        self.assertNotIn("Existing release notes", output.read_text(encoding="utf-8"))

    def test_symbolic_link_output_is_never_followed(self):
        self.commit("feat: one")
        target = self.base / "valuable.txt"
        target.write_text("Keep me", encoding="utf-8")
        (self.repo / "CHANGELOG.md").symlink_to(target)
        for args in ((), ("--force",)):
            result = self.cli(*args)
            self.assertEqual(result.returncode, 1)
            self.assertIn("symbolic-link", result.stderr)
        self.assertEqual(target.read_text(encoding="utf-8"), "Keep me")

    def test_missing_output_parent_has_no_traceback_or_partial_file(self):
        self.commit("feat: one")
        result = self.cli("--output", "missing/CHANGELOG.md")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse((self.repo / "missing").exists())

    def test_shallow_history_is_rejected(self):
        self.commit("feat: first")
        self.command("tag", "v1")
        self.commit("fix: second")
        shallow = self.base / "shallow"
        self.command("clone", "-q", "--depth", "1", self.repo.as_uri(), str(shallow))
        with self.assertRaisesRegex(changelog.ChangelogError, "Shallow history"):
            changelog.generate(shallow)

    def test_trailing_space_in_repository_name(self):
        self.commit("feat: first")
        renamed = self.base / "trailing space "
        self.repo.rename(renamed)
        self.repo = renamed
        self.assertEqual(changelog.generate(self.repo)[0], renamed)


class OutputAndErrorTests(unittest.TestCase):
    def test_atomic_no_clobber_race(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "CHANGELOG.md"
            real_link = os.link

            def racing_link(source, destination):
                Path(destination).write_text("Concurrent writer", encoding="utf-8")
                return real_link(source, destination)

            with mock.patch.object(changelog.os, "link", side_effect=racing_link):
                with self.assertRaisesRegex(changelog.ChangelogError, "not overwritten"):
                    changelog.write_output(output, "New content")
            self.assertEqual(output.read_text(encoding="utf-8"), "Concurrent writer")
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_write_failure_cleans_temporary_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "CHANGELOG.md"
            with mock.patch.object(changelog.os, "fsync", side_effect=OSError("disk failure")):
                with self.assertRaisesRegex(OSError, "disk failure"):
                    changelog.write_output(output, "New content")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_missing_git_has_friendly_error(self):
        with mock.patch.object(changelog.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(changelog.ChangelogError, "Git is required"):
                changelog.git(Path("."), "status")

    def test_git_timeout_has_friendly_error(self):
        failure = subprocess.TimeoutExpired(cmd="git", timeout=60)
        with mock.patch.object(changelog.subprocess, "run", side_effect=failure):
            with self.assertRaisesRegex(changelog.ChangelogError, "60-second"):
                changelog.git(Path("."), "status")

    def test_cli_output_failure_is_friendly(self):
        stderr = io.StringIO()
        with mock.patch.object(changelog, "generate", return_value=(Path("."), "document", 1)):
            with mock.patch.object(changelog, "write_output", side_effect=OSError("disk full")):
                with contextlib.redirect_stderr(stderr):
                    result = changelog.main([])
        self.assertEqual(result, 1)
        self.assertIn("error: disk full", stderr.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
