"""Stdlib-only unit tests for claude_review.

Run from agents/pr-reviewer:

    python tests/test_review.py -v
"""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

THIS = Path(__file__).resolve()
sys.path.insert(0, str(THIS.parent.parent))

import claude_review as cr  # noqa: E402


def _patch(path: str, **fields) -> str:
    """Build a minimal unified diff for tests."""
    return "\n".join(
        [
            f"@@ -1,{fields.get('old_lines', 1)} +1,{fields.get('new_lines', len(fields['add']))} @@",
            *[f"+{line}" for line in fields["add"]],
        ]
    )


def _ctx(files: list[cr.FileChange], **overrides) -> cr.PRContext:
    base = dict(
        owner="acme",
        repo="widgets",
        number=42,
        title="test PR",
        body="motivation goes here",
        author="alice",
        base_sha="0" * 40,
        head_sha="1" * 40,
        files=files,
    )
    base.update(overrides)
    return cr.PRContext(**base)


# ---------------------------------------------------------------------------


class ParsePRUrl(unittest.TestCase):
    def test_canonical(self):
        self.assertEqual(
            cr.parse_pr_url("https://github.com/acme/widgets/pull/42"),
            ("acme", "widgets", 42),
        )

    def test_trailing_slash(self):
        self.assertEqual(
            cr.parse_pr_url("https://github.com/acme/widgets/pull/42/"),
            ("acme", "widgets", 42),
        )

    def test_rejects_non_pr_url(self):
        with self.assertRaises(ValueError):
            cr.parse_pr_url("https://example.com/owner/repo/pull/1")


class SplitPatchLines(unittest.TestCase):
    def test_added_and_removed(self):
        patch = "\n".join(
            [
                "@@ -10,2 +10,3 @@",
                " context",
                "-old line",
                "+new line",
                "+brand new",
            ]
        )
        added, removed = cr._split_patch_lines(patch)
        self.assertEqual(added, [(11, "new line"), (12, "brand new")])
        self.assertEqual(removed, [(11, "old line")])

    def test_handles_multiple_hunks(self):
        patch = "\n".join(
            [
                "@@ -1 +1,2 @@",
                "+a",
                "+b",
                "@@ -50,1 +52,2 @@",
                "+c",
                "+d",
            ]
        )
        added, _ = cr._split_patch_lines(patch)
        self.assertEqual(added, [(1, "a"), (2, "b"), (52, "c"), (53, "d")])


