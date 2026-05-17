from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "generate-changelog" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import generate_changelog as gc  # noqa: E402


class GitFixture:
    def __init__(self, repo: Path) -> None:
        self.repo = repo

    def git(self, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()

    def commit_file(self, relative_path: str, content: str, message: str) -> None:
        target = self.repo / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self.git("add", relative_path)
        self.git("commit", "-m", message)


class GenerateChangelogTests(unittest.TestCase):
    def test_initial_commit_fallback_and_categorization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            fixture = GitFixture(repo)
            fixture.git("init")
            fixture.git("config", "user.email", "test@example.com")
            fixture.git("config", "user.name", "Test User")

            fixture.commit_file("README.md", "base\n", "chore: initial import")
            fixture.commit_file("feature.txt", "feature\n", "feat: add generator")
            fixture.commit_file("bug.txt", "bug\n", "fix: close edge case")
            fixture.commit_file("notes.txt", "note\n", "docs: clarify usage")
            fixture.commit_file("cleanup.txt", "cleanup\n", "remove obsolete file")
            fixture.commit_file("misc.txt", "misc\n", "tune ordering")

            base_ref, base_label = gc.resolve_base_ref(repo)
            self.assertTrue(base_label.startswith("initial commit"))
            entries = gc.build_entries(gc.load_commits(repo, base_ref))

            changelog = gc.render_changelog(
                repo=repo,
                entries=entries,
                base_label=base_label,
                base_ref=base_ref,
                head_ref=fixture.git("rev-parse", "HEAD"),
                generated_on=date(2026, 5, 17),
                show_uncategorized_note=any(entry.fallback_used for entry in entries),
            )

            self.assertIn("# CHANGELOG", changelog)
            self.assertIn("Generated on 2026-05-17", changelog)
            self.assertIn("## Added", changelog)
            self.assertIn("- add generator", changelog)
            self.assertIn("## Fixed", changelog)
            self.assertIn("- close edge case", changelog)
            self.assertIn("## Changed", changelog)
            self.assertIn("- clarify usage", changelog)
            self.assertIn("- tune ordering", changelog)
            self.assertIn("## Removed", changelog)
            self.assertIn("- remove obsolete file", changelog)
            self.assertIn("grouped under Changed", changelog)

    def test_last_tag_is_used_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            fixture = GitFixture(repo)
            fixture.git("init")
            fixture.git("config", "user.email", "test@example.com")
            fixture.git("config", "user.name", "Test User")

            fixture.commit_file("base.txt", "base\n", "feat: base")
            fixture.git("tag", "v1.0.0")
            fixture.commit_file("next.txt", "next\n", "feat: after tag")

            base_ref, base_label = gc.resolve_base_ref(repo)
            self.assertEqual(base_label, "v1.0.0")
            commits = gc.load_commits(repo, base_ref)
            self.assertEqual(len(commits), 1)
            self.assertEqual(gc.build_entries(commits)[0].summary, "after tag")


if __name__ == "__main__":
    unittest.main()
