from __future__ import annotations

import io
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from generate_changelog import (
    Commit,
    classify_commit,
    github_commits,
    latest_local_tag,
    local_commits,
    main,
    parse_args,
    parse_github_repo,
    render_changelog,
)


class GenerateChangelogTests(unittest.TestCase):
    def test_parses_github_repo_values(self):
        self.assertEqual(parse_github_repo("owner/repo"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("https://github.com/owner/repo.git"), ("owner", "repo"))
        self.assertEqual(parse_github_repo("git@github.com:owner/repo.git"), ("owner", "repo"))

    def test_rejects_invalid_github_repo(self):
        with self.assertRaises(SystemExit):
            parse_github_repo("https://example.com/owner/repo")

    def test_classifies_common_commit_styles(self):
        cases = {
            "feat: add billing dashboard": "Added",
            "feat(api)!: add v2 endpoint": "Added",
            "fix(api): prevent null response crash": "Fixed",
            "security: correct token handling": "Fixed",
            "remove deprecated sqlite adapter": "Removed",
            "docs: clarify setup": "Changed",
        }
        for subject, category in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(classify_commit(Commit(sha="abc1234", subject=subject)), category)

    def test_renders_only_populated_sections(self):
        output = render_changelog(
            [
                Commit(sha="abc1234", subject="feat: add export command", author="Ada"),
                Commit(sha="def5678", subject="fix: correct date heading", author="Grace"),
            ],
            since_tag="v1.0.0",
            source="github.com/example/repo",
        )
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertNotIn("### Removed", output)
        self.assertIn("Generated from `github.com/example/repo` since `v1.0.0`.", output)

    def test_renders_empty_range_explicitly(self):
        output = render_changelog([], since_tag="v2.0.0", source="example")
        self.assertIn("No commits found for this range.", output)
        self.assertNotIn("### Added", output)

    def test_max_commits_must_be_positive(self):
        with self.assertRaises(SystemExit):
            parse_args(["--max-commits", "0"])
        with self.assertRaises(SystemExit):
            parse_args(["--max-commits", "-1"])
        self.assertEqual(parse_args(["--max-commits", "25"]).max_commits, 25)

    def test_github_compare_uses_explicit_default_branch(self):
        fake_commits = [
            {
                "sha": "abcdef123456",
                "html_url": "https://github.com/owner/repo/commit/abcdef123456",
                "commit": {
                    "message": "feat: add export\n\nDetails",
                    "author": {"name": "Ada"},
                },
            }
        ]
        with mock.patch("generate_changelog.github_json") as github_json:
            github_json.return_value = {"commits": fake_commits}
            commits = github_commits(
                "owner",
                "repo",
                "v1.0.0",
                100,
                None,
                head_ref="main",
            )

        github_json.assert_called_once_with(
            "/repos/owner/repo/compare/v1.0.0...main",
            None,
        )
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0].subject, "feat: add export")
        self.assertEqual(commits[0].author, "Ada")

    def test_real_git_repo_reads_only_commits_after_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.email", "test@example.com")
            self._git(repo, "config", "user.name", "Test User")

            tracked = repo / "app.txt"
            tracked.write_text("initial\n", encoding="utf-8")
            self._git(repo, "add", "app.txt")
            self._git(repo, "commit", "-q", "-m", "chore: initial")
            self._git(repo, "tag", "v1.0.0")

            changes = [
                ("feature\n", "feat: add dashboard"),
                ("fix\n", "fix: correct crash"),
                ("remove\n", "remove deprecated endpoint"),
                ("docs\n", "docs: clarify setup"),
            ]
            for content, message in changes:
                with tracked.open("a", encoding="utf-8") as handle:
                    handle.write(content)
                self._git(repo, "add", "app.txt")
                self._git(repo, "commit", "-q", "-m", message)

            old_cwd = os.getcwd()
            os.chdir(repo)
            try:
                tag = latest_local_tag()
                commits = local_commits(tag, 100)
            finally:
                os.chdir(old_cwd)

        self.assertEqual(tag, "v1.0.0")
        self.assertEqual(len(commits), 4)
        self.assertNotIn("chore: initial", [commit.subject for commit in commits])
        categories = {classify_commit(commit) for commit in commits}
        self.assertEqual(categories, {"Added", "Fixed", "Removed", "Changed"})

    def test_dry_run_on_real_repo_does_not_create_changelog(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            self._git(repo, "init", "-q")
            self._git(repo, "config", "user.email", "test@example.com")
            self._git(repo, "config", "user.name", "Test User")

            tracked = repo / "app.txt"
            tracked.write_text("initial\n", encoding="utf-8")
            self._git(repo, "add", "app.txt")
            self._git(repo, "commit", "-q", "-m", "chore: initial")
            self._git(repo, "tag", "v1.0.0")
            tracked.write_text("initial\nfeature\n", encoding="utf-8")
            self._git(repo, "add", "app.txt")
            self._git(repo, "commit", "-q", "-m", "feat: add dashboard")

            old_cwd = os.getcwd()
            os.chdir(repo)
            stdout = io.StringIO()
            try:
                with redirect_stdout(stdout):
                    self.assertEqual(main(["--dry-run"]), 0)
            finally:
                os.chdir(old_cwd)

            self.assertFalse((repo / "CHANGELOG.md").exists())
            self.assertIn("### Added", stdout.getvalue())
            self.assertIn("since `v1.0.0`", stdout.getvalue())

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
