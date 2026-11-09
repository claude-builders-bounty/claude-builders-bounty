"""通过临时真实 Git 仓库验证 #1 的命令行交付，不依赖网络或第三方包。"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "changelog.sh"


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog test ")
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.env = dict(os.environ, GIT_AUTHOR_NAME="Test", GIT_COMMITTER_NAME="Test",
                        GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_EMAIL="test@example.invalid")
        self.git("init", "-q")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              text=True, capture_output=True, check=True).stdout.strip()

    def commit(self, message):
        self.git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def run_cli(self, *args, ok=True):
        result = subprocess.run(["bash", str(SCRIPT), *args], cwd=self.repo,
                                env=self.env, text=True, capture_output=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_categories_only_include_commits_since_latest_tag(self):
        old = self.commit("feat: old feature")
        self.git("tag", "v1.0.0")
        for message in ["feat(api): add export", "fix: repair parser",
                        "refactor: simplify reader", "remove: drop old flag",
                        "docs: explain usage"]:
            self.commit(message)
        output = self.run_cli("--stdout").stdout
        for heading in ["Added", "Fixed", "Changed", "Removed"]:
            self.assertIn("### " + heading, output)
        for text in ["add export", "repair parser", "simplify reader", "drop old flag", "explain usage"]:
            self.assertIn(text, output)
        self.assertNotIn(old[:7], output)

    def test_no_tags_includes_entire_history(self):
        sha = self.commit("feat: first feature")
        self.assertIn(sha[:7], self.run_cli("--stdout").stdout)

    def test_empty_repository_returns_clear_error(self):
        self.assertIn("no commits", self.run_cli("--stdout", ok=False).stderr.lower())

    def test_no_new_commits_reports_empty_release(self):
        self.commit("feat: baseline")
        self.git("tag", "v1")
        self.assertIn("No changes", self.run_cli("--stdout").stdout)

    def test_default_output_is_changelog_in_current_directory(self):
        self.commit("feat: write file")
        self.run_cli()
        self.assertIn("write file", (self.repo / "CHANGELOG.md").read_text())

    def test_existing_file_is_preserved_without_force(self):
        self.commit("feat: write file")
        target = self.repo / "CHANGELOG.md"
        target.write_text("KEEP ME")
        self.run_cli(ok=False)
        self.assertEqual(target.read_text(), "KEEP ME")

    def test_force_allows_explicit_overwrite(self):
        self.commit("fix: refreshed output")
        (self.repo / "CHANGELOG.md").write_text("old")
        self.run_cli("--force")
        self.assertIn("refreshed output", (self.repo / "CHANGELOG.md").read_text())

    def test_explicit_since_ref_and_output_with_spaces(self):
        base = self.commit("feat: excluded")
        self.commit("fix: included")
        self.run_cli("--since", base, "--output", "release notes.md")
        content = (self.repo / "release notes.md").read_text()
        self.assertIn("included", content)
        self.assertNotIn("excluded", content)

    def test_invalid_ref_never_overwrites_output(self):
        self.commit("feat: baseline")
        target = self.repo / "CHANGELOG.md"
        target.write_text("KEEP")
        self.assertIn("reference", self.run_cli("--since", "missing-ref", "--force", ok=False).stderr)
        self.assertEqual(target.read_text(), "KEEP")

    def test_breaking_commit_and_unicode_are_preserved(self):
        self.commit("feat(api)!: 支持导出\n\nBREAKING CHANGE: old output removed")
        output = self.run_cli("--stdout").stdout
        self.assertIn("支持导出", output)
        self.assertIn("BREAKING", output)

    def test_commit_subject_is_data_never_shell_code(self):
        self.commit("fix: $(touch OWNED) `touch PWNED` [link](https://example.invalid)")
        output = self.run_cli("--stdout").stdout
        self.assertIn("touch OWNED", output)
        self.assertFalse((self.repo / "OWNED").exists())
        self.assertFalse((self.repo / "PWNED").exists())
        self.assertNotIn("[link](https://example.invalid)", output)

    def test_unreachable_tag_is_ignored(self):
        base = self.commit("chore: base")
        branch = self.git("branch", "--show-current")
        self.git("checkout", "-qb", "other")
        self.commit("feat: unrelated")
        self.git("tag", "v99")
        self.git("checkout", "-q", branch)
        self.commit("fix: relevant")
        output = self.run_cli("--stdout").stdout
        self.assertIn(base[:7], output)
        self.assertNotIn("unrelated", output)

    def test_invalid_repository_fails_without_writing(self):
        # 在父目录也无 Git 仓库的路径检查失败，避免误用 Git 的向上发现逻辑。
        with tempfile.TemporaryDirectory() as outside:
            result = subprocess.run(["bash", str(SCRIPT), "--repo", outside],
                                    text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("repository", result.stderr.lower())

    def test_repository_path_can_contain_spaces(self):
        self.commit("feat: spaced path")
        self.assertIn("spaced path", self.run_cli("--repo", str(self.repo), "--stdout").stdout)


if __name__ == "__main__":
    unittest.main()
