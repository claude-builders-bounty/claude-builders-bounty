"""Tests for generate_changelog (stdlib unittest, no deps)."""
import importlib.util
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("gc", HERE.parent / "generate_changelog.py")
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)


class TestCategorize(unittest.TestCase):
    def test_conventional(self):
        self.assertEqual(gc.categorize("feat: add voice endpoint"), "Added")
        self.assertEqual(gc.categorize("fix(api): handle timeout"), "Fixed")
        self.assertEqual(gc.categorize("chore: bump deps"), "Changed")
        self.assertEqual(gc.categorize("remove legacy auth"), "Removed")

    def test_keywords(self):
        self.assertEqual(gc.categorize("Add support for RTL"), "Added")
        self.assertEqual(gc.categorize("resolve crash on empty input"), "Fixed")
        self.assertEqual(gc.categorize("Deleted stale fixtures"), "Removed")

    def test_default(self):
        self.assertEqual(gc.categorize("update docs"), "Changed")


class TestBuild(unittest.TestCase):
    def test_buckets_and_format(self):
        commits = [("abc123", "feat: add changelog"), ("def456", "fix: escape html"),
                   ("a1b2c3", "remove dead code"), ("d4e5f6", "tweak wording")]
        out = gc.build_changelog(commits, "1.0.0", "2026-01-01")
        self.assertIn("# Changelog", out)
        for s in ("Added", "Fixed", "Changed", "Removed"):
            self.assertIn(f"### {s}", out)
        self.assertIn("add changelog (abc123)", out)

    def test_empty(self):
        out = gc.build_changelog([], "0.1.0", "2026-01-01", previous="")
        self.assertIn("_No commits found", out)


class TestEndToEnd(unittest.TestCase):
    def test_generates_from_real_repo(self):
        with tempfile.TemporaryDirectory() as d:
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
            def run(*a):
                subprocess.run(["git", *a], cwd=d, env=env, check=True,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            run("init", "-q")
            Path(d, "a.txt").write_text("1")
            run("add", "-A"); run("commit", "-q", "-m", "feat: first feature")
            Path(d, "b.txt").write_text("2")
            run("add", "-A"); run("commit", "-q", "-m", "fix: squashed bug")
            old = os.getcwd(); os.chdir(d)
            try:
                text = gc.build_changelog(gc.collect_commits(gc.last_tag()), "unreleased", "2026-01-01")
            finally:
                os.chdir(old)
            self.assertIn("### Added", text)
            self.assertIn("### Fixed", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
