#!/usr/bin/env python3
"""Unit tests for claude-review (no network)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import claude_review as cr  # noqa: E402


SAMPLE_DIFF = """diff --git a/app.py b/app.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/app.py
@@ -0,0 +1,5 @@
+def hello():
+    return "hi"
+
+def bad():
+    eval("1+1")
diff --git a/tests/test_app.py b/tests/test_app.py
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/tests/test_app.py
@@ -0,0 +1,3 @@
+from app import hello
+
+def test_hello():
+    assert hello() == "hi"
"""


class TestParsePrRef(unittest.TestCase):
    def test_url(self):
        self.assertEqual(
            cr.parse_pr_ref("https://github.com/acme/demo/pull/42"),
            ("acme", "demo", 42),
        )

    def test_short(self):
        self.assertEqual(cr.parse_pr_ref("acme/demo#7"), ("acme", "demo", 7))

    def test_bad(self):
        self.assertIsNone(cr.parse_pr_ref("not-a-pr"))


class TestAnalyze(unittest.TestCase):
    def test_eval_risk_and_tests(self):
        files = cr.parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual(len(files), 2)
        findings, summary, risks, suggestions, conf = cr.analyze("feat: hello", "", files)
        self.assertTrue(summary)
        self.assertTrue(any("eval" in r.lower() for r in risks))
        self.assertIn(conf, ("Low", "Medium", "High"))
        self.assertTrue(any(f.kind == "tests" and f.severity == "info" for f in findings))

    def test_empty_diff(self):
        findings, summary, risks, suggestions, conf = cr.analyze("x", "", [])
        self.assertEqual(conf, "Low")
        self.assertTrue(any(f.kind == "empty" for f in findings))

    def test_cli_diff_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sample.diff"
            p.write_text(SAMPLE_DIFF, encoding="utf-8")
            out = Path(td) / "out.md"
            rc = cr.main(["--diff", str(p), "--title", "feat: hello", "-o", str(out), "--no-llm"])
            self.assertEqual(rc, 0)
            text = out.read_text(encoding="utf-8")
            self.assertIn("## Summary", text)
            self.assertIn("## Risks", text)
            self.assertIn("## Suggestions", text)
            self.assertIn("## Confidence", text)


if __name__ == "__main__":
    unittest.main()
