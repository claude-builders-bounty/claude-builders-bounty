from __future__ import annotations
import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("changelog", ROOT / "changelog.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="changelog tests ")
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test Writer")
        self.git("config", "user.email", "writer@example.invalid")
    def tearDown(self):
        self.tmp.cleanup()
    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.STDOUT, text=True)
    def commit(self, subject, body=None):
        args=["commit", "-q", "--allow-empty", "-m", subject]
        if body is not None: args += ["-m", body]
        self.git(*args)
        return self.git("rev-parse", "HEAD").strip()
    def cli(self,*args):
        return subprocess.run(["bash",str(ROOT/'changelog.sh'),"--repo",str(self.repo),*args],capture_output=True,text=True)
    def test_empty_repository(self):
        text=m.generate(self.repo)
        self.assertIn("0 non-merge",text)
        self.assertEqual(text.count("_None._"),4)
    def test_no_tags_all_history(self):
        self.commit("feat: first")
        self.commit("fix: second")
        text=m.generate(self.repo)
        self.assertIn("2 non-merge",text)
        self.assertIn("first",text)
        self.assertIn("second",text)
    def test_excludes_tag_commit(self):
        self.commit("feat: old feature"); self.git("tag","v1")
        sha=self.commit("fix: new repair")
        text=m.generate(self.repo)
        self.assertNotIn("old feature",text)
        self.assertIn(sha[:12],text)
        self.assertIn("since tag v1",text)
    def test_tag_at_head_has_no_changes(self):
        self.commit("feat: initial"); self.git("tag","v1")
        self.assertIn("0 non-merge",m.generate(self.repo))
    def test_annotated_tag(self):
        self.commit("feat: initial"); self.git("tag","-a","v1","-m","release")
        self.commit("fix: latest")
        self.assertIn("1 non-merge",m.generate(self.repo))
    def test_unreachable_high_tag_ignored(self):
        self.commit("feat: initial"); self.git("tag","v1")
        self.git("switch","-q","-c","side");self.commit("feat: side");self.git("tag","v999")
        self.git("switch","-q","main");self.commit("fix: main")
        text=m.generate(self.repo)
        self.assertIn("since tag v1",text);self.assertNotIn("v999",text)
    def test_explicit_ancestor(self):
        first=self.commit("add: root");self.commit("fix: next")
        text=m.generate(self.repo,since=first)
        self.assertIn("1 non-merge",text)
    def test_nonancestor_rejected(self):
        self.commit("add: root");self.git("switch","-q","-c","side");side=self.commit("add: side")
        self.git("switch","-q","main")
        with self.assertRaises(m.ChangelogError):m.generate(self.repo,since=side)
    def test_invalid_reference_rejected(self):
        self.commit("add: root")
        with self.assertRaises(m.ChangelogError):m.generate(self.repo,since="--help")
    def test_all_history_overrides_tag(self):
        self.commit("add: root");self.git("tag","v1");self.commit("fix: next")
        self.assertIn("2 non-merge",m.generate(self.repo,all_history=True))
    def test_merge_message_omitted_constituents_included(self):
        self.commit("add: root");self.git("tag","v1");self.git("switch","-q","-c","side")
        self.commit("feat: branch work");self.git("switch","-q","main");self.commit("fix: main work")
        self.git("merge","--no-ff","-m","Merge unhelpful message","side")
        text=m.generate(self.repo)
        self.assertIn("2 non-merge",text);self.assertNotIn("unhelpful",text)
    def test_all_four_categories(self):
        for s in ["feat(api): new endpoint","fix: problem","refactor: internals","remove: old route"]:self.commit(s)
        text=m.generate(self.repo)
        for section in m.SECTIONS:self.assertIn("### "+section,text)
        self.assertLess(text.index("new endpoint"),text.index("### Fixed"))
        self.assertGreater(text.index("old route"),text.index("### Removed"))
    def test_unknown_subject_is_changed(self):
        self.assertEqual(m.categorize("Improve configuration")[0],"Changed")
    def test_imperative_categories(self):
        for s,expect in [("Add export","Added"),("Fixed crash","Fixed"),("Delete old code","Removed")]:
            self.assertEqual(m.categorize(s)[0],expect)
    def test_breaking_subject_and_body(self):
        self.commit("feat(api)!: breaking endpoint");self.commit("refactor: engine","BREAKING CHANGE: migrate settings")
        self.assertEqual(m.generate(self.repo).count("**Breaking:**"),2)
    def test_unicode_and_multiline_body(self):
        self.commit("fix(ui): café ✓","body\nwith\ttabs\nand extra lines")
        self.assertIn("café ✓",m.generate(self.repo))
    def test_subjects_are_literal_not_shell_or_html(self):
        target=self.root/'pwned'
        self.commit(f"feat: $(touch {target}) <script>alert(1)</script> [x](https://bad.invalid)")
        text=m.generate(self.repo)
        self.assertFalse(target.exists());self.assertNotIn("<script>",text);self.assertIn("&lt;script&gt;",text)
        self.assertIn(r"\[x\]",text)
    def test_idempotent_file(self):
        self.commit("feat: init");self.assertEqual(self.cli().returncode,0)
        p=self.repo/'CHANGELOG.md';old=p.read_bytes();r=self.cli()
        self.assertEqual(r.returncode,0);self.assertEqual(old,p.read_bytes());self.assertIn("Unchanged",r.stdout)
    def test_existing_release_and_prefix_preserved(self):
        self.commit("fix: next");p=self.repo/'CHANGELOG.md';p.write_text("# Changelog\n\nManual release policy\n\n## 1.0\n\nHistorical notes\n")
        self.assertEqual(self.cli().returncode,0);self.commit("feat: another");self.assertEqual(self.cli().returncode,0)
        text=p.read_text();self.assertEqual(text.count("Historical notes"),1);self.assertIn("Manual release policy",text);self.assertEqual(text.count(m.START),1)
    def test_malformed_markers_keep_file(self):
        self.commit("fix: next");p=self.repo/'CHANGELOG.md';p.write_text(m.START+"broken");old=p.read_bytes()
        self.assertEqual(self.cli().returncode,2);self.assertEqual(p.read_bytes(),old)
    def test_stdout_makes_no_file(self):
        self.commit("feat: example");r=self.cli("--stdout")
        self.assertEqual(r.returncode,0);self.assertTrue(r.stdout.startswith("# Changelog"));self.assertFalse((self.repo/'CHANGELOG.md').exists())
    def test_output_outside_repo(self):
        self.commit("fix: example");p=self.root/'report.md';r=self.cli("--output",str(p))
        self.assertEqual(r.returncode,0);self.assertTrue(p.is_file());self.assertFalse((self.repo/'CHANGELOG.md').exists())
    def test_symlink_preserved(self):
        self.commit("fix: example");target=self.root/'actual';target.write_text('preserve');(self.repo/'CHANGELOG.md').symlink_to(target)
        self.assertEqual(self.cli().returncode,2);self.assertEqual(target.read_text(),'preserve')
    def test_file_mode_retained(self):
        self.commit("fix: example");p=self.repo/'CHANGELOG.md';p.write_text('# Notes\n');p.chmod(0o640)
        self.assertEqual(self.cli().returncode,0);self.assertEqual(p.stat().st_mode&0o777,0o640)
    def test_shallow_clone_rejected(self):
        self.commit('feat: first');self.commit('fix: second');clone=self.root/'shallow'
        subprocess.run(['git','clone','-q','--depth','1',self.repo.as_uri(),str(clone)],check=True)
        with self.assertRaisesRegex(m.ChangelogError,'Shallow'):m.generate(clone)
    def test_nonrepo_is_an_error(self):
        with self.assertRaises(m.ChangelogError):m.generate(self.root)
    def test_missing_destination_directory(self):
        self.commit('fix: example');r=self.cli('--output',str(self.root/'missing'/'out.md'))
        self.assertEqual(r.returncode,2)
    def test_ambiguous_cli_range_rejected(self):
        self.commit('fix: example');self.assertEqual(self.cli('--since','HEAD','--all-history').returncode,2)
    def test_reversed_markers_rejected(self):
        with self.assertRaises(m.ChangelogError):m.integrate(m.END+'\n'+m.START,'replacement')
    def test_repeated_markers_rejected(self):
        with self.assertRaises(m.ChangelogError):m.integrate(m.START+m.END+m.START+m.END,'replacement')

if __name__=='__main__':unittest.main()
