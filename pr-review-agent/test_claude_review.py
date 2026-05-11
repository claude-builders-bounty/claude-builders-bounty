#!/usr/bin/env python3
import importlib.machinery
import importlib.util
import pathlib


module_path = pathlib.Path("pr-review-agent/claude-review")
loader = importlib.machinery.SourceFileLoader("claude_review", str(module_path))
spec = importlib.util.spec_from_loader("claude_review", loader)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

sample_diff = """diff --git a/package.json b/package.json
index 111..222 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
+  "scripts": {"test": "vitest"},
   "dependencies": {}
 }
diff --git a/src/run.ts b/src/run.ts
index 111..222 100644
--- a/src/run.ts
+++ b/src/run.ts
@@ -1,2 +1,3 @@
+eval(input)
 console.log("ok")
"""

files = module.changed_files(sample_diff)
assert files == ["package.json", "src/run.ts"], files

risks = module.detect_risks(sample_diff, files)
assert any("Dependency metadata" in risk for risk in risks), risks
assert any("dynamic evaluation" in risk for risk in risks), risks
assert any("No obvious test files" in risk for risk in risks), risks

review = module.render(
    "https://github.com/example/repo/pull/1",
    {"title": "Example PR", "user": {"login": "octo"}},
    sample_diff,
)
assert "### Summary" in review
assert "### Identified Risks" in review
assert "### Improvement Suggestions" in review
assert "### Confidence:" in review

print("pr review agent tests passed")
