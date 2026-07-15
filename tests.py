#!/usr/bin/env python3
"""Tests for claude-review PR reviewer."""
import os, subprocess, sys

CLI = os.path.join(os.path.dirname(__file__), "agents", "claude-review", "claude_review.py")

def test_cli_help():
    proc = subprocess.run([sys.executable, CLI, "--help"], capture_output=True, text=True, timeout=10)
    assert proc.returncode == 0, f"Help failed: {proc.stderr}"
    assert "--pr" in proc.stdout, "Help should mention --pr"

def test_cli_requires_pr():
    proc = subprocess.run([sys.executable, CLI], capture_output=True, text=True, timeout=10)
    assert proc.returncode != 0, "Should fail without --pr"

def test_cli_parses_pr_url():
    proc = subprocess.run([sys.executable, CLI, "--pr", "https://github.com/o/r/pull/1"], capture_output=True, text=True, timeout=10)
    assert "ANTHROPIC_API_KEY" in proc.stderr or "api key" in proc.stderr.lower(), f"Expected API key error: {proc.stderr[:200]}"

def test_github_action_exists():
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "agents", "claude-review", "claude-review-action.yml"))

def test_readme_exists():
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "agents", "claude-review", "README.md"))

def test_readme_has_samples():
    content = open(os.path.join(os.path.dirname(__file__), "agents", "claude-review", "README.md")).read()
    assert "Summary of Changes" in content

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    p = f = 0
    for t in tests:
        try: t(); print(f"  ✅ {t.__name__}"); p += 1
        except Exception as e: print(f"  ❌ {t.__name__}: {e}"); f += 1
    print(f"\nResults: {p} passed, {f} failed out of {len(tests)}")
