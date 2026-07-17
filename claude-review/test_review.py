#!/usr/bin/env python3
"""Test script for claude-review — validates GitHub fetching and CLI works."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))

from claude_review import parse_pr_url, fetch_pr_metadata, fetch_pr_diff, fetch_pr_files


def test_parse_urls():
    """Test URL parsing with various formats."""
    cases = [
        ("https://github.com/anthropics/anthropic-sdk-python/pull/100",
         ("anthropics", "anthropic-sdk-python", 100)),
        ("github.com/owner/repo/pull/42",
         ("owner", "repo", 42)),
        ("owner/repo#99",
         ("owner", "repo", 99)),
        ("https://www.github.com/org/project/pull/1",
         ("org", "project", 1)),
    ]
    for url, expected in cases:
        result = parse_pr_url(url)
        assert result == expected, f"Failed for {url}: got {result}"
        print(f"  PASS: {url} -> {result}")
    print("URL parsing: ALL PASS")


def test_fetch_pr(owner, repo, pr_num):
    """Test fetching PR data from GitHub."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    print(f"\nTesting PR fetch: {owner}/{repo}#{pr_num}")
    meta = fetch_pr_metadata(owner, repo, pr_num, token)
    print(f"  Title: {meta['title']}")
    print(f"  Author: {meta['user']['login']}")
    print(f"  Files: {meta['changed_files']}")
    print(f"  +{meta['additions']}/-{meta['deletions']}")

    diff = fetch_pr_diff(owner, repo, pr_num, token)
    print(f"  Diff: {len(diff)} chars")

    files = fetch_pr_files(owner, repo, pr_num, token)
    print(f"  File list: {[f['filename'] for f in files[:5]]}")

    assert len(diff) > 0, "Diff is empty"
    assert meta["title"], "Title is empty"
    print(f"  PASS: {owner}/{repo}#{pr_num}")


def test_cli_interface():
    """Test the CLI interface."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "claude_review", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"CLI help failed: {result.stderr}"
    assert "claude-review" in result.stdout.lower() or "usage" in result.stdout.lower()
    print("\nCLI --help: PASS")


def main():
    print("=" * 60)
    print("claude-review Test Suite")
    print("=" * 60)

    # Test 1: URL parsing
    print("\n[1] URL Parsing")
    test_parse_urls()

    # Test 2: CLI interface
    print("\n[2] CLI Interface")
    test_cli_interface()

    # Test 3: Fetch real PRs (no token needed for public repos)
    print("\n[3] Fetch Real PRs")
    test_fetch_pr("anthropics", "anthropic-sdk-python", 100)
    test_fetch_pr("python", "cpython", 117000)

    # Test 4: JSON output flag
    print("\n[4] CLI JSON flag")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "claude_review", "--help"],
        capture_output=True, text=True
    )
    assert "--json" in result.stdout or "json" in result.stdout.lower()
    print("  PASS: --json flag present")

    # Test 5: Output flag
    assert "-o" in result.stdout or "output" in result.stdout.lower()
    print("  PASS: -o flag present")

    # Test 6: Model flag
    assert "--model" in result.stdout or "model" in result.stdout.lower()
    print("  PASS: --model flag present")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
