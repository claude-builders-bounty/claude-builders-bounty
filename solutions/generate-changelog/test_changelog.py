"""Integration tests use real isolated Git repositories, never the user's Git config."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("changelog.py")
spec = importlib.util.spec_from_file_location("changelog", SCRIPT)
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="changelog test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                        GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                        GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        self.command("init", "--quiet")
        self.command("config", "commit.gpgsign", "false")
        self.command("config", "core.hooksPath", str(self.root / "no-hooks"))
        self.commit("initial fixture")
        self.command("tag", "v1.0.0")

    def command(self, *args, repo=None):
        return subprocess.run(["git", "-C", str(repo or self.repo), *args], env=self.env,
                              check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()

    def commit(self, subject):
        self.command("commit", "--quiet", "--allow-empty", "-m", subject)
        return self.command("rev-parse", "HEAD")

    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(SCRIPT), "--repo", str(self.repo), *args],
                              cwd=cwd, env=self.env, capture_output=True, encoding="utf-8")

    def test_all_categories_exclude_tag_commit(self):
        self.commit("feat(api): add endpoint")
        self.commit("fix: handle empty input")
        self.commit("refactor!: change defaults")
        self.commit("chore: remove legacy path")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("initial fixture", out.stdout)
        for heading, subject in [("Added", "feat(api): add endpoint"),
                                 ("Fixed", "fix: handle empty input"),
                                 ("Changed", "refactor!: change defaults"),
                                 ("Removed", "chore: remove legacy path")]:
            section = out.stdout.split("### " + heading + "\n", 1)[1].split("### ", 1)[0]
            self.assertIn(subject, section)

    def test_unreachable_higher_tag_is_ignored(self):
        self.command("checkout", "--quiet", "-b", "side")
        self.commit("feat: unrelated release")
        self.command("tag", "v999.0.0")
        self.command("checkout", "--quiet", "-")
        self.commit("fix: main line")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("**v1.0.0**", out.stdout)
        self.assertNotIn("unrelated release", out.stdout)

    def test_annotated_tag_is_supported(self):
        self.commit("feat: released")
        self.command("tag", "-a", "v2.0.0", "-m", "release")
        self.commit("fix: after release")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("**v2.0.0**", out.stdout)
        self.assertNotIn("feat: released", out.stdout)

    def test_no_tags_uses_all_history(self):
        self.command("tag", "-d", "v1.0.0")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("no reachable tag", out.stdout)
        self.assertIn("initial fixture", out.stdout)

    def test_tag_at_head_yields_four_empty_sections(self):
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.count("_None._"), 4)

    def test_repeat_generation_is_identical_and_check_does_not_write(self):
        self.commit("add widget")
        out = self.run_cli()
        self.assertEqual(out.returncode, 0, out.stderr)
        path = self.repo / "CHANGELOG.md"
        before, modified = path.read_bytes(), path.stat().st_mtime_ns
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_mtime_ns, modified)
        self.assertEqual(self.run_cli("--check").returncode, 0)
        self.commit("fix widget")
        self.assertEqual(self.run_cli("--check").returncode, 1)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertIn("fix widget", path.read_text())

    def test_existing_manual_file_is_never_overwritten(self):
        path = self.repo / "CHANGELOG.md"
        content = b"# My release notes\r\n\r\nDo not lose this.\r\n"
        path.write_bytes(content)
        out = self.run_cli()
        self.assertEqual(out.returncode, 2)
        self.assertIn("existing content is preserved", out.stderr)
        self.assertEqual(path.read_bytes(), content)

    def test_manual_prefix_suffix_and_crlf_are_preserved(self):
        self.assertEqual(self.run_cli().returncode, 0)
        path = self.repo / "CHANGELOG.md"
        prefix = "# Human introduction\r\n\r\n"
        suffix = "\r\n\r\n## v1\r\nHand-written release.\r\n"
        block = changelog.generate(self.repo).rstrip("\n").replace("\n", "\r\n")
        path.write_bytes((prefix + block + suffix).encode())
        self.commit("feat: more work")
        out = self.run_cli()
        self.assertEqual(out.returncode, 0, out.stderr)
        saved = path.read_bytes().decode()
        self.assertTrue(saved.startswith(prefix))
        self.assertTrue(saved.endswith(suffix))
        self.assertNotIn("\n", saved.replace("\r\n", ""))

    def test_subject_is_text_not_shell_or_html(self):
        self.commit('fix: $(touch INJECTED) `calc` <script>x</script> [click](bad) 中文')
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertFalse((self.repo / "INJECTED").exists())
        self.assertIn("&lt;script&gt;", out.stdout)
        self.assertIn(r"\`calc\`", out.stdout)
        self.assertIn(r"\[click\]", out.stdout)
        self.assertIn("中文", out.stdout)

    def test_merge_includes_branch_commits_once(self):
        self.command("checkout", "--quiet", "-b", "feature")
        branch_commit = self.commit("feat: merged change")
        self.command("checkout", "--quiet", "-")
        self.commit("fix: main change")
        self.command("merge", "--no-ff", "feature", "-m", "Merge feature")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.count(branch_commit[:10]), 1)
        self.assertEqual(out.stdout.count("Merge feature"), 1)

    def test_explicit_since_resolves_ancestor(self):
        since = self.commit("feat: custom base")
        self.commit("fix: selected range")
        out = self.run_cli("--since", since, "--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("custom base", out.stdout)
        self.assertIn("selected range", out.stdout)

    def test_invalid_and_unrelated_revisions_fail_without_output(self):
        self.assertEqual(self.run_cli("--since", "missing-ref").returncode, 2)
        self.assertEqual(self.run_cli("--since=--all").returncode, 2)
        self.command("checkout", "--quiet", "-b", "other")
        other = self.commit("feat: unrelated")
        self.command("checkout", "--quiet", "-")
        self.assertEqual(self.run_cli("--since", other).returncode, 2)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_shallow_repository_refuses_incomplete_history(self):
        clone = self.root / "shallow"
        self.command("clone", "--depth=1", self.repo.as_uri(), str(clone))
        out = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(clone)],
                             env=self.env, capture_output=True, encoding="utf-8")
        self.assertEqual(out.returncode, 2)
        self.assertIn("Shallow history", out.stderr)
        self.assertFalse((clone / "CHANGELOG.md").exists())

    def test_check_missing_output_does_not_create_it(self):
        self.assertEqual(self.run_cli("--check").returncode, 1)
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_output_path_with_spaces_outside_repo(self):
        path = self.root / "draft release.md"
        out = self.run_cli("--output", str(path))
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertTrue(path.exists())
        self.assertFalse((self.repo / "CHANGELOG.md").exists())

    def test_credentials_never_appear_in_commit_links(self):
        self.command("remote", "add", "origin", "https://username:fake-secret@github.com/example/project.git")
        commit = self.commit("feat: linked")
        out = self.run_cli("--stdout")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertNotIn("fake-secret", out.stdout)
        self.assertIn("https://github.com/example/project/commit/" + commit, out.stdout)


class FormatTests(unittest.TestCase):
    def test_plain_and_conventional_subjects(self):
        examples = {"Added": ["Add UI", "feat(cli)!: command"],
                    "Fixed": ["FIX parser", "hotfix: retry"],
                    "Changed": ["docs: remove mention", "revert: feat: previous", "Update dependency"],
                    "Removed": ["Drop old code", "refactor: delete obsolete code", "remove!: endpoint"]}
        for expected, subjects in examples.items():
            for subject in subjects:
                with self.subTest(subject=subject):
                    self.assertEqual(changelog.category(subject), expected)

    def test_duplicate_or_malformed_markers_are_rejected(self):
        start, end = changelog.START, changelog.END
        for content in [start + "\n" + start + "\n" + end,
                        end + "\n" + start, "prefix" + start + "\n" + end,
                        start + "trailing\n" + end, start + "\n" + end + "trailing"]:
            with self.subTest(content=content), self.assertRaises(changelog.ChangelogError):
                changelog.merge_document(content, start + "\nnew\n" + end + "\n")

    def test_github_origin_variants(self):
        self.assertEqual(changelog.github_url("git@github.com:owner/repo.git"), "https://github.com/owner/repo")
        self.assertEqual(changelog.github_url("ssh://git@github.com/owner/repo.git"), "https://github.com/owner/repo")
        self.assertIsNone(changelog.github_url("https://github.com.evil.invalid/owner/repo"))
        self.assertIsNone(changelog.github_url("https://example.invalid/owner/repo"))


if __name__ == "__main__":
    unittest.main()
