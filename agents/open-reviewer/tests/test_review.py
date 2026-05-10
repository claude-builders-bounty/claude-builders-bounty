#!/usr/bin/env python3
"""Tests for open-reviewer CLI."""

import json
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bin"))

import importlib
_mod = importlib.import_module("claude-review")

parse_pr_url = _mod.parse_pr_url
compute_confidence = _mod.compute_confidence
build_report = _mod.build_report
_heuristic_security = _mod._heuristic_security
_heuristic_quality = _mod._heuristic_quality

# Old import (doesn't work with hyphen filename):
# from claude_review import parse_pr_url, ...


# ── parse_pr_url ────────────────────────────────────────────────────────────

def test_parse_pr_url():
    owner, repo, num = parse_pr_url("https://github.com/psf/requests/pull/7401")
    assert owner == "psf"
    assert repo == "requests"
    assert num == 7401


def test_parse_pr_url_invalid():
    try:
        parse_pr_url("https://github.com/psf/requests/issues/7401")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# ── _heuristic_security ────────────────────────────────────────────────────

def test_security_hardcoded_credential():
    diff = 'api_key = "sk-abcdef1234567890"'
    findings = _heuristic_security(diff)
    assert any(f["severity"] == "CRITICAL" and "credential" in f["type"].lower() for f in findings)


def test_security_eval():
    diff = "result = eval(user_input)"
    findings = _heuristic_security(diff)
    assert any(f["severity"] == "HIGH" and "injection" in f["type"].lower() for f in findings)


def test_security_shell_true():
    diff = "subprocess.run(cmd, shell=True)"
    findings = _heuristic_security(diff)
    assert any(f["severity"] == "HIGH" and "Shell" in f["type"] for f in findings)


def test_security_clean():
    diff = "x = 1 + 2\ny = x * 3\n"
    findings = _heuristic_security(diff)
    assert len(findings) == 0


# ── _heuristic_quality ─────────────────────────────────────────────────────

def test_quality_missing_tests():
    files = [{"filename": "src/app.py", "additions": 50, "deletions": 10}]
    diff = "def new_feature():\n    pass\n"
    findings = _heuristic_quality(files, diff)
    assert any(f["type"] == "Missing tests" for f in findings)


def test_quality_has_tests():
    files = [
        {"filename": "src/app.py", "additions": 50, "deletions": 10},
        {"filename": "tests/test_app.py", "additions": 30, "deletions": 0},
    ]
    diff = "def new_feature():\n    pass\n"
    findings = _heuristic_quality(files, diff)
    assert not any(f["type"] == "Missing tests" for f in findings)


def test_quality_large_diff():
    files = [{"filename": f"src/file{i}.py", "additions": 200, "deletions": 50} for i in range(10)]
    diff = ""
    findings = _heuristic_quality(files, diff)
    assert any(f["type"] == "Large diff" for f in findings)


# ── compute_confidence ─────────────────────────────────────────────────────

def test_confidence_high():
    pr = {"additions": 10, "deletions": 5, "body": "Fix typo"}
    conf = compute_confidence(pr, [], [])
    assert conf["score"] >= 0.70
    assert conf["label"] == "High"


def test_confidence_low():
    pr = {"additions": 1000, "deletions": 800, "body": ""}
    security = [
        {"severity": "CRITICAL", "type": "key"},
        {"severity": "CRITICAL", "type": "key2"},
    ]
    quality = [{"severity": "HIGH", "type": "no tests"}]
    conf = compute_confidence(pr, security, quality)
    assert conf["score"] < 0.40
    assert conf["label"] == "Low"


def test_confidence_medium():
    pr = {"additions": 300, "deletions": 100, "body": "Add feature X"}
    security = [{"severity": "HIGH", "type": "eval"}]
    quality = [{"severity": "MEDIUM", "type": "todo"}]
    conf = compute_confidence(pr, security, quality)
    assert 0.40 <= conf["score"] < 0.70
    assert conf["label"] == "Medium"


# ── build_report ───────────────────────────────────────────────────────────

def test_build_report_markdown():
    pr = {
        "number": 42,
        "title": "Add feature X",
        "user": {"login": "dev"},
        "additions": 50,
        "deletions": 10,
        "changed_files": 3,
        "body": "New feature",
    }
    security = [{"severity": "HIGH", "type": "eval", "snippet": "eval(x)"}]
    quality = [{"severity": "MEDIUM", "type": "TODO", "snippet": "TODO: fix"}]
    confidence = {"score": 0.65, "label": "Medium"}
    report = build_report(pr, security, quality, confidence)
    assert "🤖 Claude Review" in report
    assert "#42" in report
    assert "eval" in report
    assert "0.65" in report
    assert "Medium" in report


def test_build_report_json():
    pr = {
        "number": 42,
        "title": "Add feature X",
        "user": {"login": "dev"},
        "additions": 50,
        "deletions": 10,
        "changed_files": 3,
        "body": "New feature",
    }
    security = []
    quality = []
    confidence = {"score": 0.85, "label": "High"}
    report = build_report(pr, security, quality, confidence, json_mode=True)
    data = json.loads(report)
    assert data["pr"] == 42
    assert data["confidence"]["score"] == 0.85


# ── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import __main__
    # Simple test runner
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
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
