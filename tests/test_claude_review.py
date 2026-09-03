import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
from pathlib import Path


def load_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "agents" / "pr-reviewer" / "claude_review.py"
    spec = importlib.util.spec_from_file_location("claude_review", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


claude_review = load_module()


class ClaudeReviewTest(unittest.TestCase):
    def test_parses_and_categorizes_risks(self):
        diff = textwrap.dedent(
            """\
            diff --git a/app/auth.py b/app/auth.py
            index 1111111..2222222 100644
            --- a/app/auth.py
            +++ b/app/auth.py
            @@ -1,2 +1,3 @@
             def run(value):
            +    eval(value)
                 return True
            diff --git a/tests/test_auth.py b/tests/test_auth.py
            index 3333333..4444444 100644
            --- a/tests/test_auth.py
            +++ b/tests/test_auth.py
            @@ -0,0 +1,2 @@
            +def test_run():
            +    assert True
            """
        )

        analysis = claude_review.analyze_diff(diff)
        rendered = claude_review.render_markdown(analysis, pr_url="https://github.com/o/r/pull/1")

        self.assertEqual(len(analysis.files), 2)
        self.assertIn("Shell execution", "\n".join(analysis.risks))
        self.assertIn("security-sensitive", "\n".join(analysis.risks))
        self.assertIn("Confidence score: Medium", rendered)
        self.assertIn("https://github.com/o/r/pull/1", rendered)

    def test_pr_url_validation(self):
        self.assertEqual(
            claude_review.pr_to_diff_url("https://github.com/owner/repo/pull/123"),
            "https://github.com/owner/repo/pull/123.diff",
        )
        self.assertEqual(
            claude_review.pr_to_api_diff_url("https://github.com/owner/repo/pull/123"),
            "https://api.github.com/repos/owner/repo/pulls/123",
        )
        self.assertEqual(
            claude_review.pr_to_issue_comments_url("https://github.com/owner/repo/pull/123"),
            "https://api.github.com/repos/owner/repo/issues/123/comments",
        )
        with self.assertRaises(ValueError):
            claude_review.pr_to_diff_url("https://example.com/not-a-pr")

    def test_build_diff_request_uses_api_accept_and_optional_token(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            request = claude_review.build_diff_request("https://github.com/owner/repo/pull/123")

        self.assertEqual(request.full_url, "https://api.github.com/repos/owner/repo/pulls/123")
        self.assertEqual(request.get_header("Accept"), "application/vnd.github.v3.diff")
        self.assertEqual(request.get_header("User-agent"), "claude-review-agent")
        self.assertIsNone(request.get_header("Authorization"))

        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "ghs_example"}, clear=True):
            authed_request = claude_review.build_diff_request("https://github.com/owner/repo/pull/123")

        self.assertEqual(authed_request.get_header("Authorization"), "Bearer ghs_example")

        with mock.patch.dict("os.environ", {"GH_TOKEN": "ghs_fallback"}, clear=True):
            fallback_request = claude_review.build_diff_request("https://github.com/owner/repo/pull/123")

        self.assertEqual(fallback_request.get_header("Authorization"), "Bearer ghs_fallback")

    def test_post_comment_requires_token(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "requires GITHUB_TOKEN or GH_TOKEN"):
                claude_review.post_pr_comment("https://github.com/owner/repo/pull/123", "review")

    def test_post_comment_uses_issue_comments_api(self):
        class DummyResponse:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return b'{"id": 1}'

        with mock.patch.dict("os.environ", {"GH_TOKEN": "ghs_example"}, clear=True):
            with mock.patch("urllib.request.urlopen", return_value=DummyResponse()) as urlopen:
                claude_review.post_pr_comment("https://github.com/owner/repo/pull/123", "review body")

        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/owner/repo/issues/123/comments")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Accept"), "application/vnd.github+json")
        self.assertEqual(request.get_header("Authorization"), "Bearer ghs_example")
        self.assertEqual(json.loads(request.data.decode("utf-8")), {"body": "review body"})

    def test_detects_common_review_hazards(self):
        diff = textwrap.dedent(
            """\
            diff --git a/web/app.js b/web/app.js
            index 1111111..2222222 100644
            --- a/web/app.js
            +++ b/web/app.js
            @@ -1,2 +1,8 @@
             export function render(value) {
            +  document.body.innerHTML = value
            +  const endpoint = "http://api.example.com"
            +  const devOnly = "http://localhost:3000"
            +  const key = "-----BEGIN OPENSSH PRIVATE KEY-----"
            +  try { risky() } catch (err) {}
            +  console.log(endpoint)
             }
            """
        )

        risks = "\n".join(claude_review.analyze_diff(diff).risks)

        self.assertIn("DOM injection", risks)
        self.assertIn("Plain HTTP URL", risks)
        self.assertIn("Private key material", risks)
        self.assertIn("Silent exception handler", risks)
        self.assertIn("Debug output", risks)
        self.assertNotIn("localhost:3000", risks)

    def test_detects_destructive_rm_flag_permutations(self):
        diff = textwrap.dedent(
            """\
            diff --git a/scripts/cleanup.sh b/scripts/cleanup.sh
            index 1111111..2222222 100755
            --- a/scripts/cleanup.sh
            +++ b/scripts/cleanup.sh
            @@ -1,2 +1,5 @@
             #!/usr/bin/env bash
            +rm -fr build
            +rm -r -f dist
            +rm --recursive --force cache
            +rm -f --recursive tmp
            """
        )
        risks = "\n".join(claude_review.analyze_diff(diff).risks)

        self.assertIn("rm -fr build", risks)
        self.assertIn("rm -r -f dist", risks)
        self.assertIn("rm --recursive --force cache", risks)
        self.assertIn("rm -f --recursive tmp", risks)

        safer_diff = textwrap.dedent(
            """\
            diff --git a/scripts/cleanup.sh b/scripts/cleanup.sh
            index 1111111..2222222 100755
            --- a/scripts/cleanup.sh
            +++ b/scripts/cleanup.sh
            @@ -1,2 +1,4 @@
             #!/usr/bin/env bash
            +rm -r build
            +rm -f stale.log
            """
        )

        safer_risks = "\n".join(claude_review.analyze_diff(safer_diff).risks)
        self.assertNotIn("Destructive command", safer_risks)

    def test_large_diffs_are_truncated_with_low_confidence(self):
        diff = textwrap.dedent(
            """\
            diff --git a/app/large.py b/app/large.py
            index 1111111..2222222 100644
            --- a/app/large.py
            +++ b/app/large.py
            @@ -0,0 +1,2 @@
            +def changed():
            +    return True
            """
        )
        diff += "+padding\n" * ((claude_review.MAX_DIFF_CHARS // len("+padding\n")) + 10)

        analysis = claude_review.analyze_diff(diff)
        rendered = claude_review.render_markdown(analysis)

        self.assertTrue(analysis.truncated)
        self.assertEqual(analysis.analyzed_chars, claude_review.MAX_DIFF_CHARS)
        self.assertEqual(analysis.confidence, "Low")
        self.assertIn("Diff was truncated", "\n".join(analysis.risks))
        self.assertIn("Only the first 120,000", rendered)
        self.assertIn("Confidence score: Low", rendered)

    def test_detects_privileged_workflow_changes(self):
        diff = textwrap.dedent(
            """\
            diff --git a/.github/workflows/review.yml b/.github/workflows/review.yml
            index 1111111..2222222 100644
            --- a/.github/workflows/review.yml
            +++ b/.github/workflows/review.yml
            @@ -1,5 +1,10 @@
             name: Review
             on:
            +  pull_request_target:
            +permissions: write-all
            +id-token: write
            +pull-requests: write
             jobs:
               review:
                 runs-on: ubuntu-latest
            """
        )

        analysis = claude_review.analyze_diff(diff)
        risks = "\n".join(analysis.risks)
        suggestions = "\n".join(analysis.suggestions)

        self.assertIn("Privileged workflow trigger", risks)
        self.assertIn("Broad workflow permission", risks)
        self.assertIn("CI workflow changed", risks)
        self.assertIn("Pin workflow permissions", suggestions)

    def test_cli_reads_local_diff_alias(self):
        diff = textwrap.dedent(
            """\
            diff --git a/README.md b/README.md
            index 1111111..2222222 100644
            --- a/README.md
            +++ b/README.md
            @@ -1 +1,2 @@
             # Project
            +Add setup notes.
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            diff_path = Path(tmpdir) / "change.diff"
            diff_path.write_text(diff, encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = claude_review.main(["--diff", str(diff_path)])

        self.assertEqual(exit_code, 0)
        rendered = stdout.getvalue()
        self.assertIn("### Summary of changes", rendered)
        self.assertIn("README.md", rendered)
        self.assertNotIn("_Reviewed PR:", rendered)

    def test_cli_writes_output_file(self):
        diff = textwrap.dedent(
            """\
            diff --git a/docs/usage.md b/docs/usage.md
            index 1111111..2222222 100644
            --- a/docs/usage.md
            +++ b/docs/usage.md
            @@ -1 +1,2 @@
             # Usage
            +Add reviewer output instructions.
            """
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            diff_path = tmp / "change.diff"
            output_path = tmp / "review.md"
            diff_path.write_text(diff, encoding="utf-8")
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = claude_review.main(["--diff", str(diff_path), "--output", str(output_path)])

            rendered = output_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("### Summary of changes", rendered)
        self.assertIn("docs/usage.md", rendered)
        self.assertNotIn("_Reviewed PR:", rendered)

    def test_sample_outputs_keep_required_review_structure(self):
        samples = Path(__file__).resolve().parents[1] / "agents" / "pr-reviewer" / "samples"
        sample_outputs = sorted(samples.glob("*.md"))

        self.assertGreaterEqual(len(sample_outputs), 2)
        for sample_output in sample_outputs:
            rendered = sample_output.read_text(encoding="utf-8")
            self.assertIn("### Summary of changes", rendered)
            self.assertIn("### Identified risks", rendered)
            self.assertIn("### Improvement suggestions", rendered)
            self.assertRegex(rendered, r"### Confidence score: (Low|Medium|High)")
            self.assertIn("_Reviewed PR: https://github.com/", rendered)

    def test_action_commenter_reuses_cli_output(self):
        root = Path(__file__).resolve().parents[1]
        workflow = root / ".github" / "workflows" / "claude-review-comment.yml"
        contents = workflow.read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", contents)
        self.assertIn("pull-requests: write", contents)
        self.assertIn("issues: write", contents)
        self.assertIn("GITHUB_TOKEN: ${{ github.token }}", contents)
        self.assertIn('python3 agents/pr-reviewer/claude_review.py --pr "$PR_URL" --output review.md', contents)
        self.assertIn("--post-comment", contents)
        self.assertIn("workflow token can only comment on PRs in this repository", contents)
        self.assertIn("          import re\n          import sys", contents)

        ci_workflow = root / ".github" / "workflows" / "pr-reviewer.yml"
        ci_contents = ci_workflow.read_text(encoding="utf-8")
        self.assertGreaterEqual(ci_contents.count(".github/workflows/claude-review-comment.yml"), 2)


if __name__ == "__main__":
    unittest.main()
