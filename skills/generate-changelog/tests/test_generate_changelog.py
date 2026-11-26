"""Tests for generate_changelog.py — stdlib unittest, no pytest needed.

Run:  python3 -m unittest discover -s tests -v
       python3 -m pytest tests/ -q        (optional)
"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import generate_changelog as gc  # noqa: E402


def C(subject, body="", sha="abc1234"):
    return gc.Commit(sha=sha, subject=subject, body=body)


class TestClassifyConventional(unittest.TestCase):
    def test_feat_is_added(self):
        e = gc.classify(C("feat: add dark mode"))
        self.assertEqual((e.category, e.text), ("Added", "Add dark mode"))

    def test_feat_with_scope_keeps_scope(self):
        e = gc.classify(C("feat(auth): add login"))
        self.assertEqual((e.category, e.text), ("Added", "Add login (auth)"))

    def test_fix_is_fixed(self):
        e = gc.classify(C("fix: crash on empty input"))
        self.assertEqual((e.category, e.text), ("Fixed", "Crash on empty input"))

    def test_fix_with_scope(self):
        e = gc.classify(C("fix(parser): handle null bytes"))
        self.assertEqual(e.category, "Fixed")

    def test_security_is_fixed(self):
        e = gc.classify(C("security: patch XSS in comments"))
        self.assertEqual(e.category, "Fixed")

    def test_refactor_perf_chore_are_changed(self):
        for subject in ("refactor: split utils module",
                        "perf: speed up log parsing",
                        "chore: bump deps",
                        "docs: update README",
                        "ci: add windows job",
                        "style: run black",
                        "test: add regression test"):
            with self.subTest(subject=subject):
                self.assertEqual(gc.classify(C(subject)).category, "Changed")

    def test_remove_types_are_removed(self):
        for subject in ("remove: legacy API endpoint",
                        "delete: old migration",
                        "drop: support for python 3.7",
                        "deprecate: v1 auth flow"):
            with self.subTest(subject=subject):
                self.assertEqual(gc.classify(C(subject)).category, "Removed")

    def test_breaking_bang_goes_to_changed(self):
        e = gc.classify(C("feat!: drop v1 API"))
        self.assertEqual(e.category, "Changed")
        self.assertTrue(e.breaking)

    def test_breaking_change_in_body(self):
        e = gc.classify(C("feat: new parser", body="BREAKING CHANGE: old flags removed"))
        self.assertEqual(e.category, "Changed")
        self.assertTrue(e.breaking)

    def test_unknown_conventional_type_falls_back_to_keywords(self):
        e = gc.classify(C("wip: fix the login bug"))
        self.assertEqual(e.category, "Fixed")

    def test_case_insensitive_type(self):
        e = gc.classify(C("FEAT: add search"))
        self.assertEqual(e.category, "Added")


class TestClassifyKeywords(unittest.TestCase):
    def test_add_keyword(self):
        self.assertEqual(gc.classify(C("Add new export button")).category, "Added")

    def test_introduce_and_implement_are_added(self):
        self.assertEqual(gc.classify(C("Introduce caching layer")).category, "Added")
        self.assertEqual(gc.classify(C("Implement OAuth login")).category, "Added")

    def test_fix_keywords(self):
        for s in ("Fix crash on startup", "Patch memory leak",
                  "Resolve race condition", "Correct typo in docs"):
            with self.subTest(s=s):
                self.assertEqual(gc.classify(C(s)).category, "Fixed")

    def test_removed_beats_fixed_in_priority(self):
        # "remove the fix" must not be misfiled as a fix.
        e = gc.classify(C("Remove the temporary fix for login"))
        self.assertEqual(e.category, "Removed")

    def test_removed_keywords(self):
        for s in ("Remove unused helper", "Delete temp files",
                  "Drop python 2 support", "Deprecate old flag"):
            with self.subTest(s=s):
                self.assertEqual(gc.classify(C(s)).category, "Removed")

    def test_changed_keywords(self):
        for s in ("Update dependencies", "Improve error messages",
                  "Rename config key", "Refactor auth module"):
            with self.subTest(s=s):
                self.assertEqual(gc.classify(C(s)).category, "Changed")

    def test_unknown_goes_to_changed_not_dropped(self):
        e = gc.classify(C("Misc tweaks"))
        self.assertEqual((e.category, e.text), ("Changed", "Misc tweaks"))

    def test_empty_subject_is_skipped(self):
        self.assertIsNone(gc.classify(C("   ")))

    def test_merge_skipped_by_default(self):
        self.assertIsNone(gc.classify(C("Merge pull request #42 from foo/bar")))

    def test_merge_included_when_asked(self):
        buckets = gc.categorize([C("Merge pull request #42 from foo/bar")],
                                include_merges=True)
        self.assertEqual(len(buckets["Changed"]), 1)

    def test_revert_kept_under_changed(self):
        e = gc.classify(C('Revert "feat: add X"'))
        self.assertEqual(e.category, "Changed")
        self.assertTrue(e.text.startswith("Revert:"))

    def test_description_cleaning(self):
        e = gc.classify(C("feat: add search."))
        self.assertEqual(e.text, "Add search")


class TestCategorize(unittest.TestCase):
    def test_buckets_and_order(self):
        commits = [C("feat: add a"), C("fix: fix b"), C("feat: add c")]
        buckets = gc.categorize(commits)
        self.assertEqual([e.text for e in buckets["Added"]], ["Add a", "Add c"])
        self.assertEqual([e.text for e in buckets["Fixed"]], ["Fix b"])
        self.assertEqual(buckets["Removed"], [])

    def test_dedup_case_insensitive(self):
        commits = [C("feat: add login"), C("Add Login"), C("fix: fix typo")]
        buckets = gc.categorize(commits)
        self.assertEqual(len(buckets["Added"]), 1)
        self.assertEqual(len(buckets["Fixed"]), 1)

    def test_breaking_gets_marker(self):
        buckets = gc.categorize([C("feat!: new API")])
        self.assertTrue(buckets["Changed"][0].text.startswith("⚠ BREAKING: "))


class TestRender(unittest.TestCase):
    def test_section_order_and_empty_sections_omitted(self):
        buckets = {"Added": [gc.Entry("Added", "Add a")],
                   "Fixed": [], "Changed": [gc.Entry("Changed", "Tweak b")],
                   "Removed": []}
        out = gc.render(buckets, "Unreleased", "2026-11-12", "v1.0.0", 2)
        self.assertIn("# Changelog", out)
        self.assertIn("## [Unreleased] - 2026-11-12", out)
        self.assertLess(out.index("### Added"), out.index("### Changed"))
        self.assertNotIn("### Fixed", out)
        self.assertNotIn("### Removed", out)
        self.assertIn("- Add a", out)

    def test_empty_range_still_valid_file(self):
        out = gc.render({c: [] for c in gc.CATEGORIES}, "Unreleased",
                        "2026-11-12", "v1.0.0", 0)
        self.assertIn("No changes since v1.0.0.", out)

    def test_show_hashes(self):
        buckets = {"Added": [gc.Entry("Added", "Add a", sha="abcdef123456")],
                   "Fixed": [], "Changed": [], "Removed": []}
        out = gc.render(buckets, "Unreleased", "2026-11-12", None, 1,
                        show_hashes=True)
        self.assertIn("- Add a (abcdef1)", out)


class GitRepoTestCase(unittest.TestCase):
    """End-to-end tests in real temporary git repos."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.com")
        self._git("config", "user.name", "Test")
        self._git("config", "commit.gpgsign", "false")

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args, **kw):
        env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-01T00:00:00Z",
                   GIT_COMMITTER_DATE="2026-01-01T00:00:00Z")
        subprocess.run(["git", "-C", self.repo, *args], check=True,
                       capture_output=True, text=True, env=env, **kw)

    def _commit(self, filename, content, message):
        with open(os.path.join(self.repo, filename), "w") as fh:
            fh.write(content)
        self._git("add", ".")
        self._git("commit", "-m", message)

    def test_last_tag_none_without_tags(self):
        self._commit("a.txt", "x", "feat: add a")
        self.assertIsNone(gc.get_last_tag(self.repo))

    def test_get_commits_since_tag(self):
        self._commit("a.txt", "x", "feat: add a")
        self._git("tag", "v0.1.0")
        self._commit("b.txt", "y", "fix: fix b")
        self._commit("c.txt", "z", "docs: update readme")
        self.assertEqual(gc.get_last_tag(self.repo), "v0.1.0")
        commits = gc.get_commits(self.repo, "v0.1.0")
        self.assertEqual([c.subject for c in commits],
                         ["docs: update readme", "fix: fix b"])

    def test_full_run_no_tag(self):
        self._commit("a.txt", "x", "feat: add a")
        self._commit("b.txt", "y", "fix: fix b")
        rc = gc.main(["--repo", self.repo, "--output",
                      os.path.join(self.repo, "CHANGELOG.md")])
        self.assertEqual(rc, 0)
        with open(os.path.join(self.repo, "CHANGELOG.md")) as fh:
            out = fh.read()
        self.assertIn("### Added", out)
        self.assertIn("- Add a", out)
        self.assertIn("### Fixed", out)
        self.assertIn("- Fix b", out)

    def test_full_run_empty_since_tag(self):
        self._commit("a.txt", "x", "feat: add a")
        self._git("tag", "v0.1.0")
        rc = gc.main(["--repo", self.repo, "--output",
                      os.path.join(self.repo, "CHANGELOG.md")])
        self.assertEqual(rc, 0)
        with open(os.path.join(self.repo, "CHANGELOG.md")) as fh:
            self.assertIn("No changes since v0.1.0.", fh.read())

    def test_dry_run_writes_nothing(self):
        self._commit("a.txt", "x", "feat: add a")
        rc = gc.main(["--repo", self.repo, "--dry-run"])
        self.assertEqual(rc, 0)
        self.assertFalse(os.path.exists(os.path.join(self.repo, "CHANGELOG.md")))

    def test_multiline_body_breaking_change(self):
        self._commit("a.txt", "x", "feat: new api")
        # Amend the body via a second commit with a breaking body.
        with open(os.path.join(self.repo, "b.txt"), "w") as fh:
            fh.write("y")
        self._git("add", ".")
        env = dict(os.environ, GIT_AUTHOR_DATE="2026-01-02T00:00:00Z",
                   GIT_COMMITTER_DATE="2026-01-02T00:00:00Z")
        subprocess.run(["git", "-C", self.repo, "commit", "-m",
                        "feat: new parser", "-m",
                        "BREAKING CHANGE: old flags removed"],
                       check=True, capture_output=True, text=True, env=env)
        commits = gc.get_commits(self.repo, None)
        buckets = gc.categorize(commits)
        self.assertTrue(any(e.text.startswith("⚠ BREAKING:")
                            for e in buckets["Changed"]))


