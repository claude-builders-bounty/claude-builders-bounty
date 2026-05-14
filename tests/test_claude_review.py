from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "claude-review"


class ClaudeReviewCliTest(unittest.TestCase):
    def run_review(self, diff: str) -> str:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(textwrap.dedent(diff).strip() + "\n")
            path = handle.name

        result = subprocess.run(
            [sys.executable, str(CLI), "--diff-file", path],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_outputs_required_sections(self) -> None:
        output = self.run_review(
            """
            diff --git a/src/auth.ts b/src/auth.ts
            index 1111111..2222222 100644
            --- a/src/auth.ts
            +++ b/src/auth.ts
            @@ -1,2 +1,3 @@
             export function canRead() {
            +  console.log("debug");
               return true;
             }
            """
        )

        self.assertIn("## Summary", output)
        self.assertIn("## Identified Risks", output)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("## Confidence", output)
        self.assertIn("Authentication", output)
        self.assertIn("Debug", output)

    def test_empty_diff_is_low_confidence(self) -> None:
        output = self.run_review("")
        self.assertIn("No diff content was found", output)
        self.assertIn("Low", output)


if __name__ == "__main__":
    unittest.main()
