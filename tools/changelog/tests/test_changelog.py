"""Stdlib-only unit tests for tools/changelog/generate_changelog.py.

Run from the bounty repo root:

    python tools/changelog/tests/test_changelog.py -v
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parent.parent))

import generate_changelog as gc  # noqa: E402


def C(subject: str, body: str = "", sha: str = "abcdef0", author: str = "Alice") -> gc.Commit:
    return gc.Commit(
        sha=sha + "0" * 33,
        short_sha=sha[:7],
        subject=subject,
        body=body,
        author=author,
        email=f"{author.lower()}@example.com",
    )


# ---------------------------------------------------------------------------
# Categorization
# ---------------------------------------------------------------------------


class CategorizeConventional(unittest.TestCase):
    cases = [
        ("feat: add login button", "Added"),
        ("feat(auth): add SSO", "Added"),
        ("fix: handle null response", "Fixed"),
        ("fix(api): handle 503", "Fixed"),
        ("perf: cache regex compile", "Changed"),
        ("refactor: extract helper", "Changed"),
        ("revert: drop legacy adapter", "Removed"),
        ("deps: bump dependency", "Changed"),
    ]

    def test_buckets(self):
        for subject, expected in self.cases:
            with self.subTest(subject=subject):
                bucket, _ = gc.categorize(C(subject))
                self.assertEqual(bucket, expected, subject)


class CategorizeSkipped(unittest.TestCase):
    skip_subjects = [
        "chore: update deps",
        "docs: fix typo",
        "test: cover edge case",
        "style: reformat",
        "build: update CI",
        "ci: bump runner",
    ]

    def test_skipped_by_default(self):
        for subject in self.skip_subjects:
            with self.subTest(subject=subject):
                bucket, _ = gc.categorize(C(subject))
                self.assertIsNone(bucket, f"{subject!r} should be filtered")

    def test_included_when_requested(self):
        bucket, _ = gc.categorize(C("chore: update deps"), include_skipped=True)
        self.assertEqual(bucket, "Changed")


class CategorizeVerbHeuristics(unittest.TestCase):
    cases = [
        ("Add login button", "Added"),
        ("Adds login button", "Added"),
        ("Implement OAuth flow", "Added"),
        ("Introduce feature flags", "Added"),
        ("Fix race condition in cache", "Fixed"),
        ("Resolve flaky test", "Fixed"),
        ("Patch security advisory", "Fixed"),
        ("Update API client to v3", "Changed"),
        ("Improve performance of N+1 query", "Changed"),
        ("Bump axios to 1.7.0", "Changed"),
        ("Migrate from Redis to Postgres", "Changed"),
        ("Remove legacy auth path", "Removed"),
        ("Drop python 3.8 support", "Removed"),
        ("Deprecate /v1 endpoints", "Removed"),
    ]

    def test_verb_buckets(self):
        for subject, expected in self.cases:
            with self.subTest(subject=subject):
                bucket, _ = gc.categorize(C(subject))
                self.assertEqual(bucket, expected, subject)


class CategorizeBreaking(unittest.TestCase):
    def test_breaking_in_body_marked(self):
        commit = C("feat: rework auth", body="BREAKING CHANGE: removes legacy token format")
        self.assertTrue(commit.has_breaking)

    def test_breaking_marker_in_subject(self):
        commit = C("feat!: rework auth")
        self.assertTrue(commit.has_breaking)


class CategorizeFallback(unittest.TestCase):
    def test_unknown_subject_falls_to_changed(self):
        bucket, headline = gc.categorize(C("Misc work"))
        self.assertEqual(bucket, "Changed")
        self.assertEqual(headline, "Misc work")


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


class RenderSection(unittest.TestCase):
    def test_renders_all_buckets_when_present(self):
        commits = [
            C("feat: add login", sha="aaaa111"),
            C("fix: handle nulls", sha="bbbb222"),
            C("refactor: rename module", sha="cccc333"),
            C("revert: drop adapter", sha="dddd444"),
        ]
        section, buckets = gc.render_section(commits, "v1.0.0", date(2026, 5, 9))
        self.assertIn("## [v1.0.0] - 2026-05-09", section)
        self.assertIn("### Added", section)
        self.assertIn("### Fixed", section)
        self.assertIn("### Changed", section)
        self.assertIn("### Removed", section)
        for bucket, items in buckets.items():
            with self.subTest(bucket=bucket):
                self.assertEqual(len(items), 1)

    def test_breaking_banner_when_present(self):
        commits = [C("feat!: rework auth", sha="aaaa111")]
        section, _ = gc.render_section(commits, "v2.0.0", date(2026, 5, 9))
        self.assertIn("BREAKING", section)
        self.assertIn("⚠️", section)

    def test_empty_when_only_skipped(self):
        commits = [C("chore: bump deps"), C("docs: typo")]
        section, _ = gc.render_section(commits, "v1.0.1", date(2026, 5, 9))
        self.assertIn("No notable changes", section)
        self.assertNotIn("### Added", section)

    def test_repo_url_renders_commit_links(self):
        commits = [C("feat: something", sha="aaaa111")]
        section, _ = gc.render_section(
            commits, "v1.0.0", date(2026, 5, 9),
            repo_url="https://github.com/acme/widgets",
        )
        self.assertIn("https://github.com/acme/widgets/commit/", section)


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


class UpsertChangelog(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.path = self.tmp / "CHANGELOG.md"

    def tearDown(self):
        for p in self.tmp.rglob("*"):
            if p.is_file():
                p.unlink()
        self.tmp.rmdir()

    def test_creates_with_preamble_when_missing(self):
        gc.upsert_changelog(self.path, "## [v1.0.0] - 2026-05-09\n\n### Added\n- Hello\n")
        out = self.path.read_text(encoding="utf-8")
        self.assertIn("# Changelog", out)
        self.assertIn("Keep a Changelog", out)
        self.assertIn("## [v1.0.0] - 2026-05-09", out)

    def test_inserts_new_section_above_old(self):
        self.path.write_text(
            "# Changelog\n\nAll notable changes...\n\n"
            "## [v1.0.0] - 2026-04-01\n\n### Added\n- Old\n",
            encoding="utf-8",
        )
        gc.upsert_changelog(self.path, "## [v1.1.0] - 2026-05-09\n\n### Added\n- New\n")
        out = self.path.read_text(encoding="utf-8")
        new_idx = out.index("## [v1.1.0]")
        old_idx = out.index("## [v1.0.0]")
        self.assertLess(new_idx, old_idx, "new section must appear above old")
        # Existing preamble preserved
        self.assertIn("All notable changes...", out)


# ---------------------------------------------------------------------------
# End-to-end: build a real tiny repo and run the CLI
# ---------------------------------------------------------------------------


class EndToEnd(unittest.TestCase):
    def _git(self, repo: Path, *args: str) -> str:
        env = os.environ.copy()
        env.update({
            "GIT_AUTHOR_NAME": "Tester",
            "GIT_AUTHOR_EMAIL": "tester@example.com",
            "GIT_COMMITTER_NAME": "Tester",
            "GIT_COMMITTER_EMAIL": "tester@example.com",
        })
        return subprocess.check_output(
            ["git", *args], cwd=repo, text=True, env=env, stderr=subprocess.PIPE,
        )

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self._git(self.repo, "init", "-q", "-b", "main")
        # First release: v1.0.0
        (self.repo / "README.md").write_text("# demo\n")
        self._git(self.repo, "add", ".")
        self._git(self.repo, "commit", "-q", "-m", "initial")
        self._git(self.repo, "tag", "v1.0.0")
        # New work since v1.0.0
        (self.repo / "feature.py").write_text("# feat\n")
        self._git(self.repo, "add", ".")
        self._git(self.repo, "commit", "-q", "-m", "feat: add feature module")
        (self.repo / "feature.py").write_text("# feat v2\n")
        self._git(self.repo, "add", ".")
        self._git(self.repo, "commit", "-q", "-m", "fix: handle empty input")
        (self.repo / "README.md").write_text("# demo (updated)\n")
        self._git(self.repo, "add", ".")
        self._git(self.repo, "commit", "-q", "-m", "docs: tweak readme")  # filtered

    def tearDown(self):
        # On Windows .git directories can hold read-only files; chmod first
        import shutil, stat

        def onerror(func, path, _exc):
            try:
                os.chmod(path, stat.S_IWRITE)
                func(path)
            except OSError:
                pass

        shutil.rmtree(self.repo, onerror=onerror)

    def test_cli_default_emits_section(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            rc = gc.main([
                "--repo", str(self.repo),
                "--version", "v1.1.0",
                "--date", "2026-05-09",
            ])
        self.assertEqual(rc, 0, stderr.getvalue())
        out = stdout.getvalue()
        self.assertIn("## [v1.1.0] - 2026-05-09", out)
        self.assertIn("### Added", out)
        self.assertIn("add feature module", out)
        self.assertIn("### Fixed", out)
        self.assertIn("handle empty input", out)
        # docs commit was filtered
        self.assertNotIn("tweak readme", out)
        self.assertIn("Using last tag as base: v1.0.0", stderr.getvalue())

    def test_cli_in_place_creates_file(self):
        rc = gc.main([
            "--repo", str(self.repo),
            "--version", "v1.1.0",
            "--date", "2026-05-09",
            "--in-place",
            "--quiet",
        ])
        self.assertEqual(rc, 0)
        out = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("# Changelog", out)
        self.assertIn("## [v1.1.0] - 2026-05-09", out)
        self.assertIn("Keep a Changelog", out)

    def test_cli_no_commits_returns_2(self):
        # Same base as HEAD → no commits
        stderr = io.StringIO()
        with patch.object(sys, "stderr", stderr):
            rc = gc.main([
                "--repo", str(self.repo),
                "--since", "HEAD",
                "--version", "v1.1.0",
                "--date", "2026-05-09",
            ])
        self.assertEqual(rc, 2)
        self.assertIn("No commits to write", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
