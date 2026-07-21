#!/usr/bin/env python3
"""Tests for changelog-gen."""
import os, subprocess, sys, tempfile

CLI = os.path.join(os.path.dirname(__file__), "changelog-generator", "changelog_gen.py")

def test_cli_help():
    proc = subprocess.run([sys.executable, CLI, "--help"], capture_output=True, text=True, timeout=10)
    assert proc.returncode == 0, f"Help failed: {proc.stderr}"
    assert "--since" in proc.stdout or "--version" in proc.stdout

def test_cli_runs_in_git_repo():
    proc = subprocess.run([sys.executable, CLI, "--since", "HEAD~5"], capture_output=True, text=True, timeout=10, cwd=os.path.dirname(__file__))
    assert proc.returncode == 0 or "No commits" in proc.stderr

def test_cli_with_version():
    proc = subprocess.run([sys.executable, CLI, "--since", "HEAD~3", "--version", "1.0.0"], capture_output=True, text=True, timeout=10, cwd=os.path.dirname(__file__))
    if proc.returncode == 0 and proc.stdout.strip():
        assert "1.0.0" in proc.stdout

def test_bash_wrapper_exists():
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "changelog-generator", "changelog.sh"))

def test_skill_md_exists():
    assert os.path.exists(os.path.join(os.path.dirname(__file__), "changelog-generator", "SKILL.md"))

def test_readme_has_sample():
    content = open(os.path.join(os.path.dirname(__file__), "changelog-generator", "README.md")).read()
    assert "Sample Output" in content or "## [" in content

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    p = f = 0
    for t in tests:
        try: t(); print(f"  ✅ {t.__name__}"); p += 1
        except Exception as e: print(f"  ❌ {t.__name__}: {e}"); f += 1
    print(f"\nResults: {p} passed, {f} failed out of {len(tests)}")
