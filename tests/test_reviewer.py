from claude_review.reviewer import ReviewEngine


SAMPLE_DIFF_WITH_VULN = """diff --git a/app/auth.py b/app/auth.py
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/app/auth.py
@@ -0,0 +1,15 @@
+import requests
+
+API_KEY = "sk-live-1234567890abcdef"
+
+def fetch_user_data(user_id):
+    query = "SELECT * FROM users WHERE id = " + str(user_id)
+    res = requests.get("https://api.example.com/user/" + user_id)
+    return res.json()
+"""

SAMPLE_SAFE_DIFF = """diff --git a/utils/math.py b/utils/math.py
new file mode 100644
index 0000000..abcdef1
--- /dev/null
+++ b/utils/math.py
@@ -0,0 +1,8 @@
+def add(a: int, b: int) -> int:
+    return a + b
+
diff --git a/tests/test_math.py b/tests/test_math.py
new file mode 100644
index 0000000..abcdef2
--- /dev/null
+++ b/tests/test_math.py
@@ -0,0 +1,6 @@
+from utils.math import add
+
+def test_add():
+    assert add(2, 3) == 5
+"""


def test_parse_diff_files():
    engine = ReviewEngine()
    files = engine.parse_diff_files(SAMPLE_DIFF_WITH_VULN)
    assert len(files) == 1
    assert files[0]["path"] == "app/auth.py"
    assert files[0]["additions_count"] > 0


def test_risk_detection_on_vulnerabilities():
    engine = ReviewEngine()
    metadata = {
        "title": "Add user authentication helper",
        "user": {"login": "testdev"},
        "base": {"ref": "main"},
        "head": {"ref": "feat/auth"}
    }
    review = engine.review(metadata, SAMPLE_DIFF_WITH_VULN)

    # Check risk identification
    risk_text = " ".join(review["risks"])
    assert "Potential Hardcoded Credential" in risk_text
    assert "SQL Injection Vulnerability" in risk_text
    assert "Network Socket Hang Risk" in risk_text
    assert review["confidence"] == "Low"


def test_safe_diff_high_confidence():
    engine = ReviewEngine()
    metadata = {
        "title": "Add math utility and test",
        "user": {"login": "gooddev"},
        "base": {"ref": "main"},
        "head": {"ref": "feat/math"}
    }
    review = engine.review(metadata, SAMPLE_SAFE_DIFF)

    assert review["confidence"] == "High"
    assert len(review["risks"]) == 1
    assert "No critical security vulnerabilities" in review["risks"][0]
