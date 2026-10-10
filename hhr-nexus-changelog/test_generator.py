from pathlib import Path
import subprocess
import tempfile
import unittest
import generate_changelog as g

class GeneratorTests(unittest.TestCase):
    def test_categories_and_breaking(self):
        self.assertEqual(g.classify('feat(api)!: Add authentication'),('Added','api: Add authentication',True))
        self.assertEqual(g.classify('fix: handle invalid amount')[0],'Fixed')
        self.assertEqual(g.classify('Remove deprecated endpoint')[0],'Removed')
        self.assertEqual(g.classify('docs: update setup')[0],'Changed')

    def test_history_excludes_commits_before_tag(self):
        scratch=Path(__file__).resolve().parents[4]/'work'/'generator-tests'
        scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as d:
            repo=Path(d)
            def run(*args):
                subprocess.run(['git','-C',d,*args],check=True,capture_output=True)
            run('init');run('config','user.name','Nexus Test');run('config','user.email','nexus-test@example.invalid')
            run('commit','--allow-empty','-m','feat: old item');run('tag','v1.0.0')
            run('commit','--allow-empty','-m','fix: repair parsing')
            run('commit','--allow-empty','-m','remove: legacy interface')
            text=g.generate(repo)
            self.assertNotIn('old item',text)
            self.assertIn('repair parsing',text)
            self.assertIn('legacy interface',text)
            self.assertIn('### Added',text)
            self.assertIn('### Fixed',text)

    def test_markdown_is_escaped(self):
        self.assertEqual(g.escape('[link](url)'),r'\[link\](url)')

if __name__=='__main__':
    unittest.main()
