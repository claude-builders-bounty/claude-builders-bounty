#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agents" / "pr-reviewer" / "claude_review.py"


SAMPLE_DIFF = """diff --git a/app/api/billing/route.ts b/app/api/billing/route.ts
index 1111111..2222222 100644
--- a/app/api/billing/route.ts
+++ b/app/api/billing/route.ts
@@ -1,3 +1,6 @@
+const token = "test-placeholder-token";
+export async function DELETE() {
+  await db.execute("DELETE FROM invoices");
+}
 export async function GET() {
   return Response.json({ ok: true });
 }
"""


class PRReviewerTests(unittest.TestCase):
    def test_generates_structured_review_from_diff_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "sample.diff"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(SCRIPT), "--diff", str(diff_path)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("## Automated PR Review", result.stdout)
        self.assertIn("Risk: **High**", result.stdout)
        self.assertIn("secret-like strings detected", result.stdout)
        self.assertIn("destructive command patterns detected", result.stdout)
        self.assertIn("Add or update tests", result.stdout)


if __name__ == "__main__":
    unittest.main()
