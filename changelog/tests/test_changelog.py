"""Exercise the CLI against real temporary Git histories."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "changelog.sh"


class ChangelogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog tests ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="test@example.com",
                        GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="test@example.com")
        self.git("init", "-b", "main")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args],
                                       env=self.env, stderr=subprocess.PIPE,
                                       text=True).strip()

    def commit(self, message):
        self.git("commit", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def run_cli(self, *args, ok=True, repo=None):
        result = subprocess.run(["bash", str(SCRIPT), "--repo",
                                 str(repo or self.repo), *args], cwd=self.root,
                                env=self.env, capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("error:", result.stderr)
        return result

    def output(self):
        return (self.repo / "CHANGELOG.md").read_text()

    def test_range_and_categories(self):
        old = self.commit("old release")
        self.git("tag", "v1")
        expected = {
            "Added": [self.commit("feat(api)!: new endpoint"),
                      self.commit("Added a command"),
                      self.commit("Added: another command")],
            "Fixed": [self.commit("FIX(parser): correct parsing"),
                      self.commit("Fixes a typo")],
            "Changed": [self.commit("docs: describe usage"),
                        self.commit("refactor: remove duplication"),
                        self.commit("merge-like ordinary message")],
            "Removed": [self.commit("remove(api): old endpoint"),
                        self.commit("Removed unused option")],
        }
        self.run_cli()
        out = self.output()
        self.assertNotIn(f"({old})", out)
        for category, hashes in expected.items():
            section = out.split(f"### {category}\n", 1)[1].split("\n### ")[0]
            for sha in hashes:
                self.assertEqual(section.count(f"({sha})"), 1)
        self.assertEqual(out.count("\n- "), sum(map(len, expected.values())))

    def test_without_tags_and_escaping(self):
        sha = self.commit('Add <script>alert(1)</script> [link](bad) *bold* `tick`')
        self.run_cli()
        out = self.output()
        self.assertIn(f"({sha})", out)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)
        self.assertIn(r"\[link\]\(bad\)", out)
        self.assertIn(r"\*bold\*", out)

    def test_annotated_tag_at_head(self):
        self.commit("feat: already released")
        self.git("tag", "-a", "v2", "-m", "release")
        self.run_cli()
        out = self.output()
        self.assertEqual(out.count("- None."), 4)
        self.assertNotIn("already released", out)

    def test_unreachable_tag_is_ignored(self):
        self.commit("base")
        self.git("tag", "v1")
        self.git("checkout", "-b", "other")
        unwanted = self.commit("feat: other branch")
        self.git("tag", "v999")
        self.git("checkout", "main")
        wanted = self.commit("fix: main")
        self.run_cli()
        self.assertIn(f"({wanted})", self.output())
        self.assertNotIn(unwanted, self.output())

    def test_merge_commits_once(self):
        self.commit("base")
        self.git("tag", "v1")
        self.git("checkout", "-b", "feature")
        feature = self.commit("feat: branch work")
        self.git("checkout", "main")
        main = self.commit("fix: main work")
        self.git("merge", "--no-ff", "feature", "-m", "Merge feature")
        merge = self.git("rev-parse", "HEAD")
        self.run_cli()
        for sha in (feature, main, merge):
            self.assertEqual(self.output().count(f"({sha})"), 1)

    def test_merges_classified_by_subject(self):
        self.commit("base")
        self.git("tag", "v1")
        expected = {}
        for index, (subject, category) in enumerate([
            ("FEAT(api)!: integrate feature", "Added"),
            ("fix: integrate correction", "Fixed"),
            ("remove old option", "Removed"),
            ("Merge feature", "Changed"),
        ]):
            branch = f"feature-{index}"
            self.git("checkout", "-b", branch)
            self.commit("chore: branch work")
            self.git("checkout", "main")
            self.git("merge", "--no-ff", branch, "-m", subject)
            sha = self.git("rev-parse", "HEAD")
            self.assertEqual(len(self.git("show", "-s", "--format=%P", sha).split()), 2)
            expected[sha] = category
        self.run_cli()
        out = self.output()
        for sha, category in expected.items():
            section = out.split(f"### {category}\n", 1)[1].split("\n### ")[0]
            self.assertIn(f"({sha})", section)
            self.assertEqual(out.count(f"({sha})"), 1)

    def test_determinism_and_read_only_git(self):
        self.commit("base")
        self.git("tag", "v1")
        self.commit("feat: next")
        before = self.git("status", "--porcelain"), self.git("show-ref")
        self.run_cli("--output", "first.md")
        self.run_cli("--output", "second.md")
        self.assertEqual((self.root / "first.md").read_bytes(),
                         (self.root / "second.md").read_bytes())
        self.assertEqual(before, (self.git("status", "--porcelain"),
                                  self.git("show-ref")))

    def test_existing_file_and_symlink_are_preserved(self):
        self.commit("feat: next")
        target = self.root / "existing.md"
        target.write_text("KEEP")
        self.run_cli("--output", str(target), ok=False)
        link = self.repo / "CHANGELOG.md"
        link.symlink_to(target)
        self.run_cli(ok=False)
        self.assertEqual(target.read_text(), "KEEP")
        self.assertTrue(link.is_symlink())

    def test_empty_and_nonrepo_fail_without_output(self):
        self.run_cli(ok=False)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())
        self.run_cli(repo=self.root, ok=False)
        self.assertFalse((self.root / "CHANGELOG.md").exists())

    def test_shallow_clone_rejected(self):
        self.commit("base")
        self.commit("feat: next")
        shallow = self.root / "shallow"
        subprocess.run(["git", "clone", "--depth", "1", self.repo.as_uri(),
                        str(shallow)], env=self.env, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.run_cli(repo=shallow, ok=False)
        self.assertFalse((shallow / "CHANGELOG.md").exists())

    def test_output_error(self):
        self.commit("base")
        self.run_cli("--output", "missing/CHANGELOG.md", ok=False)

    def test_help(self):
        result = subprocess.run(["bash", str(SCRIPT), "--help"],
                                capture_output=True, text=True, cwd=self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--repo", result.stdout)
        self.assertIn("--output", result.stdout)

    def test_unicode_subject(self):
        sha = self.commit("feat: español 日本語 \u2028 separator")
        self.run_cli()
        self.assertIn(f"({sha})", self.output())
        self.assertIn("español 日本語", self.output())


if __name__ == "__main__":
    unittest.main()
