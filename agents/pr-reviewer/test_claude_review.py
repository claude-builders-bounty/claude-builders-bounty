#!/usr/bin/env python3
"""Smoke tests for the PR reviewer CLI."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile


MODULE_PATH = pathlib.Path(__file__).with_name("claude-review.py")
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
assert SPEC and SPEC.loader
claude_review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = claude_review
SPEC.loader.exec_module(claude_review)


SAMPLE_DIFF = """\
diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,6 @@
 import os
+
+def run(value):
+    return eval(value)
 print("hello")
diff --git a/requirements.txt b/requirements.txt
index 1111111..2222222 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -1 +1,2 @@
 flask==3.0.0
+requests==2.32.0
"""


def test_parser_and_findings() -> None:
    stats = claude_review.parse_diff(SAMPLE_DIFF)
    findings, suggestions = claude_review.build_findings(stats, SAMPLE_DIFF)

    assert len(stats.changed_files) == 2
    assert stats.total_additions == 4
    assert any("Dependency" in finding.title for finding in findings)
    assert any("injection" in finding.title.lower() for finding in findings)
    assert suggestions


def test_cli_writes_markdown() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        diff_path = pathlib.Path(temp_dir) / "sample.diff"
        output_path = pathlib.Path(temp_dir) / "review.md"
        diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")

        code = claude_review.main([
            "--diff-file",
            str(diff_path),
            "--output",
            str(output_path),
        ])

        report = output_path.read_text(encoding="utf-8")
        assert code == 0
        assert "# Claude PR Review" in report
        assert "## Risk Assessment" in report
        assert "## Suggested Improvements" in report
        assert "## Confidence" in report


if __name__ == "__main__":
    test_parser_and_findings()
    test_cli_writes_markdown()
    print("All PR reviewer smoke tests passed.")
