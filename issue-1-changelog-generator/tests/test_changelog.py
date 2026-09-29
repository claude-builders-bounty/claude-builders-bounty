from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "changelog.py"
SPEC = importlib.util.spec_from_file_location("changelog", MODULE_PATH)
assert SPEC and SPEC.loader
changelog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(changelog)


def run(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, stdout=subprocess.DEVNULL)


def commit(repo: Path, subject: str, filename: str) -> None:
    path = repo / filename
    path.write_text(subject + "\n", encoding="utf-8")
    run(repo, "add", filename)
    run(repo, "commit", "-m", subject)


class ChangelogTests(unittest.TestCase):
    def make_repo(self) -> Path:
        root = Path(self.tempdir.name)
        run(root, "init", "-q")
        run(root, "config", "user.name", "Changelog Test")
        run(root, "config", "user.email", "test@example.invalid")
        return root

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_uses_only_commits_after_latest_tag_and_all_sections(self) -> None:
        repo = self.make_repo()
        commit(repo, "feat: before tag", "before.txt")
        run(repo, "tag", "v1.0.0")

        commit(repo, "feat(ui): add dashboard", "feature.txt")
        commit(repo, "fix!: prevent crash", "fix.txt")
        commit(repo, "docs: clarify setup", "docs.txt")
        commit(repo, "remove: legacy endpoint", "remove.txt")

        tag = changelog.latest_tag(repo)
        commits = changelog.commits_since_tag(repo, tag)
        rendered = changelog.render(tag, commits)

        self.assertEqual(tag, "v1.0.0")
        self.assertNotIn("before tag", rendered)
        self.assertIn("## Added", rendered)
        self.assertIn("add dashboard", rendered)
        self.assertIn("## Fixed", rendered)
        self.assertIn("prevent crash", rendered)
        self.assertIn("## Changed", rendered)
        self.assertIn("clarify setup", rendered)
        self.assertIn("## Removed", rendered)
        self.assertIn("legacy endpoint", rendered)

    def test_unknown_subject_falls_back_to_changed(self) -> None:
        section, subject = changelog.classify("Improve contributor guide")
        self.assertEqual(section, "Changed")
        self.assertEqual(subject, "Improve contributor guide")

    def test_word_prefixes_are_supported(self) -> None:
        self.assertEqual(changelog.classify("Added export button")[0], "Added")
        self.assertEqual(changelog.classify("Fixed timeout bug")[0], "Fixed")
        self.assertEqual(changelog.classify("Deleted obsolete config")[0], "Removed")

    def test_no_tag_uses_repository_history(self) -> None:
        repo = self.make_repo()
        commit(repo, "fix: first commit", "one.txt")
        self.assertIsNone(changelog.latest_tag(repo))
        commits = changelog.commits_since_tag(repo, None)
        rendered = changelog.render(None, commits)
        self.assertIn("repository history through `HEAD`", rendered)
        self.assertIn("first commit", rendered)

    def test_max_commits_is_optional_and_bounded(self) -> None:
        repo = self.make_repo()
        for i in range(4):
            commit(repo, f"chore: change {i}", f"{i}.txt")
        all_commits = changelog.commits_since_tag(repo, None)
        limited = changelog.commits_since_tag(repo, None, 2)
        self.assertEqual(len(all_commits), 4)
        self.assertEqual(len(limited), 2)

    def test_empty_tag_range_is_valid(self) -> None:
        repo = self.make_repo()
        commit(repo, "feat: initial", "one.txt")
        run(repo, "tag", "v1")
        tag = changelog.latest_tag(repo)
        commits = changelog.commits_since_tag(repo, tag)
        rendered = changelog.render(tag, commits)
        self.assertEqual(commits, [])
        self.assertIn("No non-merge commits were found", rendered)


if __name__ == "__main__":
    unittest.main()
