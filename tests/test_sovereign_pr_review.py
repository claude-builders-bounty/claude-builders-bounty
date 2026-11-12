import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"agents"/"sovereign-pr-review"))
import claude_review as r
class ParseTests(unittest.TestCase):
 def test_valid(self): self.assertEqual(r.parse_pr_url("https://github.com/acme/app/pull/42"),("acme","app",42))
 def test_non_github(self):
  with self.assertRaises(ValueError): r.parse_pr_url("https://example.com/acme/app/pull/42")
 def test_issue_url(self):
  with self.assertRaises(ValueError): r.parse_pr_url("https://github.com/acme/app/issues/42")
class DiffTests(unittest.TestCase):
 def test_added_secret_line(self):
  files=[{"filename":"app/config.py","patch":"@@ -1,0 +2 @@\n+API_KEY = 'sk_live_123456789abcdef'"}]
  self.assertTrue(any(x["title"]=="Possible credential" and x["line"]==2 for x in r.analyze(files)[0]))
 def test_removed_secret_ignored(self):
  files=[{"filename":"app/config.py","patch":"@@ -2 +1,0 @@\n-API_KEY = 'sk_live_123456789abcdef'"}]
  self.assertEqual(r.analyze(files)[0],[])
 def test_private_key(self):
  files=[{"filename":"key.pem","patch":"@@ -0,0 +1 @@\n+-----BEGIN PRIVATE KEY-----"}]
  self.assertTrue(any(x["title"]=="Private key material" for x in r.analyze(files)[0]))
 def test_disabled_test(self):
  files=[{"filename":"tests/test_api.py","patch":"@@ -1,0 +2 @@\n+pytest.skip('temporary')"}]
  self.assertTrue(any(x["title"]=="Disabled test" for x in r.analyze(files)[0]))
 def test_missing_tests(self):
  files=[{"filename":"src/api.py","patch":"@@ -0,0 +1 @@\n+def handle(): return True"}]
  self.assertTrue(any("no test/spec path" in x for x in r.analyze(files)[1]))
 def test_high_confidence_requires_tests(self):
  files=[{"filename":"src/api.py","patch":"@@ -0,0 +1 @@\n+def handle(): return True"},{"filename":"tests/test_api.py","patch":"@@ -0,0 +1 @@\n+def test_handle(): assert True"}]
  findings,_,score=r.analyze(files); self.assertEqual(findings,[]); self.assertEqual(score,"High")
 def test_report_sections(self):
  pr={"title":"Example","html_url":"https://github.com/a/b/pull/1","additions":1,"deletions":0,"changed_files":1}
  report=r.render(pr,[],[],["Add tests."],"Medium")
  for section in r.SECTIONS: self.assertIn("## "+section,report)
if __name__=="__main__": unittest.main()
