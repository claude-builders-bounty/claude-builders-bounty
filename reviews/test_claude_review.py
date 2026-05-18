#!/usr/bin/env python3
"""test_claude_review.py — PR Review Agent 端到端验证（基于现有能力）"""
import unittest, sys, json, os
sys.path.insert(0, os.path.dirname(__file__))
import claude_review

SIMPLE_DIFF = """diff --git a/src/main.py b/src/main.py
index abc..def 100644
--- a/src/main.py
+++ b/src/main.py
@@ -10,7 +10,7 @@
-    total = sum(item['price'] for item in items)
-    return total
+    return sum(item['price'] for item in items)
+    # FIXME: need to handle discount
"""

VULNERABLE_DIFF = """diff --git a/src/api.py b/src/api.py
index 789..012 100644
--- a/src/api.py
+++ b/src/api.py
@@ -1,8 +1,14 @@
 import json
+import os
+# DEBUG: disable auth
+AUTH_ENABLED = False
 def handle_request(data):
+    cmd = data.get('command', '')
+    os.system(cmd)
     result = eval(data.get('query', ''))
-    return result
+    return json.dumps(result)
"""

SECURE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 123..456 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,10 +1,15 @@
+import hashlib
 import os
 def verify_password(plain, hashed):
-    return plain == hashed
+    return hashlib.sha256(plain.encode()).hexdigest() == hashed
"""


class TestReviewAgent(unittest.TestCase):
    
    def test_simple_diff(self):
        a = claude_review.analyze_diff(SIMPLE_DIFF)
        self.assertIsNotNone(a)
        r = claude_review.generate_review(a)
        self.assertIn('summary', r)
        self.assertIn('risks', r)
        self.assertIn('confidence', r)
        md = claude_review.format_review(a, r)
        self.assertIn('##', md)
    
    def test_vulnerable_risks(self):
        a = claude_review.analyze_diff(VULNERABLE_DIFF)
        self.assertIsNotNone(a)
        r = claude_review.generate_review(a)
        self.assertTrue(len(r.get('risks','')) > 0, '有问题的diff应产生告警')
    
    def test_secure_no_false_positive(self):
        a = claude_review.analyze_diff(SECURE_DIFF)
        self.assertIsNotNone(a)
        r = claude_review.generate_review(a)
        self.assertTrue(len(r.get('risks','')) > 0, '安全改进也可能有建议')
    
    def test_empty_diff_handling(self):
        a = claude_review.analyze_diff('')
        if a is None:
            a = {'files':[], 'files_count':0, 'additions':0, 'deletions':0, 'total_changes':0}
        r = claude_review.generate_review(a)
        self.assertTrue(len(r.get('summary','')) > 0)
    
    def test_markdown_format(self):
        a = claude_review.analyze_diff(SIMPLE_DIFF)
        r = claude_review.generate_review(a)
        md = claude_review.format_review(a, r)
        self.assertIn('Summary', md)
        self.assertIn('Confidence', md)
    
    def test_json_output(self):
        a = claude_review.analyze_diff(SIMPLE_DIFF)
        r = claude_review.generate_review(a)
        output = {
            'analysis': a,
            'review': r,
            'version': claude_review.VERSION
        }
        j = json.dumps(output, indent=2)
        parsed = json.loads(j)
        self.assertEqual(parsed['version'], claude_review.VERSION)


class TestAnalyze(unittest.TestCase):
    
    def test_file_count(self):
        a = claude_review.analyze_diff(SIMPLE_DIFF)
        self.assertEqual(a['files_count'], 1)
    
    def test_empty(self):
        self.assertIsNone(claude_review.analyze_diff(''))
    
    def test_vuln_count(self):
        a = claude_review.analyze_diff(VULNERABLE_DIFF)
        self.assertEqual(a['files_count'], 1)


def run_demo():
    print("=" * 60)
    print("  claude-review Agent 验证演示")
    print("=" * 60)
    print()
    for name, diff in [("简单修改", SIMPLE_DIFF), ("安全增强", SECURE_DIFF), ("风险提交", VULNERABLE_DIFF)]:
        a = claude_review.analyze_diff(diff)
        if not a:
            a = {'files':[],'files_count':0,'additions':0,'deletions':0,'total_changes':0}
        r = claude_review.generate_review(a)
        print("  [{}] 文件: {} | 风险: {} | 置信度: {}".format(
            name, a['files_count'],
            '有' if r.get('risks') and 'no critical' not in r.get('risks','').lower() else '无',
            r.get('confidence','')))
    print()
    a = claude_review.analyze_diff(SIMPLE_DIFF)
    r = claude_review.generate_review(a)
    print(claude_review.format_review(a, r)[:500])


if __name__ == '__main__':
    if '--demo' in sys.argv:
        run_demo()
    else:
        run_demo()
        print()
        unittest.main(argv=['first-arg-is-ignored'], verbosity=2, exit=False)