class TestCLIAndExtras(unittest.TestCase):
    def test_version_flag(self):
        self.assertEqual(gc.main(["--version-flag"]), 0)

    def test_scope_with_breaking_bang(self):
        e = gc.classify(C("feat(auth)!: change token format"))
        self.assertEqual(e.category, "Changed")
        self.assertTrue(e.breaking)

    def test_deprecate_free_text_is_removed(self):
        self.assertEqual(gc.classify(C("Deprecate the v1 endpoint")).category,
                         "Removed")

    def test_categorize_preserves_order_within_category(self):
        commits = [C("fix: first bug"), C("feat: new thing"), C("fix: second bug")]
        buckets = gc.categorize(commits)
        self.assertEqual([e.text for e in buckets["Fixed"]],
                         ["First bug", "Second bug"])

    def test_render_uses_given_version_label(self):
        out = gc.render({c: [] for c in gc.CATEGORIES}, "1.2.0",
                        "2026-11-12", "v1.1.0", 0)
        self.assertIn("## [1.2.0] - 2026-11-12", out)

    def test_get_commits_parses_body(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "-C", d, "init", "-b", "main"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.email", "t@e.c"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.name", "T"],
                           check=True, capture_output=True)
            with open(os.path.join(d, "a.txt"), "w") as fh:
                fh.write("x")
            subprocess.run(["git", "-C", d, "add", "."], check=True,
                           capture_output=True)
            subprocess.run(["git", "-C", d, "commit", "-m", "feat: new api",
                            "-m", "BREAKING CHANGE: old flags removed"],
                           check=True, capture_output=True)
            commits = gc.get_commits(d, None)
            self.assertEqual(len(commits), 1)
            self.assertIn("BREAKING CHANGE", commits[0].body)

    def test_cli_since_flag_limits_range(self):
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "-C", d, "init", "-b", "main"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.email", "t@e.c"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.name", "T"],
                           check=True, capture_output=True)
            with open(os.path.join(d, "a.txt"), "w") as fh:
                fh.write("x")
            subprocess.run(["git", "-C", d, "add", "."], check=True,
                           capture_output=True)
            subprocess.run(["git", "-C", d, "commit", "-m", "feat: add a"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "tag", "v0.1.0"], check=True,
                           capture_output=True)
            rc = gc.main(["--repo", d, "--since", "v0.1.0", "--dry-run"])
            self.assertEqual(rc, 0)

    def test_changelog_sh_wrapper_runs(self):
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with tempfile.TemporaryDirectory() as d:
            subprocess.run(["git", "-C", d, "init", "-b", "main"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.email", "t@e.c"],
                           check=True, capture_output=True)
            subprocess.run(["git", "-C", d, "config", "user.name", "T"],
                           check=True, capture_output=True)
            with open(os.path.join(d, "a.txt"), "w") as fh:
                fh.write("x")
            subprocess.run(["git", "-C", d, "add", "."], check=True,
                           capture_output=True)
            subprocess.run(["git", "-C", d, "commit", "-m", "feat: add a"],
                           check=True, capture_output=True)
            result = subprocess.run(
                ["bash", os.path.join(skill_dir, "changelog.sh"),
                 "--repo", d, "--dry-run"],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("- Add a", result.stdout)


if __name__ == "__main__":
    unittest.main()