class HeuristicsSecrets(unittest.TestCase):
    def test_aws_key(self):
        fc = cr.FileChange(
            "src/config.py", "modified", 1, 0,
            patch="",
            added_lines=[(3, 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"')],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        sev = [f.severity for f in findings if f.category == "security"]
        self.assertIn("critical", sev, f"expected security finding, got {findings}")

    def test_openai_key(self):
        fc = cr.FileChange(
            "src/x.ts", "modified", 1, 0,
            patch="",
            added_lines=[(1, 'const k = "sk-abc123def456ghi789jklm"')],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any(f.severity == "critical" for f in findings))

    def test_no_false_positive_on_short_token(self):
        fc = cr.FileChange(
            "src/x.py", "modified", 1, 0,
            patch="",
            added_lines=[(1, "user_key = 'short'")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertFalse(
            any(f.category == "security" for f in findings),
            "short token should not trigger secret heuristic",
        )


class HeuristicsDanger(unittest.TestCase):
    def test_eval_flagged(self):
        fc = cr.FileChange(
            "src/x.py", "modified", 1, 0,
            patch="",
            added_lines=[(1, "result = eval(user_input)")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any("eval" in f.message for f in findings))

    def test_shell_true_flagged(self):
        fc = cr.FileChange(
            "src/x.py", "modified", 1, 0,
            patch="",
            added_lines=[(1, "subprocess.run(cmd, shell=True)")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any("shell=True" in f.message for f in findings))

    def test_dangerously_set_inner_html(self):
        fc = cr.FileChange(
            "src/X.tsx", "modified", 1, 0,
            patch="",
            added_lines=[(1, "<div dangerouslySetInnerHTML={{__html: input}} />")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any("dangerouslySetInnerHTML" in f.message for f in findings))


class HeuristicsHygiene(unittest.TestCase):
    def test_console_log(self):
        fc = cr.FileChange(
            "src/x.ts", "modified", 1, 0,
            patch="",
            added_lines=[(1, "console.log('debug', x)")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any("console.log" in f.message for f in findings))

    def test_todo_marker(self):
        fc = cr.FileChange(
            "src/x.py", "modified", 1, 0,
            patch="",
            added_lines=[(1, "# TODO: handle the edge case")],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any(f.category == "hygiene" for f in findings))


class HeuristicsTestCoverage(unittest.TestCase):
    def test_warns_when_source_changed_without_tests(self):
        src = cr.FileChange(
            "src/feature.py", "modified", 50, 0,
            patch="",
            added_lines=[(i, f"line {i}") for i in range(1, 51)],
        )
        ctx = _ctx([src])
        findings = cr.run_heuristics(ctx)
        self.assertTrue(any(f.category == "testing" for f in findings))

    def test_no_warning_when_tests_changed(self):
        src = cr.FileChange(
            "src/feature.py", "modified", 50, 0,
            patch="",
            added_lines=[(i, f"line {i}") for i in range(1, 51)],
        )
        test = cr.FileChange(
            "tests/test_feature.py", "modified", 10, 0,
            patch="",
            added_lines=[(i, f"def test_{i}(): pass") for i in range(1, 11)],
        )
        findings = cr.run_heuristics(_ctx([src, test]))
        self.assertFalse(
            any(f.category == "testing" for f in findings),
            "tests touched — no missing-tests finding expected",
        )

    def test_skips_tiny_changes(self):
        # 5 added lines is below the 30-line threshold for the missing-tests warning
        src = cr.FileChange(
            "src/x.py", "modified", 5, 0,
            patch="",
            added_lines=[(i, f"x = {i}") for i in range(1, 6)],
        )
        findings = cr.run_heuristics(_ctx([src]))
        self.assertFalse(any(f.category == "testing" for f in findings))


class HeuristicsSize(unittest.TestCase):
    def test_large_diff_warning(self):
        # Build a single 900-line + 0-line file (additions=900, deletions=0)
        fc = cr.FileChange(
            "src/big.py", "modified", 900, 0,
            patch="",
            added_lines=[(i, "x") for i in range(900)],
        )
        findings = cr.run_heuristics(_ctx([fc]))
        self.assertTrue(any(f.category == "size" for f in findings))


class ConfidenceScore(unittest.TestCase):
    def test_high_for_clean_small_diff(self):
        fc = cr.FileChange("src/x.py", "modified", 5, 0, patch="", added_lines=[])
        score, label = cr.confidence_score(_ctx([fc]), [])
        self.assertGreaterEqual(score, 0.7)
        self.assertEqual(label, "High")

    def test_low_for_critical_findings(self):
        fc = cr.FileChange("src/x.py", "modified", 5, 0, patch="", added_lines=[])
        findings = [
            cr.Finding("critical", "security", "secret leak"),
            cr.Finding("critical", "security", "another"),
            cr.Finding("critical", "security", "third"),
        ]
        score, label = cr.confidence_score(_ctx([fc]), findings)
        self.assertLess(score, 0.4)
        self.assertEqual(label, "Low")

    def test_medium_for_large_clean_diff(self):
        fc = cr.FileChange("src/x.py", "modified", 700, 100, patch="", added_lines=[])
        score, label = cr.confidence_score(_ctx([fc]), [])
        self.assertEqual(label, "Medium")


class RenderMarkdown(unittest.TestCase):
    def _render(self, ctx, findings, llm_body=None):
        score, label = cr.confidence_score(ctx, findings)
        return cr.render_markdown(ctx, findings, label, score, llm_body, "heuristic")

    def test_includes_marker_and_pr_url(self):
        fc = cr.FileChange("src/x.py", "modified", 5, 0, patch="", added_lines=[])
        out = self._render(_ctx([fc]), [])
        self.assertIn(cr.REVIEW_MARKER, out)
        self.assertIn("https://github.com/acme/widgets/pull/42", out)

    def test_renders_heuristic_sections_when_no_llm(self):
        fc = cr.FileChange("src/x.py", "modified", 5, 0, patch="", added_lines=[])
        out = self._render(_ctx([fc]), [])
        self.assertIn("### Summary", out)
        self.assertIn("### Risks", out)
        self.assertIn("### Suggestions", out)
        self.assertIn("### Confidence", out)

    def test_uses_llm_body_when_provided(self):
        fc = cr.FileChange("src/x.py", "modified", 5, 0, patch="", added_lines=[])
        out = self._render(_ctx([fc]), [], llm_body="**Summary** custom body")
        self.assertIn("**Summary** custom body", out)
        # Heuristic section headers must NOT appear when LLM supplies the body
        self.assertNotIn("### Risks", out)


class CLIIntegration(unittest.TestCase):
    """Mock fetch_pr to exercise the full main() path without network."""

    def setUp(self):
        fc = cr.FileChange(
            "src/x.py", "modified", 5, 0,
            patch="@@ -1,1 +1,1 @@\n+print(x)",
            added_lines=[(1, "print(x)")],
        )
        self.ctx = _ctx([fc])

    def test_heuristic_mode_prints_markdown(self):
        with patch.object(cr, "fetch_pr", return_value=self.ctx):
            stdout = io.StringIO()
            with patch.object(sys, "stdout", stdout):
                rc = cr.main(["--pr", "https://github.com/acme/widgets/pull/42", "--mode", "heuristic"])
        self.assertEqual(rc, 0)
        body = stdout.getvalue()
        self.assertIn(cr.REVIEW_MARKER, body)
        self.assertIn("Confidence", body)

    def test_json_envelope(self):
        with patch.object(cr, "fetch_pr", return_value=self.ctx):
            stdout = io.StringIO()
            with patch.object(sys, "stdout", stdout):
                rc = cr.main(
                    [
                        "--pr",
                        "https://github.com/acme/widgets/pull/42",
                        "--mode",
                        "heuristic",
                        "--json",
                    ]
                )
        self.assertEqual(rc, 0)
        env = json.loads(stdout.getvalue())
        self.assertEqual(env["pr"], "https://github.com/acme/widgets/pull/42")
        self.assertIn("markdown", env)
        self.assertIn("confidence", env)
        self.assertIn(env["confidence"]["label"], ("High", "Medium", "Low"))

    def test_llm_mode_without_key_errors(self):
        with patch.object(cr, "fetch_pr", return_value=self.ctx), patch.dict(
            "os.environ", {"ANTHROPIC_API_KEY": ""}, clear=False
        ), patch.object(cr.os.environ, "get", side_effect=lambda k, d=None: None if k == "ANTHROPIC_API_KEY" else d):
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
                rc = cr.main(
                    [
                        "--pr",
                        "https://github.com/acme/widgets/pull/42",
                        "--mode",
                        "llm",
                    ]
                )
        self.assertEqual(rc, 2)
        self.assertIn("ANTHROPIC_API_KEY", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
