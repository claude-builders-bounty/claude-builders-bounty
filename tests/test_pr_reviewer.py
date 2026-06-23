import importlib.util
import sys
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[1] / "agents" / "pr-reviewer" / "claude_review.py"
    spec = importlib.util.spec_from_file_location("claude_review", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["claude_review"] = module
    spec.loader.exec_module(module)
    return module


def test_review_contains_required_sections():
    module = load_module()
    diff = """diff --git a/app.py b/app.py
index 111..222 100644
--- a/app.py
+++ b/app.py
@@ -1 +1,2 @@
-print('old')
+print('new')
+print('done')
"""

    review = module.render_review(diff, "https://github.com/example/repo/pull/1")

    assert "### Summary" in review
    assert "### Identified risks" in review
    assert "### Improvement suggestions" in review
    assert "### Confidence score" in review
    assert "No test file was changed" in review


def test_review_detects_tests_and_sensitive_paths():
    module = load_module()
    diff = """diff --git a/server/auth.py b/server/auth.py
index 111..222 100644
--- a/server/auth.py
+++ b/server/auth.py
@@ -1 +1,2 @@
-token = 'old'
+token = 'new'
+permission = 'admin'
diff --git a/tests/test_auth.py b/tests/test_auth.py
index 333..444 100644
--- a/tests/test_auth.py
+++ b/tests/test_auth.py
@@ -1 +1,2 @@
 assert True
+assert 'admin'
"""

    review = module.render_review(diff)

    assert "Auth, token, secret, or permission-related files changed" in review
    assert "Confirm the touched tests fail before the fix" in review
    assert "Medium" in review or "High" in review
