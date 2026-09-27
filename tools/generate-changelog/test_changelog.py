from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from changelog import _classify, generate_changelog, main


def git(repo: Path, *args: str) -> None:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Changelog Test",
        "GIT_AUTHOR_EMAIL": "changelog-test@example.invalid",
        "GIT_COMMITTER_NAME": "Changelog Test",
        "GIT_COMMITTER_EMAIL": "changelog-test@example.invalid",
    }
    subprocess.run(
        ["git", *args],
        cwd=repo,
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def git_output(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def commit(repo: Path, name: str, subject: str) -> None:
    (repo / name).write_text(subject + "\n", encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", subject)


class ClassificationTests(unittest.TestCase):
    def test_conventional_and_plain_subjects_map_to_expected_sections(self) -> None:
        self.assertEqual(
            _classify("feat(api): add a webhook"), ("Added", "add a webhook")
        )
        self.assertEqual(
            _classify("fix: reject empty IDs"), ("Fixed", "reject empty IDs")
        )
        self.assertEqual(
            _classify("refactor: split parser"), ("Changed", "split parser")
        )
        self.assertEqual(
            _classify("remove legacy endpoint"),
            ("Removed", "remove legacy endpoint"),
        )
        self.assertEqual(
            _classify("feat!: replace the public API"),
            ("Changed", "replace the public API"),
        )
        self.assertEqual(
            _classify("miscellaneous work"), ("Changed", "miscellaneous work")
        )


class GitHistoryTests(unittest.TestCase):
    def create_repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        git(repo, "config", "user.name", "Changelog Test")
        git(repo, "config", "user.email", "changelog-test@example.invalid")
        return repo

    def test_only_non_merge_commits_after_latest_reachable_tag_are_listed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.create_repo(Path(temporary))
            commit(repo, "before.txt", "feat: before release")
            git(repo, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
            commit(repo, "fix.txt", "fix(api): handle empty input")
            commit(repo, "remove.txt", "remove legacy endpoint")
            main_branch = git_output(repo, "branch", "--show-current")
            git(repo, "switch", "-c", "feature")
            commit(repo, "feature.txt", "feat: add feature branch support")
            git(repo, "switch", main_branch)
            git(repo, "merge", "--no-ff", "--no-edit", "feature")

            output = generate_changelog(repo)
            self.assertIn("### Fixed", output)
            self.assertIn("handle empty input", output)
            self.assertIn("### Added", output)
            self.assertIn("feature branch support", output)
            self.assertIn("### Removed", output)
            self.assertNotIn("Merge branch", output)
            self.assertNotIn("before release", output)

    def test_no_tag_uses_available_history_and_unknown_subjects_are_changed(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.create_repo(Path(temporary))
            commit(repo, "one.txt", "feat: first feature")
            commit(repo, "two.txt", "cleanup scripts")

            output = generate_changelog(repo)
            self.assertIn("### Added", output)
            self.assertIn("first feature", output)
            self.assertIn("### Changed", output)
            self.assertIn("cleanup scripts", output)

    def test_empty_range_has_a_useful_unreleased_section(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = self.create_repo(Path(temporary))
            commit(repo, "one.txt", "feat: first feature")
            git(repo, "tag", "v1.0.0")

            output = generate_changelog(repo)
            self.assertIn("## [Unreleased]", output)
            self.assertIn("No non-merge commits found", output)


class OutputTests(unittest.TestCase):
    def test_existing_changelog_is_preserved_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            git(repo, "init", "-q")
            changelog = repo / "CHANGELOG.md"
            original = "# Existing changelog\n"
            changelog.write_text(original, encoding="utf-8")

            with redirect_stderr(StringIO()):
                result = main(["--repo", str(repo)])
            self.assertEqual(result, 2)
            self.assertEqual(changelog.read_text(encoding="utf-8"), original)

    def test_force_replaces_existing_output_and_stdout_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Changelog Test")
            git(repo, "config", "user.email", "changelog-test@example.invalid")
            commit(repo, "file.txt", "feat: a generated entry")
            changelog = repo / "CHANGELOG.md"
            changelog.write_text("old\n", encoding="utf-8")

            self.assertEqual(main(["--repo", str(repo), "--force"]), 0)
            self.assertIn("a generated entry", changelog.read_text(encoding="utf-8"))
            changelog.unlink()
            self.assertEqual(main(["--repo", str(repo), "--stdout"]), 0)
            self.assertFalse(changelog.exists())

    def test_shell_wrapper_works_from_outside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary) / "repo"
            repo.mkdir()
            git(repo, "init", "-q")
            git(repo, "config", "user.name", "Changelog Test")
            git(repo, "config", "user.email", "changelog-test@example.invalid")
            commit(repo, "file.txt", "feat: wrapper output")
            wrapper = Path(__file__).with_name("changelog.sh")

            result = subprocess.run(
                ["bash", str(wrapper), "--repo", str(repo), "--stdout"],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("wrapper output", result.stdout)
            self.assertFalse((repo / "CHANGELOG.md").exists())


if __name__ == "__main__":
    unittest.main()
