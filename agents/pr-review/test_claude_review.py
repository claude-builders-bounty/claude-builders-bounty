"""Tests for the claude-review agent (no network calls required)."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import claude_review as cr


# ──────────────────────────────────────────────────────────────────────────────
# parse_pr_url
# ──────────────────────────────────────────────────────────────────────────────

def test_parse_pr_url_valid():
    owner, repo, number = cr.parse_pr_url("https://github.com/psf/requests/pull/7441")
    assert owner == "psf"
    assert repo == "requests"
    assert number == 7441


def test_parse_pr_url_trailing_slash():
    owner, repo, number = cr.parse_pr_url("https://github.com/foo/bar/pull/99/")
    assert owner == "foo"
    assert number == 99


def test_parse_pr_url_invalid():
    try:
        cr.parse_pr_url("https://github.com/foo/bar")
        assert False, "should raise"
    except ValueError:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# analyse_diff — security patterns
# ──────────────────────────────────────────────────────────────────────────────

DIFF_WITH_SECRET = """\
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,3 +1,3 @@
+API_KEY = "sk-abc123secretvalue"
 HOST = "localhost"
"""

DIFF_WITH_EVAL = """\
diff --git a/utils.py b/utils.py
--- a/utils.py
+++ b/utils.py
@@ -10,3 +10,3 @@
+result = eval(user_input)
"""

DIFF_CLEAN = """\
diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,3 +1,3 @@
+print("hello world")
"""


def test_detect_hardcoded_secret():
    findings = cr.analyse_diff(DIFF_WITH_SECRET)
    assert any(f.category == "Security" for f in findings), findings


def test_detect_eval():
    findings = cr.analyse_diff(DIFF_WITH_EVAL)
    assert any("eval" in f.description.lower() for f in findings), findings


def test_clean_diff_no_findings():
    findings = cr.analyse_diff(DIFF_CLEAN)
    assert findings == []


# ──────────────────────────────────────────────────────────────────────────────
# compute_confidence
# ──────────────────────────────────────────────────────────────────────────────

def test_confidence_high_small_diff():
    meta = {"additions": 10, "deletions": 5}
    assert cr.compute_confidence(meta, []) == "High"


def test_confidence_low_large_diff():
    meta = {"additions": 2000, "deletions": 100}
    assert cr.compute_confidence(meta, []) == "Low"


def test_confidence_medium_critical_finding():
    meta = {"additions": 50, "deletions": 20}
    finding = cr.Finding("CRITICAL", "Security", "foo.py", 1, "desc", "fix")
    assert cr.compute_confidence(meta, [finding]) == "Medium"


# ──────────────────────────────────────────────────────────────────────────────
# render_markdown — output structure
# ──────────────────────────────────────────────────────────────────────────────

def test_render_markdown_contains_required_sections():
    result = cr.ReviewResult(
        pr_url="https://github.com/owner/repo/pull/1",
        pr_title="Test PR",
        pr_author="tester",
        summary="Test summary.",
        risks=["Risk one"],
        suggestions=["Suggestion one"],
        findings=[],
        confidence="High",
        files_changed=1,
        lines_added=10,
        lines_removed=2,
    )
    md = cr.render_markdown(result)
    assert "## 🤖 Claude Code Review" in md
    assert "### 📋 Summary" in md
    assert "### ⚠️ Identified Risks" in md
    assert "### 💡 Improvement Suggestions" in md
    assert "Confidence" in md
    assert "High" in md


# ──────────────────────────────────────────────────────────────────────────────
# Output format test — structured sections match acceptance criteria
# ──────────────────────────────────────────────────────────────────────────────

def test_output_has_all_acceptance_criteria_sections():
    """Acceptance criteria require: Summary, Risks, Suggestions, Confidence."""
    result = cr.ReviewResult(
        pr_url="https://github.com/x/y/pull/1",
        pr_title="AC test",
        pr_author="bot",
        summary="Some changes were made.",
        risks=["No critical risks."],
        suggestions=["Add tests."],
        findings=[],
        confidence="Medium",
        files_changed=3,
        lines_added=50,
        lines_removed=10,
    )
    md = cr.render_markdown(result)
    for required in ["Summary", "Identified Risks", "Improvement Suggestions", "Confidence"]:
        assert required in md, f"Missing section: {required}"


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✅ {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
