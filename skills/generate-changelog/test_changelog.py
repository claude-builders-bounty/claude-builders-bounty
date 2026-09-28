"""Offline regression tests using actual Bash and isolated Git repositories."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('changelog.sh').resolve()

class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = dict(os.environ, LC_ALL='C.UTF-8', GIT_CONFIG_NOSYSTEM='1',
                        GIT_CONFIG_GLOBAL=os.devnull)
    def tearDown(self):
        self.tmp.cleanup()
    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, env=self.env,
                              text=True, capture_output=True, check=True)
    def repo(self):
        self.git('init', '-q')
        self.git('config', 'user.name', 'Local fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
    def commit(self, message):
        self.git('commit', '-q', '--allow-empty', '-m', message)
    def generate(self, *args, env=None):
        return subprocess.run(['bash', str(SCRIPT), *args], cwd=self.root,
                              env=env or self.env, text=True, capture_output=True, timeout=10)
    def text(self, name='CHANGELOG.md'):
        return (self.root / name).read_text()
    def test_not_a_repository_fails_without_touching_output(self):
        out=self.root/'CHANGELOG.md';out.write_text('keep existing release notes\n')
        result=self.generate()
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(out.read_text(),'keep existing release notes\n')
    def test_empty_repository_fails_without_success_report(self):
        self.repo();result=self.generate()
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.root/'CHANGELOG.md').exists())
        self.assertNotIn('Generated',result.stdout)
    def test_no_tag_includes_entire_history_and_categories(self):
        self.repo()
        for msg in ['feat: add dashboard','fix: repair query','refactor: simplify','remove: old API']:
            self.commit(msg)
        self.assertEqual(self.generate().returncode,0)
        text=self.text()
        for heading,msg in [('Added','feat: add dashboard'),('Fixed','fix: repair query'),
                            ('Changed','refactor: simplify'),('Removed','remove: old API')]:
            self.assertIn('### '+heading+'\n- '+msg,text)
    def test_latest_reachable_tag_excludes_older_history(self):
        self.repo();self.commit('feat: old');self.git('tag','v1.0.0');self.commit('fix: new')
        self.assertEqual(self.generate().returncode,0)
        self.assertNotIn('feat: old',self.text());self.assertIn('fix: new',self.text())
    def test_no_commits_after_tag_does_not_create_blank_bullet(self):
        self.repo();self.commit('feat: released');self.git('tag','v1')
        self.assertEqual(self.generate().returncode,0)
        self.assertEqual(self.text().count('- None'),4)
    def test_custom_output_with_spaces(self):
        self.repo();self.commit('fix: x')
        self.assertEqual(self.generate('release notes.md').returncode,0)
        self.assertIn('fix: x',self.text('release notes.md'))
        self.assertFalse((self.root/'CHANGELOG.md').exists())
    def test_scoped_and_breaking_types(self):
        self.repo()
        for msg in ['feat!: new interface','fix!: correct behaviour','remove(api): old endpoint']:
            self.commit(msg)
        self.assertEqual(self.generate().returncode,0)
        text=self.text()
        self.assertIn('### Added\n- feat!: new interface',text)
        self.assertIn('### Fixed\n- fix!: correct behaviour',text)
        self.assertIn('### Removed\n- remove(api): old endpoint',text)
    def test_commit_subject_is_not_executed(self):
        self.repo();self.commit('feat: $(touch injected) `touch injected2` ; echo x')
        self.assertEqual(self.generate().returncode,0)
        self.assertFalse((self.root/'injected').exists());self.assertFalse((self.root/'injected2').exists())
    def test_git_log_failure_keeps_existing_output(self):
        self.repo();self.commit('feat: x');out=self.root/'CHANGELOG.md';out.write_text('keep\n')
        real_git=shutil.which('git');binpath=self.root/'bin';binpath.mkdir()
        proxy=binpath/'git';proxy.write_text('#!/usr/bin/env bash\nif [ "$1" = log ]; then echo "fixture log failure" >&2; exit 42; fi\nexec '+repr(real_git)+' "$@"\n');proxy.chmod(0o755)
        env=dict(self.env,PATH=str(binpath)+os.pathsep+self.env['PATH'])
        result=self.generate(env=env)
        self.assertNotEqual(result.returncode,0);self.assertEqual(out.read_text(),'keep\n')
    def test_output_directory_error_does_not_report_success(self):
        self.repo();self.commit('feat: x');result=self.generate('missing/out.md')
        self.assertNotEqual(result.returncode,0);self.assertNotIn('Generated',result.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
