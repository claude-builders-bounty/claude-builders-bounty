"""Integration tests exercise the public Bash entry point with real Git history."""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "changelog.sh"


class ChangelogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog space ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test Author")
        self.git("config", "user.email", "test@example.com")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], text=True,
                              capture_output=True, check=True).stdout.strip()

    def commit(self, subject):
        self.git("commit", "--allow-empty", "-m", subject)

    def run_cli(self, *args, check=True):
        return subprocess.run(["bash", str(SCRIPT), "--repo", str(self.repo), *args],
                              cwd=self.repo, capture_output=True, text=True, check=check)

    def test_categories_and_tag_boundary(self):
        self.commit("feat: old release")
        self.git("tag", "v1.0.0")
        for subject in ["feat(ui): café cards", "fix: empty input", "refactor!: change layout",
                        "remove: legacy page", "Update documentation"]:
            self.commit(subject)
        content = self.run_cli("--stdout").stdout
        self.assertNotIn("old release", content)
        expected = {"Added": "ui: café cards", "Fixed": "empty input",
                    "Changed": "change layout (breaking change)", "Removed": "legacy page"}
        for heading, description in expected.items():
            section = content.split(f"### {heading}\n\n", 1)[1].split("\n### ")[0]
            self.assertIn(description, section)
        self.assertIn("Update documentation", content)

    def test_no_tags_default_file_and_repeatability(self):
        self.commit("Add first page")
        self.run_cli()
        output = self.repo / "CHANGELOG.md"
        first = output.read_bytes()
        self.run_cli()
        self.assertEqual(first, output.read_bytes())
        self.assertIn(b"Add first page", first)
        self.assertIn(b"No reachable tag", first)

    def test_annotated_head_tag_and_empty_repository(self):
        self.assertEqual(self.run_cli("--stdout").stdout.count("_None._"), 4)
        self.commit("fix: released")
        self.git("tag", "-a", "v1.0.0", "-m", "Release")
        content = self.run_cli("--stdout").stdout
        self.assertEqual(content.count("_None._"), 4)
        self.assertIn("Changes since v1.0.0", content)

    def test_unreachable_tag_and_merge_commit(self):
        self.commit("feat: base")
        self.git("tag", "v1.0.0")
        self.git("checkout", "-b", "side")
        self.commit("fix: side correction")
        self.git("checkout", "main")
        self.commit("feat: main page")
        self.git("merge", "--no-ff", "side", "-m", "Merge side branch")
        self.git("checkout", "-b", "future")
        self.commit("feat: unreleased future")
        self.git("tag", "v999.0.0")
        self.git("checkout", "main")
        content = self.run_cli("--stdout").stdout
        self.assertIn("side correction", content)
        self.assertIn("main page", content)
        self.assertNotIn("Merge side branch", content)
        self.assertNotIn("unreleased future", content)
        self.assertIn("Changes since v1.0.0", content)

    def test_markdown_literals_and_output_path(self):
        self.commit("fix(ui): [label] *literal* <example> café")
        output = self.repo / "custom output.md"
        self.run_cli("--output", str(output))
        content = output.read_text()
        self.assertIn(r"\[label\] \*literal\* &lt;example&gt; café", content)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_invalid_repository_does_not_write(self):
        missing = self.repo / "missing"
        result = self.run_cli("--repo", str(missing), check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changelog:", result.stderr)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_empty_commit_message(self):
        self.git("commit", "--allow-empty", "--allow-empty-message", "-m", "")
        self.assertIn("(no commit subject)", self.run_cli("--stdout").stdout)


if __name__ == "__main__":
    unittest.main()
