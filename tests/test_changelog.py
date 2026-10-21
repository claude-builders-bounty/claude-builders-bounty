import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "generate-changelog"
WRAPPER = ROOT / "changelog.sh"


class ChangelogGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name)
        # Init a real git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Committer"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True, capture_output=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def commit(self, message: str):
        file = self.repo / "work.txt"
        with file.open("a", encoding="utf-8") as f:
            f.write(f"{message}\n")
        subprocess.run(["git", "add", "work.txt"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=self.repo, check=True, capture_output=True)

    def tag(self, tag_name: str):
        subprocess.run(["git", "tag", tag_name], cwd=self.repo, check=True, capture_output=True)

    def test_categorization_and_formatting(self):
        self.commit("feat(auth): add OAuth2 provider support")
        self.commit("fix(api): handle timeout on token refresh")
        self.commit("perf(db): optimize user query indexing")
        self.commit("docs: update setup guide in README")
        self.commit("chore: bump dependencies to latest versions")
        self.commit("revert(legacy): remove deprecated v1 endpoint")
        self.commit("feat(schema)!: switch user id format to uuid v7")

        result = subprocess.run(
            ["python3", str(BIN), "--repo", str(self.repo), "--version", "2.0.0"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout

        self.assertIn("# Changelog", output)
        self.assertIn("## [2.0.0]", output)
        self.assertIn("### Breaking Changes", output)
        self.assertIn("**[schema]** switch user id format to uuid v7", output)
        self.assertIn("### Added", output)
        self.assertIn("**[auth]** add OAuth2 provider support", output)
        self.assertIn("### Fixed", output)
        self.assertIn("**[api]** handle timeout on token refresh", output)
        self.assertIn("### Changed", output)
        self.assertIn("**[db]** optimize user query indexing", output)
        self.assertIn("### Removed", output)
        self.assertIn("**[legacy]** remove deprecated v1 endpoint", output)
        self.assertIn("### Documentation", output)
        self.assertIn("update setup guide in README", output)
        self.assertIn("### Maintenance", output)
        self.assertIn("bump dependencies to latest versions", output)

    def test_since_latest_tag(self):
        self.commit("feat: initial base feature")
        self.tag("v1.0.0")

        self.commit("fix: post-release bug")
        self.commit("feat: fresh enhancement")

        result = subprocess.run(
            ["python3", str(BIN), "--repo", str(self.repo)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout

        self.assertIn("## [Unreleased]", output)
        self.assertIn("post-release bug", output)
        self.assertIn("fresh enhancement", output)
        self.assertNotIn("initial base feature", output)

    def test_all_releases_mode(self):
        self.commit("feat: release 1 feature")
        self.tag("v1.0.0")

        self.commit("fix: release 2 fix")
        self.tag("v1.1.0")

        self.commit("feat: unreleased feature")

        result = subprocess.run(
            ["python3", str(BIN), "--repo", str(self.repo), "--all-releases"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stdout

        self.assertIn("## [Unreleased]", output)
        self.assertIn("## [v1.1.0]", output)
        self.assertIn("## [v1.0.0]", output)
        self.assertIn("unreleased feature", output)
        self.assertIn("release 2 fix", output)
        self.assertIn("release 1 feature", output)

    def test_invalid_tag_preserves_existing_output(self):
        self.commit("feat: initial feature")
        output = self.repo / "CHANGELOG.md"
        original = "# Existing release history\n"
        output.write_text(original, encoding="utf-8")

        result = subprocess.run(
            ["python3", str(BIN), "--repo", str(self.repo),
             "--since-tag", "missing-release", "--output", str(output)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_text(encoding="utf-8"), original)

    def test_wrapper_shell_script(self):
        self.commit("feat: test shell wrapper")
        result = subprocess.run(
            [str(WRAPPER), "--repo", str(self.repo), "--version", "1.0.0"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("## [1.0.0]", result.stdout)
        self.assertIn("test shell wrapper", result.stdout)


if __name__ == "__main__":
    unittest.main()
