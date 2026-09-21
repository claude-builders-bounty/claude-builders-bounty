import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('gen', Path(__file__).resolve().parents[1]/'tools'/'generate_changelog.py')
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
class ChangelogTests(unittest.TestCase):
  def test_categories(self):
    self.assertEqual(gen.cat('feat: new thing'),'Added')
    self.assertEqual(gen.cat('fix: broken thing'),'Fixed')
    self.assertEqual(gen.cat('remove old thing'),'Removed')
  def test_render(self):
    out=gen.render(['feat: add x','fix: y','remove z'])
    self.assertIn('### Added',out); self.assertIn('### Fixed',out); self.assertIn('### Removed',out)
if __name__=='__main__': unittest.main()
