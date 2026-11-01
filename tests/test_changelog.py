import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from changelog import classify

class ChangelogTests(unittest.TestCase):
    def test_classification(self):
        for subject, expected in [('feat(ui): Add dark mode', 'Added'), ('fix: repair crash', 'Fixed'), ('refactor: simplify parser', 'Changed'), ('remove: old endpoint', 'Removed'), ('Delete deprecated API', 'Removed'), ('New setting', 'Added')]:
            with self.subTest(subject=subject):
                self.assertEqual(classify(subject)[0], expected)

    def test_tag_range_and_protect_file(self):
        with tempfile.TemporaryDirectory() as d:
            def run(*args):
                return subprocess.run(args, cwd=d, capture_output=True, text=True, check=True)
            run('git', 'init', '-q')
            run('git', 'config', 'user.email', 'test@example.com')
            run('git', 'config', 'user.name', 'Test')
            f = pathlib.Path(d) / 'file.txt'
            f.write_text('a')
            run('git', 'add', '.')
            run('git', 'commit', '-qm', 'feat: initial setup')
            run('git', 'tag', 'v1.0.0')
            f.write_text('b')
            run('git', 'commit', '-qam', 'fix: repaired API')
            run(sys.executable, str(ROOT / 'changelog.py'))
            changelog = (pathlib.Path(d) / 'CHANGELOG.md').read_text()
            self.assertIn('### Fixed', changelog)
            self.assertIn('repaired API', changelog)
            self.assertNotIn('initial setup', changelog)
            self.assertNotEqual(subprocess.run([sys.executable, str(ROOT / 'changelog.py')], cwd=d, capture_output=True).returncode, 0)

if __name__ == '__main__': unittest.main()
