# -*- coding: utf-8 -*-
import subprocess
import os

import sys
import io

def test_reviewer():
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Testing PR Reviewer...")

    # Create a dummy diff with some issues
    dummy_diff = """diff --git a/test.py b/test.py
index 0000000..1234567
--- a/test.py
+++ b/test.py
@@ -1,3 +1,10 @@
 def test():
-    pass
+    # TODO: fix this
+    password = "supersecretpassword123"
+    eval("print('hello')")
+    if True:
+        if True:
+            if True:
+                if True:
+                    print("Deeply nested")
"""
    with open("dummy.diff", "w") as f:
        f.write(dummy_diff)

    # Run the reviewer
    cmd = ["python", "reviewer.py", "dummy.diff"]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")

    print("Output:")
    print(result.stdout)

    # Check for expected findings
    assert "TODO_COMMENT" in result.stdout or "todo_comment" in result.stdout
    assert "HARDCODED_SECRET" in result.stdout or "hardcoded_secret" in result.stdout
    assert "UNSAFE_EVAL" in result.stdout or "unsafe_eval" in result.stdout
    assert "High Cognitive Complexity" in result.stdout

    print("Test passed!")
    os.remove("dummy.diff")

if __name__ == "__main__":
    test_reviewer()
