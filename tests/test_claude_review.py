import unittest

from bin.claude_review import analyze, parse_diff, render_markdown


SAMPLE_DIFF = """diff --git a/app/api/users/route.ts b/app/api/users/route.ts
index 111..222 100644
--- a/app/api/users/route.ts
+++ b/app/api/users/route.ts
@@ -1,3 +1,7 @@
+import { getSession } from '@/lib/auth/session';
+import { db } from '@/lib/db';
 export async function GET() {
+  await db.execute('DELETE FROM sessions');
+  const session = await getSession();
   return Response.json({ ok: true });
 }
diff --git a/tests/users.test.ts b/tests/users.test.ts
index 333..444 100644
--- a/tests/users.test.ts
+++ b/tests/users.test.ts
@@ -0,0 +1,3 @@
+test('users route', () => {
+  expect(true).toBe(true);
+});
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_diff_counts_files_and_lines(self):
        files = parse_diff(SAMPLE_DIFF)
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0].path, "app/api/users/route.ts")
        self.assertGreater(files[0].added, 0)
        self.assertIn("auth", files[0].risk_tags)
        self.assertIn("database", files[0].risk_tags)

    def test_analyze_renders_required_sections(self):
        review = analyze("https://github.com/example/repo/pull/1", SAMPLE_DIFF)
        markdown = render_markdown(review)
        self.assertIn("### Summary of changes", markdown)
        self.assertIn("### Identified risks", markdown)
        self.assertIn("### Improvement suggestions", markdown)
        self.assertRegex(markdown, r"### Confidence score: (Low|Medium|High)")
        self.assertIn("authorization", markdown.lower())


if __name__ == "__main__":
    unittest.main()
