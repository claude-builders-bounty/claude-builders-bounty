#!/usr/bin/env python3
"""Unit tests cho claude-review (stdlib only): parse, severity, depth, JSON, truncate."""
import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
from importlib.machinery import SourceFileLoader
m = SourceFileLoader("claude_review", str(HERE / "claude-review")).load_module()


def meta(files=3, add=10, dele=2):
    return {"title": "t", "additions": add, "deletions": dele,
            "files": [{"path": f"a{i}.py"} for i in range(files)]}


class T(unittest.TestCase):
    def test_url_ok(self):
        self.assertEqual(m.parse_pr_url("https://github.com/o/r/pull/123"), ("o", "r", "123"))

    def test_url_bad(self):
        for u in ("https://github.com/o/r/issues/1", "notaurl", ""):
            with self.assertRaises(SystemExit):
                m.parse_pr_url(u)

    def test_secret_critical(self):
        r = m.build_review("u", meta(), "+ x = 'ghp_1234567890abcdef'", "standard")
        self.assertTrue(any(i["severity"] == "Critical" for i in r["risks"]))
        self.assertTrue(len(r["security"]) > 0)
        self.assertEqual(r["confidence"], "High")

    def test_quick_skips_medium(self):
        r = m.build_review("u", meta(), "+ innerHTML = x", "quick")
        self.assertEqual(r["risks"], [])
        r2 = m.build_review("u", meta(), "+ innerHTML = x", "deep")
        self.assertTrue(len(r2["risks"]) > 0)

    def test_eval_high(self):
        r = m.build_review("u", meta(), "+ eval(user_input)", "standard")
        self.assertIn("High", [i["severity"] for i in r["risks"]])

    def test_clean_low_conf(self):
        r = m.build_review("u", {"title": "t", "additions": 5, "deletions": 1,
                                 "files": [{"path": "x_test.py"}]}, "+ a = 1", "standard")
        self.assertEqual(r["confidence"], "Low")

    def test_truncated(self):
        md = dict(meta(files=5), _truncated=True)
        r = m.build_review("u", md, "+ a = 1", "standard")
        self.assertTrue(any("coverage-gap" in i["message"] for i in r["risks"]))

    def test_json_keys(self):
        import json
        r = m.build_review("u", meta(), "+ a = 1", "standard")
        d = json.loads(json.dumps(r))
        for k in ("title", "pr", "depth", "summary", "risks", "security",
                  "suggestions", "confidence"):
            self.assertIn(k, d)

    def test_markdown_sections(self):
        r = m.build_review("u", meta(), "+ a = 1", "standard")
        md = m.to_markdown(r)
        for s in ("### Summary", "### Risks", "### Security",
                  "### Suggestions", "### Confidence"):
            self.assertIn(s, md)


if __name__ == "__main__":
    unittest.main(verbosity=1)
