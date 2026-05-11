from __future__ import annotations

import datetime as dt
import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "generate-changelog" / "generate_changelog.py"
spec = importlib.util.spec_from_file_location("generate_changelog", SCRIPT)
generate_changelog = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["generate_changelog"] = generate_changelog
spec.loader.exec_module(generate_changelog)


def git(repo: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class GenerateChangelogTests(unittest.TestCase):
    def test_groups_commits_since_latest_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")
            (repo / "file.txt").write_text("base\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "chore: initial")
            git(repo, "tag", "v0.1.0")

            (repo / "feature.txt").write_text("feature\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "feat: add report export")
            (repo / "bug.txt").write_text("bug\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "fix: repair empty state")

            tag = generate_changelog.last_tag(repo)
            commits = generate_changelog.commits_since_last_tag(repo, tag)
            output = generate_changelog.render_changelog(repo, commits, tag, today=dt.date(2026, 5, 12))

        self.assertEqual(tag, "v0.1.0")
        self.assertIn("_Source: commits since `v0.1.0`._", output)
        self.assertIn("### Added\n- feat: add report export", output)
        self.assertIn("### Fixed\n- fix: repair empty state", output)
        self.assertNotIn("chore: initial", output)

    def test_category_rules_cover_removed_and_changed(self) -> None:
        removed = generate_changelog.Commit("abc1234", "remove legacy option", "")
        changed = generate_changelog.Commit("def5678", "docs: clarify setup", "")

        self.assertEqual(generate_changelog.category_for(removed), "Removed")
        self.assertEqual(generate_changelog.category_for(changed), "Changed")


if __name__ == "__main__":
    unittest.main()
