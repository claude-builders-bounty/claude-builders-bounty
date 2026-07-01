import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "claude-review"
SAMPLE_DIFF = """diff --git a/src/auth.py b/src/auth.py
index 111..222 100644
--- a/src/auth.py
+++ b/src/auth.py
@@ -1,2 +1,3 @@
 def login():
-    return True
+    return check_token()
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 111..222 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -1,2 +1,3 @@
+def test_login():
+    assert True
"""
def test_cli_outputs_structured_review(tmp_path):
    diff_file = tmp_path / "sample.diff"
    diff_file.write_text(SAMPLE_DIFF)
    result = subprocess.run([str(CLI), "--diff-file", str(diff_file)], text=True, capture_output=True)
    assert result.returncode == 0
    out = result.stdout
    assert "## Claude Review" in out
    assert "### Summary" in out
    assert "### Potential Issues" in out
    assert "### Suggested Tests" in out
    assert "### Reviewer Questions" in out
    assert "src/auth.py" in out
    assert "tests/test_auth.py" in out
