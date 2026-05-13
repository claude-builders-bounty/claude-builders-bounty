import importlib.util
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "claude-review.py"
MODULE = ROOT / "claude_review" / "cli.py"
FIXTURES = ROOT / "tests" / "fixtures"


def load_module():
    spec = importlib.util.spec_from_file_location("claude_review_cli", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ClaudeReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review = load_module()

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        ).stdout

    def test_markdown_contains_required_schema(self):
        output = self.run_cli("--diff-file", str(FIXTURES / "security.diff"))
        self.assertIn("### Summary", output)
        self.assertIn("### Identified Risks", output)
        self.assertIn("### Improvement Suggestions", output)
        self.assertIn("### Confidence Score", output)
        self.assertRegex(output, r"(?m)^(Low|Medium|High)$")

    def test_security_fixture_detects_core_risks(self):
        diff = (FIXTURES / "security.diff").read_text(encoding="utf-8")
        metadata = self.review.PullRequestMetadata(title="security fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        risk_text = " ".join(review.risks).lower()
        self.assertIn("credential", risk_text)
        self.assertIn("delete statement", risk_text)
        self.assertIn("shell=true", risk_text)
        self.assertEqual(review.confidence, "Medium")

    def test_security_fixture_includes_structured_findings_with_locations(self):
        diff = (FIXTURES / "security.diff").read_text(encoding="utf-8")
        metadata = self.review.PullRequestMetadata(title="security fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        by_code = {finding.code: finding for finding in review.findings}
        self.assertEqual(by_code["SECRET_LITERAL"].location, "app/auth.py:4")
        self.assertEqual(by_code["SHELL_TRUE"].location, "app/auth.py:5")
        self.assertEqual(
            by_code["SQL_DELETE_WITHOUT_WHERE"].location,
            "db/migrations/0002_cleanup.sql:1",
        )
        self.assertIn("...", by_code["SECRET_LITERAL"].evidence)

    def test_dependency_fixture_tracks_changed_symbol_callers(self):
        diff = (FIXTURES / "dependency_impact.diff").read_text(encoding="utf-8")
        metadata = self.review.PullRequestMetadata(title="dependency fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        by_code = {finding.code: finding for finding in review.findings}
        finding = by_code["DEPENDENT_USAGE_UNTESTED"]
        self.assertEqual(finding.location, "src/checkout.py:4")
        self.assertIn("calculate_total", finding.message)
        self.assertIn("calculate_total", finding.suggestion)
        self.assertEqual(review.confidence, "Medium")

    def test_repo_root_scan_tracks_dependents_outside_diff(self):
        diff = """diff --git a/src/pricing.py b/src/pricing.py
index 1111111..2222222 100644
--- a/src/pricing.py
+++ b/src/pricing.py
@@ -1,2 +1,2 @@
 def calculate_total(cart):
-    return cart.subtotal
+    return cart.subtotal - cart.discount
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            checkout = root / "src" / "checkout.py"
            checkout.parent.mkdir(parents=True)
            checkout.write_text(
                "from src.pricing import calculate_total\n\n"
                "def checkout(cart):\n"
                "    return charge(calculate_total(cart))\n",
                encoding="utf-8-sig",
            )
            test_file = root / "tests" / "test_checkout.py"
            test_file.parent.mkdir()
            test_file.write_text("calculate_total(cart)\n", encoding="utf-8")
            metadata = self.review.PullRequestMetadata(title="repo scan fixture")
            review = self.review.build_review(metadata, diff, 120_000, repo_root=root)
        by_code = {finding.code: finding for finding in review.findings}
        finding = by_code["DEPENDENT_USAGE_OUTSIDE_DIFF"]
        self.assertEqual(finding.location, "src/checkout.py:4")
        self.assertNotIn("tests/test_checkout.py", finding.evidence)

    def test_js_method_dependency_detection(self):
        diff = """diff --git a/src/cart.ts b/src/cart.ts
index 1111111..2222222 100644
--- a/src/cart.ts
+++ b/src/cart.ts
@@ -1,5 +1,5 @@
 export class Cart {
   calculateTotal(items) {
-    return subtotal(items)
+    return subtotal(items) - discount(items)
   }
 }
diff --git a/src/checkout.ts b/src/checkout.ts
index 3333333..4444444 100644
--- a/src/checkout.ts
+++ b/src/checkout.ts
@@ -1,3 +1,4 @@
 export function checkout(cart, items) {
+  const total = cart.calculateTotal(items)
   return charge(cart)
 }
"""
        metadata = self.review.PullRequestMetadata(title="js dependency fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        by_code = {finding.code: finding for finding in review.findings}
        self.assertEqual(by_code["DEPENDENT_USAGE_UNTESTED"].location, "src/checkout.ts:2")
        self.assertIn("calculateTotal", by_code["DEPENDENT_USAGE_UNTESTED"].message)

    def test_unrelated_test_change_does_not_hide_symbol_risk(self):
        diff = """diff --git a/src/pricing.py b/src/pricing.py
index 1111111..2222222 100644
--- a/src/pricing.py
+++ b/src/pricing.py
@@ -1,2 +1,2 @@
 def calculate_total(cart):
-    return cart.subtotal
+    return cart.subtotal - cart.discount
diff --git a/tests/test_health.py b/tests/test_health.py
index 3333333..4444444 100644
--- a/tests/test_health.py
+++ b/tests/test_health.py
@@ -1,2 +1,5 @@
 def test_health():
     assert True
+
+def test_smoke():
+    assert 1 == 1
"""
        metadata = self.review.PullRequestMetadata(title="unrelated test fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        by_code = {finding.code: finding for finding in review.findings}
        finding = by_code["CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST"]
        self.assertEqual(finding.location, "src/pricing.py:1")
        self.assertIn("calculate_total", finding.message)
        self.assertEqual(review.confidence, "Medium")

    def test_new_file_symbols_do_not_flood_test_relevance(self):
        diff = """diff --git a/src/new_feature.py b/src/new_feature.py
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/src/new_feature.py
@@ -0,0 +1,7 @@
+def parse_input(value):
+    return value.strip()
+
+def normalize_input(value):
+    return parse_input(value).lower()
diff --git a/tests/test_smoke.py b/tests/test_smoke.py
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/tests/test_smoke.py
@@ -0,0 +1,2 @@
+def test_smoke():
+    assert True
"""
        metadata = self.review.PullRequestMetadata(title="new feature fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        codes = {finding.code for finding in review.findings}
        self.assertNotIn("CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST", codes)
        self.assertIn("src/new_feature.py", review.stats.new_files)

    def test_workflow_shell_variables_are_not_dependency_symbols(self):
        diff = """diff --git a/.github/workflows/build.yml b/.github/workflows/build.yml
index 1111111..2222222 100644
--- a/.github/workflows/build.yml
+++ b/.github/workflows/build.yml
@@ -1,3 +1,5 @@
 name: Build
+run: |
+  MISSING=()
diff --git a/tests/test_smoke.py b/tests/test_smoke.py
index 3333333..4444444 100644
--- a/tests/test_smoke.py
+++ b/tests/test_smoke.py
@@ -1 +1,2 @@
 def test_smoke():
+    assert True
"""
        metadata = self.review.PullRequestMetadata(title="workflow fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        codes = {finding.code for finding in review.findings}
        self.assertNotIn("CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST", codes)

    def test_fixture_sample_and_docs_paths_do_not_emit_runtime_risks(self):
        diff = """diff --git a/agents/pr-reviewer/tests/fixtures/security.diff b/agents/pr-reviewer/tests/fixtures/security.diff
new file mode 100644
index 0000000..1111111
--- /dev/null
+++ b/agents/pr-reviewer/tests/fixtures/security.diff
@@ -0,0 +1,4 @@
++API_KEY = "not-a-real-secret"
++subprocess.run(user_input, shell=True)
++DELETE FROM users;
++TODO: exercise detector
diff --git a/agents/pr-reviewer/samples/report.md b/agents/pr-reviewer/samples/report.md
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/agents/pr-reviewer/samples/report.md
@@ -0,0 +1,2 @@
+- [High][FORCE_DELETE] sample.py:1 - Evidence: `rm -rf /tmp/work`
+- [High][SHELL_TRUE] sample.py:2 - Evidence: `shell=True`
diff --git a/agents/pr-reviewer/SUBMISSION.md b/agents/pr-reviewer/SUBMISSION.md
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/agents/pr-reviewer/SUBMISSION.md
@@ -0,0 +1,2 @@
+- External LLM commands run without `shell=True`.
+- The sample fixture includes TODO text for expected output checks.
diff --git a/agents/pr-reviewer/tests/test_claude_review.py b/agents/pr-reviewer/tests/test_claude_review.py
new file mode 100644
index 0000000..4444444
--- /dev/null
+++ b/agents/pr-reviewer/tests/test_claude_review.py
@@ -0,0 +1,4 @@
+DANGEROUS_FIXTURE = "rm -rf /tmp/work"
+SHELL_FIXTURE = "shell=True"
+TODO_FIXTURE = "TODO: test detector"
+SECRET_FIXTURE = "API_KEY = 'not-a-real-secret'"
"""
        metadata = self.review.PullRequestMetadata(title="noise path fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        codes = {finding.code for finding in review.findings}
        self.assertFalse(
            {"SECRET_LITERAL", "SQL_DELETE_WITHOUT_WHERE", "SHELL_TRUE", "FORCE_DELETE", "TODO_IN_CHANGE"} & codes
        )

    def test_rule_description_strings_do_not_emit_runtime_risks(self):
        diff = """diff --git a/src/rules.py b/src/rules.py
index 1111111..2222222 100644
--- a/src/rules.py
+++ b/src/rules.py
@@ -1 +1,8 @@
 RULES = {
+    "shell": "A subprocess call enables shell=True.",
+    "todo": "New TODO/FIXME marker indicates incomplete follow-up work.",
+    "pattern": r"subprocess\\.[a-z_]+\\([^\\n]*shell=True",
+    "risk": f"{path} calls subprocess with `shell=True`; pass argv lists.",
+    "delete": f"{path} includes `rm -rf`; validate the target path.",
+    "safe": "pass",
 }
"""
        metadata = self.review.PullRequestMetadata(title="rule text fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        codes = {finding.code for finding in review.findings}
        self.assertNotIn("SHELL_TRUE", codes)
        self.assertNotIn("TODO_IN_CHANGE", codes)
        self.assertNotIn("FORCE_DELETE", codes)

    def test_safe_fixture_can_be_high_confidence(self):
        diff = (FIXTURES / "safe_with_tests.diff").read_text(encoding="utf-8")
        metadata = self.review.PullRequestMetadata(title="safe fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        self.assertEqual(review.confidence, "High")
        self.assertTrue(review.stats.tests_touched)
        self.assertNotIn("Add or update focused tests", " ".join(review.suggestions))

    def test_json_output_has_contract_keys(self):
        output = self.run_cli(
            "--diff-file",
            str(FIXTURES / "safe_with_tests.diff"),
            "--format",
            "json",
        )
        payload = json.loads(output)
        self.assertEqual(
            sorted(payload.keys()),
            ["confidence", "findings", "metadata", "risks", "suggestions", "summary"],
        )
        self.assertIn(payload["confidence"], {"Low", "Medium", "High"})
        self.assertIsInstance(payload["findings"], list)

    def test_sarif_output_contains_rules_and_locations(self):
        output = self.run_cli(
            "--diff-file",
            str(FIXTURES / "dependency_impact.diff"),
            "--format",
            "sarif",
        )
        payload = json.loads(output)
        self.assertEqual(payload["version"], "2.1.0")
        result = payload["runs"][0]["results"][1]
        self.assertEqual(result["ruleId"], "DEPENDENT_USAGE_UNTESTED")
        self.assertEqual(
            result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
            "src/checkout.py",
        )

    def test_config_can_disable_rules_ignore_paths_and_override_severity(self):
        diff = (FIXTURES / "security.diff").read_text(encoding="utf-8")
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".yml", delete=False) as tmp:
            tmp.write(
                "\ufeffdisabled_rules:\n"
                "  - NO_TEST_CHANGES\n"
                "ignored_paths:\n"
                "  - db/**\n"
                "severity_overrides:\n"
                "  SECRET_LITERAL: Medium\n"
            )
            config_path = tmp.name
        try:
            config = self.review.load_review_config(config_path)
            metadata = self.review.PullRequestMetadata(title="security fixture")
            review = self.review.build_review(metadata, diff, 120_000, config=config)
        finally:
            Path(config_path).unlink(missing_ok=True)
        by_code = {finding.code: finding for finding in review.findings}
        self.assertNotIn("NO_TEST_CHANGES", by_code)
        self.assertNotIn("SQL_DELETE_WITHOUT_WHERE", by_code)
        self.assertNotIn("DB_SCHEMA_CHANGE", by_code)
        self.assertEqual(by_code["SECRET_LITERAL"].severity, "Medium")

    def test_github_annotations_render_located_findings(self):
        diff = (FIXTURES / "dependency_impact.diff").read_text(encoding="utf-8")
        metadata = self.review.PullRequestMetadata(title="dependency fixture")
        review = self.review.build_review(metadata, diff, 120_000)
        annotations = self.review.render_github_annotations(review)
        self.assertIn("::warning file=src/checkout.py,title=Medium DEPENDENT_USAGE_UNTESTED,line=4::", annotations)
        self.assertNotIn("NO_TEST_CHANGES", annotations)

    def test_step_summary_appends_markdown(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            summary_path = tmp.name
        try:
            self.review.append_step_summary(summary_path, "## First")
            self.review.append_step_summary(summary_path, "## Second")
            written = Path(summary_path).read_text(encoding="utf-8")
            self.assertIn("## First\n## Second\n", written)
        finally:
            Path(summary_path).unlink(missing_ok=True)

    def test_fail_on_severity_returns_nonzero_after_output(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--diff-file",
                str(FIXTURES / "security.diff"),
                "--fail-on",
                "High",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("### Identified Risks", completed.stdout)
        self.assertIn("SHELL_TRUE", completed.stdout)
        self.assertIn("met --fail-on High", completed.stderr)

    def test_fail_on_severity_is_thresholded(self):
        safe_diff = (FIXTURES / "safe_with_tests.diff").read_text(encoding="utf-8")
        security_diff = (FIXTURES / "security.diff").read_text(encoding="utf-8")
        safe_review = self.review.build_review(self.review.PullRequestMetadata(title="safe"), safe_diff, 120_000)
        security_review = self.review.build_review(
            self.review.PullRequestMetadata(title="security"), security_diff, 120_000
        )
        self.assertFalse(self.review.should_fail_review(safe_review, "Low"))
        self.assertTrue(self.review.should_fail_review(security_review, "High"))
        self.assertTrue(self.review.should_fail_review(security_review, "Medium"))

    def test_comment_failure_can_be_non_blocking(self):
        original_post_comment = self.review.post_comment
        original_load_inputs = self.review.load_inputs

        def fail_post_comment(*_args, **_kwargs):
            raise self.review.ReviewError("simulated comment failure")

        def fixture_inputs(_args):
            return (
                self.review.PullRequestMetadata(
                    url="https://github.com/owner/repo/pull/1",
                    title="fixture",
                ),
                (FIXTURES / "safe_with_tests.diff").read_text(encoding="utf-8"),
            )

        self.review.post_comment = fail_post_comment
        self.review.load_inputs = fixture_inputs
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                code = self.review.main(
                    [
                        "--pr",
                        "https://github.com/owner/repo/pull/1",
                        "--update-comment",
                        "--allow-comment-failure",
                    ]
                )
            self.assertEqual(code, 0)
        finally:
            self.review.post_comment = original_post_comment
            self.review.load_inputs = original_load_inputs

    def test_prompt_only_returns_external_llm_prompt(self):
        output = self.run_cli(
            "--diff-file",
            str(FIXTURES / "safe_with_tests.diff"),
            "--prompt-only",
        )
        self.assertIn("Return only a JSON object", output)
        self.assertIn('"confidence"', output)
        self.assertIn("```diff", output)

    def test_llm_command_backend_parses_json_response(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".py", delete=False) as tmp:
            tmp.write(
                "import json, sys\n"
                "sys.stdin.read()\n"
                "print(json.dumps({"
                "'summary': 'This is sentence one. This is sentence two.', "
                "'risks': ['LLM risk'], "
                "'suggestions': ['LLM suggestion'], "
                "'confidence': 'High'"
                "}))\n"
            )
            command_path = tmp.name
        try:
            diff = (FIXTURES / "security.diff").read_text(encoding="utf-8")
            metadata = self.review.PullRequestMetadata(title="security fixture")
            review = self.review.build_llm_review(
                metadata,
                diff,
                120_000,
                f'"{sys.executable}" "{command_path}"',
            )
            self.review.validate_review(review)
            self.assertEqual(review.risks[0], "LLM risk")
            self.assertEqual(review.confidence, "Medium")
            self.assertIn("SECRET_LITERAL", " ".join(review.risks))
            self.assertIn("SECRET_LITERAL", {finding.code for finding in review.findings})
        finally:
            Path(command_path).unlink(missing_ok=True)

    def test_pr_url_parser_rejects_non_pr_url(self):
        with self.assertRaises(self.review.ReviewError):
            self.review.parse_pr_url("https://github.com/owner/repo/issues/123")

    def test_pr_parser_accepts_owner_repo_number_shorthand(self):
        ref = self.review.parse_pr_url("owner/repo#123")
        self.assertEqual(ref.slug, "owner/repo")
        self.assertEqual(ref.number, 123)
        self.assertEqual(ref.url, "https://github.com/owner/repo/pull/123")

    def test_post_comment_validation_happens_before_output(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--diff-file",
                str(FIXTURES / "safe_with_tests.diff"),
                "--post-comment",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--post-comment requires --pr", completed.stderr)

    def test_diff_paths_with_spaces_are_preserved(self):
        diff = """diff --git a/old name.txt b/new name.txt
similarity index 80%
rename from old name.txt
rename to new name.txt
--- a/old name.txt
+++ b/new name.txt
@@ -1 +1 @@
-old
+new
diff --git a/src/one.py b/src/one.py
--- a/src/one.py
+++ b/src/one.py
@@ -1 +1 @@
-x = 1
+x = 2
"""
        stats = self.review.parse_diff(diff)
        self.assertEqual(stats.files, ["new name.txt", "src/one.py"])
        self.assertEqual(stats.changed_files, 2)
        self.assertEqual(
            self.review.normalize_repo_relative_path(".github/workflows/review.yml"),
            ".github/workflows/review.yml",
        )
        self.assertEqual(self.review.normalize_repo_relative_path("./.env"), ".env")

    def test_empty_diff_is_rejected_without_stdout(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), "--diff-file", tmp_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("Diff is empty", completed.stderr)

    def test_tiny_max_diff_chars_is_rejected(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--diff-file",
                str(FIXTURES / "safe_with_tests.diff"),
                "--max-diff-chars",
                "0",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--max-diff-chars must be at least", completed.stderr)

    def test_validate_review_rejects_invalid_confidence(self):
        review = self.review.Review(
            summary="This is sentence one. This is sentence two.",
            risks=["risk"],
            suggestions=["suggestion"],
            confidence="Certain",
            metadata=self.review.PullRequestMetadata(),
            stats=self.review.DiffStats(),
        )
        with self.assertRaises(self.review.ReviewError):
            self.review.validate_review(review)

    def test_comment_body_adds_marker_once(self):
        body = "## Claude Code PR Review\n"
        marked = self.review.comment_body(body)
        self.assertIn(self.review.REVIEW_MARKER, marked)
        self.assertEqual(self.review.comment_body(marked).count(self.review.REVIEW_MARKER), 1)


if __name__ == "__main__":
    unittest.main()
