import importlib.util, unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('review', Path(__file__).resolve().parents[1]/'claude_review.py')
review=importlib.util.module_from_spec(spec); spec.loader.exec_module(review)
class ReviewTests(unittest.TestCase):
  def test_markdown_shape(self):
    out=review.analyze('diff --git a/app/api/x b/app/api/x')
    for x in ['### Summary','### Identified risks','### Improvement suggestions','### Confidence:']:
      self.assertIn(x,out)
if __name__=='__main__': unittest.main()
