import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from changelog_skill.generator import (
    categorize_commit,
    collect_commits_since_last_tag,
    generate_changelog_markdown,
)


class ChangelogGeneratorTests(unittest.TestCase):
    def test_categorize_commit_maps_common_prefixes(self):
        self.assertEqual(categorize_commit("feat: add billing portal"), "Added")
        self.assertEqual(categorize_commit("fix: handle null state"), "Fixed")
        self.assertEqual(categorize_commit("refactor: simplify parser"), "Changed")
        self.assertEqual(categorize_commit("remove legacy endpoint"), "Removed")

    def test_generate_changelog_markdown_groups_sections(self):
        markdown = generate_changelog_markdown(
            version="Unreleased",
            commits=[
                "feat: add teams page",
                "fix: prevent duplicate invite emails",
                "docs: update onboarding notes",
                "remove deprecated admin widget",
            ],
        )

        self.assertIn("## Unreleased", markdown)
        self.assertIn("### Added", markdown)
        self.assertIn("### Fixed", markdown)
        self.assertIn("### Changed", markdown)
        self.assertIn("### Removed", markdown)

    def test_collect_commits_since_last_tag_reads_git_history(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)

            (repo / "README.md").write_text("hello\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "feat: initial release"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "tag", "v0.1.0"], cwd=repo, check=True, capture_output=True)

            (repo / "README.md").write_text("hello world\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "fix: update greeting"], cwd=repo, check=True, capture_output=True)

            commits = collect_commits_since_last_tag(repo)
            self.assertEqual(commits, ["fix: update greeting"])


if __name__ == "__main__":
    unittest.main()
