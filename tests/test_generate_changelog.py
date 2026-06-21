import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "generate_changelog.py"
spec = importlib.util.spec_from_file_location("generate_changelog", MODULE_PATH)
generate_changelog = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["generate_changelog"] = generate_changelog
spec.loader.exec_module(generate_changelog)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.strip()


class GenerateChangelogTests(unittest.TestCase):
    def test_conventional_commit_categories(self):
        cases = {
            "feat(auth): add login": ("Added", "Add login"),
            "fix: handle empty tag list": ("Fixed", "Handle empty tag list"),
            "refactor(core): simplify parser": ("Changed", "Simplify parser"),
            "remove old migration": ("Removed", "Old migration"),
        }

        for subject, expected in cases.items():
            with self.subTest(subject=subject):
                self.assertEqual(generate_changelog.clean_subject(subject), expected)

    def test_build_changelog_has_required_sections(self):
        commits = [
            generate_changelog.Commit("abc123456", "feat: add billing", "2026-06-01"),
            generate_changelog.Commit("def123456", "fix: repair webhook retry", "2026-06-02"),
            generate_changelog.Commit("123456789", "remove legacy endpoint", "2026-06-03"),
        ]

        output = generate_changelog.build_changelog(commits, "v1.0.0", include_hashes=True)

        self.assertIn("## [Unreleased]", output)
        self.assertIn("### Added\n- Add billing (`abc1234`)", output)
        self.assertIn("### Fixed\n- Repair webhook retry (`def1234`)", output)
        self.assertIn("### Removed\n- Legacy endpoint (`1234567`)", output)

    def test_cli_generates_changelog_since_latest_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")

            (repo / "app.txt").write_text("one\n", encoding="utf-8")
            git(repo, "add", "app.txt")
            git(repo, "commit", "-m", "feat: initial app")
            git(repo, "tag", "v1.0.0")

            (repo / "app.txt").write_text("one\ntwo\n", encoding="utf-8")
            git(repo, "add", "app.txt")
            git(repo, "commit", "-m", "fix: repair startup crash")

            code = generate_changelog.main(["--repo", str(repo), "--output", "CHANGELOG.md"])

            self.assertEqual(code, 0)
            changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
            self.assertIn("_Generated from commits since `v1.0.0`._", changelog)
            self.assertIn("### Fixed\n- Repair startup crash", changelog)
            self.assertNotIn("Initial app", changelog)


if __name__ == "__main__":
    unittest.main()
