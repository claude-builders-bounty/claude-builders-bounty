#!/usr/bin/env python3
"""
Test Suite for Claude Code PR Review Sub-Agent
Tests static analysis, security detection, and Markdown formatting across 2 real PR scenarios.
"""

import subprocess
import sys
import os

RISKY_DIFF = """diff --git a/src/api/auth.ts b/src/api/auth.ts
index 1111111..2222222 100644
--- a/src/api/auth.ts
+++ b/src/api/auth.ts
@@ -10,4 +10,12 @@ export function authenticateUser(req) {
+    const apiKey = "sk_live_983749823749823749823";
+    const query = "SELECT * FROM users WHERE email = '" + req.body.email + "'";
+    eval(req.body.customCallback);
+    return db.raw(query);
 }
"""

CLEAN_TESTED_DIFF = """diff --git a/src/math/calculator.ts b/src/math/calculator.ts
index 3333333..4444444 100644
--- a/src/math/calculator.ts
+++ b/src/math/calculator.ts
@@ -5,3 +5,7 @@ export function add(a: number, b: number): number {
     return a + b;
 }
+export function multiply(a: number, b: number): number {
+    return a * b;
+}
diff --git a/tests/calculator.test.ts b/tests/calculator.test.ts
new file mode 100644
index 0000000..5555555
--- /dev/null
+++ b/tests/calculator.test.ts
@@ -0,0 +1,8 @@
+import { describe, it, expect } from "vitest";
+import { multiply } from "../src/math/calculator";
+
+describe("multiply", () => {
+    it("should multiply two positive numbers", () => {
+        expect(multiply(3, 4)).toBe(12);
+    });
+});
"""

def test_pr_reviewer():
    script = os.path.abspath("claude_review.py")

    # Test Scenario 1: Risky PR
    res1 = subprocess.run([sys.executable, script], input=RISKY_DIFF, text=True, capture_output=True)
    assert res1.returncode == 0, f"Reviewer failed on risky diff: {res1.stderr}"
    out1 = res1.stdout
    print("=== REVIEW 1: RISKY PR ===")
    print(out1)

    assert "Summary of Changes" in out1
    assert "Identified Risks" in out1
    assert "Security" in out1
    assert "hardcoded credential" in out1 or "token" in out1
    assert "eval" in out1
    assert "Confidence Score: **`Low`**" in out1

    # Test Scenario 2: Clean Tested PR
    res2 = subprocess.run([sys.executable, script], input=CLEAN_TESTED_DIFF, text=True, capture_output=True)
    assert res2.returncode == 0, f"Reviewer failed on clean diff: {res2.stderr}"
    out2 = res2.stdout
    print("=== REVIEW 2: CLEAN TESTED PR ===")
    print(out2)

    assert "Summary of Changes" in out2
    assert "Confidence Score: **`High`**" in out2
    assert "Comprehensive test modifications were included" in out2

    print("\n[✓] ALL PR REVIEW AGENT ACCEPTANCE CRITERIA VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    test_pr_reviewer()
