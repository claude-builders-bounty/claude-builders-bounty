"""Offline tests: no personal credentials, network calls, or paid model calls."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch

import claude_review as cr

URL = "https://github.com/acme/project/pull/7"
DIFF = """diff --git a/app.py b/app.py
index 1234567..2345678 100644
--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-answer = 1
+answer = 2
"""
INFO = {
    "number": 7, "html_url": URL, "title": "Change the answer", "body": "A small fix.",
    "head": {"sha": "a" * 40, "ref": "fix"}, "base": {"sha": "b" * 40, "ref": "main"},
    "changed_files": 1, "additions": 1, "deletions": 1,
}
DATA = {"summary": ["This changes the answer returned by the helper.",
                    "The existing assignment is replaced with a new value."],
        "risks": ["app.py:1 changes observable behavior."],
        "suggestions": ["Add a regression test for the expected value."], "confidence": "Medium"}


def snapshot() -> cr.Snapshot:
    return cr.Snapshot.from_data(cr.parse_pr_url(URL), {"metadata": copy.deepcopy(INFO), "diff": DIFF})


def request() -> dict:
    return cr.make_request(snapshot())


class Response(io.BytesIO):
    pass


class FakeHTTP:
    def __init__(self, results):
        self.results = list(results)
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result if isinstance(result, str) else json.dumps(result)


class TestURL(unittest.TestCase):
    def test_canonical(self):
        pr = cr.parse_pr_url(URL)
        self.assertEqual((pr.owner, pr.repo, pr.number), ("acme", "project", 7))
        self.assertEqual(pr.api, "https://api.github.com/repos/acme/project/pulls/7")

    def test_anchor_query_and_trailing_slash(self):
        self.assertEqual(cr.parse_pr_url(URL + "/?tab=files#discussion").url, URL)

    def test_outer_spaces_and_case_insensitive_host(self):
        self.assertEqual(cr.parse_pr_url("  " + URL.replace("github.com", "GITHUB.COM") + " ").url, URL)

    def test_repository_dots_and_underscores(self):
        self.assertEqual(cr.parse_pr_url("https://github.com/acme/a.b_c/pull/12").repo, "a.b_c")


INVALID_URLS = [
    "", "github.com/acme/project/pull/7", "http://github.com/acme/project/pull/7",
    "https://github.com.evil.test/acme/project/pull/7", "https://gitlab.com/acme/project/pull/7",
    "https://user:secret@github.com/acme/project/pull/7", "https://github.com:443/acme/project/pull/7",
    "https://github.com/acme/project/issues/7", "https://github.com/acme/project/pull/0",
    "https://github.com/acme/project/pull/-1", "https://github.com/acme/project/pull/01",
    "https://github.com/acme/project/pull/seven", "https://github.com/acme/project/pull/7/files",
    "https://github.com/acme/../pull/7", "https://github.com/acme/./pull/7",
    "https://github.com/acme/%2fetc/pull/7", "https://github.com/acme/project/pull/7\n",
    "https://github.com/acme/project/pull/7\x1b", "https://github.com/ácme/project/pull/7",
    "https://github.com/acme\\evil/project/pull/7", "https://[bad/acme/project/pull/7",
    "https://github.com/acme/project/pull/1000000000", None,
]
for idx, value in enumerate(INVALID_URLS):
    def invalid_test(self, value=value):
        with self.assertRaises(cr.ReviewError) as error:
            cr.parse_pr_url(value)
        self.assertEqual(error.exception.code, 2)
        self.assertNotIn("secret", str(error.exception))
    setattr(TestURL, f"test_invalid_{idx:02d}", invalid_test)


class TestData(unittest.TestCase):
    def test_snapshot_roundtrip(self):
        saved = snapshot()
        self.assertEqual(cr.Snapshot.from_data(saved.pr, saved.to_data()), saved)


    def test_hunk_accounting(self):
        self.assertEqual(cr.validate_diff(DIFF), (1, 1, 1))
        self.assertEqual(cr.validate_diff(DIFF + "\\ No newline at end of file\n"), (1, 1, 1))
        with_context = DIFF.replace("@@ -1 +1 @@", "@@ -1,2 +1,2 @@") + " unchanged\n"
        self.assertEqual(cr.validate_diff(with_context), (1, 1, 1))

    def test_hunk_truncation_and_malformed_counts(self):
        bad = [DIFF.replace("+answer = 2\n", ""), DIFF.replace("+answer = 2", "-answer = 2"),
               DIFF.replace("+answer = 2", "unexpected"), DIFF.replace("@@ -1 +1 @@", "@@ bad @@"),
               DIFF.replace("+answer = 2\n", "diff --git a/b b/b\n"),
               DIFF.replace("+answer = 2\n", "@@ -2 +2 @@\n")]
        for diff in bad:
            with self.subTest(diff=diff), self.assertRaises(cr.ReviewError):
                cr.validate_diff(diff)

    def test_snapshot_stat_mismatch(self):
        with self.assertRaisesRegex(cr.ReviewError, "line statistics"):
            cr.Snapshot.from_data(cr.parse_pr_url(URL), {"metadata": {**INFO, "additions": 9}, "diff": DIFF})

    def test_non_integer_stat_rejected(self):
        with self.assertRaises(cr.ReviewError):
            cr.metadata({**INFO, "additions": True}, cr.parse_pr_url(URL))

    def test_optional_description(self):
        value = copy.deepcopy(INFO)
        value["body"] = None
        self.assertEqual(cr.metadata(value, cr.parse_pr_url(URL))["body"], "")

    def test_invalid_metadata(self):
        cases = [({}, "empty"), ({**INFO, "number": True}, "bool"),
                 ({**INFO, "number": 8}, "number"), ({**INFO, "html_url": URL + "9"}, "url"),
                 ({**INFO, "title": ""}, "title"), ({**INFO, "body": []}, "body"),
                 ({**INFO, "head": {"sha": "no", "ref": "fix"}}, "sha"),
                 ({**INFO, "head": {"sha": "a" * 40, "ref": 3}}, "ref"),
                 ({**INFO, "additions": -1}, "negative")]
        for info, label in cases:
            with self.subTest(label=label), self.assertRaises(cr.ReviewError) as error:
                cr.metadata(info, cr.parse_pr_url(URL))
            self.assertEqual(error.exception.code, 3)

    def test_diff_must_be_complete(self):
        for diff in ("not a diff", None, "\x00" + DIFF, DIFF + DIFF):
            with self.subTest(diff=diff), self.assertRaises(cr.ReviewError):
                cr.Snapshot.from_data(cr.parse_pr_url(URL), {"metadata": INFO, "diff": diff})

    def test_no_changes(self):
        with self.assertRaisesRegex(cr.ReviewError, "no reviewable"):
            cr.Snapshot.from_data(cr.parse_pr_url(URL),
                                 {"metadata": {**INFO, "changed_files": 0, "additions": 0, "deletions": 0}, "diff": ""})

    def test_request_deterministic_and_bound_to_revision(self):
        self.assertEqual(request(), request())
        other = snapshot().to_data()
        other["metadata"]["head"]["sha"] = "c" * 40
        revised = cr.make_request(cr.Snapshot.from_data(cr.parse_pr_url(URL), other))
        self.assertNotEqual(request()["request_sha256"], revised["request_sha256"])
        self.assertEqual(request()["context"]["diff_sha256"], cr.digest(DIFF))

    def test_large_diff_rejected_by_default(self):
        with self.assertRaisesRegex(cr.ReviewError, "exceeds"):
            cr.make_request(snapshot(), max_diff=20)

    def test_utf8_truncation(self):
        original = cr.Snapshot(snapshot().pr, copy.deepcopy(INFO), DIFF + "😀" * 10)
        result = cr.make_request(original, max_diff=len(DIFF.encode()) + 2, allow_truncation=True)
        self.assertEqual(result["context"]["diff"], DIFF)
        self.assertTrue(result["context"]["diff_truncated"])
        self.assertEqual(result["context"]["diff_bytes_total"], len(DIFF.encode()) + 40)

    def test_metadata_truncation_disclosed(self):
        original = cr.Snapshot(snapshot().pr, {**INFO, "body": "x" * 12_001, "title": "x" * 1_001}, DIFF)
        result = cr.make_request(original)
        self.assertTrue(result["context"]["description_truncated"])
        self.assertTrue(result["context"]["title_truncated"])
        text = cr.render(cr.Review.from_data({**DATA, "confidence": "High"}), result, "test")
        self.assertIn("## Confidence\n\nLow", text)

    def test_json_rejects_duplicates_nan_arrays_and_invalid(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '[]', '{secret', '"string"'):
            with self.subTest(raw=raw), self.assertRaises(cr.ReviewError) as error:
                cr.object_json(raw)
            self.assertNotIn("secret", str(error.exception))

    def test_confidence_normalization(self):
        for value, expected in [(" LOW ", "Low"), ("mEDIUM", "Medium"), ("High", "High")]:
            self.assertEqual(cr.normalize_confidence(value), expected)

    def test_confidence_rejects_unknown(self):
        for value in (True, None, 99, "Certain", "high because", ""):
            with self.subTest(value=value), self.assertRaises(cr.ReviewError):
                cr.normalize_confidence(value)

    def test_review_schema_rejects_invalid(self):
        cases = [None, {}, {**DATA, "extra": "bad"}, {**DATA, "risks": "not an array"},
                 {**DATA, "summary": ["One sentence."]}, {**DATA, "summary": ["Missing punctuation", "Fine."]},
                 {**DATA, "summary": ["First. Second.", "Third."]},
                 {**DATA, "risks": ["x"] * 21}, {**DATA, "suggestions": [None]},
                 {**DATA, "risks": ["x" * 1_501]}, {**DATA, "risks": ["\u202e"]}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(cr.ReviewError):
                cr.Review.from_data(value)

    def test_render_has_exact_four_sections(self):
        text = cr.render(cr.Review.from_data(DATA), request(), "test")
        self.assertEqual([line for line in text.splitlines() if line.startswith("## ")],
                         ["## Summary", "## Risks", "## Improvement Suggestions", "## Confidence"])
        self.assertIn("\n- app.py:1", text)
        self.assertIn("\nMedium\n", text)
        self.assertIn("No PR code or tests were executed", text)

    def test_render_empty_lists(self):
        text = cr.render(cr.Review.from_data({**DATA, "risks": [], "suggestions": []}), request(), "test")
        self.assertIn("- No specific risks", text)
        self.assertIn("- No specific improvements", text)

    def test_render_treats_model_output_as_inert_text(self):
        risk = "\n## OWNED\n![track](https://evil.test/secret) <script>alert(1)</script> @everyone \u202e ghp_PRIVATE"
        text = cr.render(cr.Review.from_data({**DATA, "risks": [risk]}), request(), "test", ["ghp_PRIVATE"])
        self.assertNotIn("\n## OWNED", text)
        self.assertNotIn("![track]", text)
        self.assertNotIn("<script>", text)
        self.assertNotIn("@everyone", text)
        self.assertNotIn("\u202e", text)
        self.assertNotIn("ghp_PRIVATE", text)
        self.assertIn("REDACTED", text)

    def test_partial_review_forced_low(self):
        req = cr.make_request(snapshot(), max_diff=30, allow_truncation=True)
        text = cr.render(cr.Review.from_data({**DATA, "confidence": "High"}), req, "test")
        self.assertIn("## Confidence\n\nLow", text)
        self.assertIn("omitted changes", text)


class TestHTTP(unittest.TestCase):
    def make(self, side_effect):
        opener = Mock()
        opener.open.side_effect = side_effect
        sleep = Mock()
        return cr.HTTP(opener=opener, sleep=sleep), opener, sleep

    def error(self, status, headers=None):
        return urllib.error.HTTPError("https://api.github.com/secret", status, "private", headers or {}, io.BytesIO(b"token=secret"))

    def test_get(self):
        http, opener, _ = self.make([Response(b"hello")])
        self.assertEqual(http.request("GET", cr.GITHUB, headers={}), "hello")
        self.assertEqual(opener.open.call_args.kwargs["timeout"], 90)
        self.assertEqual(opener.open.call_args.args[0].get_method(), "GET")

    def test_post_json(self):
        http, opener, _ = self.make([Response(b"{}")])
        http.request("POST", cr.ANTHROPIC, headers={}, data={"a": "é"}, service="Anthropic")
        self.assertEqual(json.loads(opener.open.call_args.args[0].data), {"a": "é"})

    def test_large_response_rejected(self):
        http, _, _ = self.make([Response(b"x" * (cr.MAX_RESPONSE + 1))])
        with self.assertRaisesRegex(cr.ReviewError, "safety limit"):
            http.request("GET", cr.GITHUB, headers={})

    def test_invalid_utf8(self):
        http, _, _ = self.make([Response(b"\xff")])
        with self.assertRaisesRegex(cr.ReviewError, "UTF-8"):
            http.request("GET", cr.GITHUB, headers={})

    def test_forbidden_never_leaks_response_or_exception(self):
        http, opener, _ = self.make([self.error(403)])
        with self.assertRaises(cr.ReviewError) as error:
            http.request("GET", cr.GITHUB, headers={"Authorization": "Bearer secret"})
        self.assertEqual(error.exception.code, 3)
        self.assertNotIn("secret", str(error.exception))
        self.assertEqual(opener.open.call_count, 1)

    def test_not_found(self):
        http, _, _ = self.make([self.error(404)])
        with self.assertRaisesRegex(cr.ReviewError, "not found"):
            http.request("GET", cr.GITHUB, headers={})

    def test_unauthorized_anthropic(self):
        http, _, _ = self.make([self.error(401)])
        with self.assertRaises(cr.ReviewError) as error:
            http.request("POST", cr.ANTHROPIC, headers={}, service="Anthropic")
        self.assertEqual(error.exception.code, 4)

    def test_retry_get_503(self):
        http, opener, sleep = self.make([self.error(503), Response(b"ok")])
        self.assertEqual(http.request("GET", cr.GITHUB, headers={}), "ok")
        self.assertEqual(opener.open.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_retry_after(self):
        http, _, sleep = self.make([self.error(429, {"Retry-After": "2"}), Response(b"ok")])
        http.request("GET", cr.GITHUB, headers={})
        sleep.assert_called_once_with(2)

    def test_long_retry_after_fails_without_sleep(self):
        http, _, sleep = self.make([self.error(429, {"Retry-After": "999"})])
        with self.assertRaisesRegex(cr.ReviewError, "Rate limited"):
            http.request("GET", cr.GITHUB, headers={})
        sleep.assert_not_called()

    def test_no_post_retry(self):
        http, opener, sleep = self.make([self.error(503)])
        with self.assertRaises(cr.ReviewError):
            http.request("POST", cr.GITHUB, headers={}, data={"body": "review"})
        self.assertEqual(opener.open.call_count, 1)
        sleep.assert_not_called()

    def test_network_retries_bounded(self):
        http, opener, sleep = self.make([urllib.error.URLError("secret")] * 3)
        with self.assertRaisesRegex(cr.ReviewError, "connection failed") as error:
            http.request("GET", cr.GITHUB, headers={})
        self.assertNotIn("secret", str(error.exception))
        self.assertEqual(opener.open.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_timeout_post_never_retried(self):
        http, opener, _ = self.make([TimeoutError("secret")])
        with self.assertRaises(cr.ReviewError):
            http.request("POST", cr.ANTHROPIC, headers={}, service="Anthropic")
        self.assertEqual(opener.open.call_count, 1)

    def test_destination_allowlist(self):
        for url in ("http://api.github.com", "https://evil.test", "https://api.github.com@evil.test"):
            with self.subTest(url=url), self.assertRaises(cr.ReviewError):
                cr.HTTP().request("GET", url, headers={})

    def test_redirect_handler(self):
        self.assertIsNone(cr.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test"))


class TestGitHub(unittest.TestCase):
    def test_real_fetch_path_contract(self):
        http = FakeHTTP([INFO, DIFF, INFO])
        result = cr.GitHubClient(http).snapshot(cr.parse_pr_url(URL))
        self.assertEqual(result, snapshot())
        self.assertEqual(http.calls[1][2]["headers"]["Accept"], "application/vnd.github.diff")
        self.assertNotIn("Authorization", http.calls[0][2]["headers"])

    def test_fetch_detects_concurrent_head_change(self):
        after = {**INFO, "head": {"sha": "c" * 40, "ref": "fix"}}
        with self.assertRaisesRegex(cr.ReviewError, "changed while fetching"):
            cr.GitHubClient(FakeHTTP([INFO, DIFF, after])).snapshot(cr.parse_pr_url(URL))

    def test_fetch_detects_description_change(self):
        with self.assertRaisesRegex(cr.ReviewError, "changed while fetching"):
            cr.GitHubClient(FakeHTTP([INFO, DIFF, {**INFO, "body": "different"}])).snapshot(cr.parse_pr_url(URL))

    def test_fetch_propagates_errors(self):
        with self.assertRaisesRegex(cr.ReviewError, "HTTP 403"):
            cr.GitHubClient(FakeHTTP([cr.ReviewError("HTTP 403", 3)])).snapshot(cr.parse_pr_url(URL))

    def test_post_comment(self):
        http = FakeHTTP([INFO, {"id": 42}])
        link = cr.GitHubClient(http, "token").post(snapshot(), "Review")
        self.assertEqual(link, URL + "#issuecomment-42")
        self.assertEqual(http.calls[-1][1], "https://api.github.com/repos/acme/project/issues/7/comments")
        self.assertEqual(http.calls[-1][2]["data"], {"body": "Review"})
        self.assertEqual(http.calls[-1][2]["headers"]["Authorization"], "Bearer token")

    def test_post_requires_token(self):
        with self.assertRaisesRegex(cr.ReviewError, "required"):
            cr.GitHubClient(FakeHTTP([])).post(snapshot(), "Review")

    def test_post_rejects_oversized_comment(self):
        with self.assertRaisesRegex(cr.ReviewError, "size limit"):
            cr.GitHubClient(FakeHTTP([]), "token").post(snapshot(), "x" * 60_001)

    def test_post_refuses_stale_review(self):
        for key in ("head", "base"):
            info = {**INFO, key: {"sha": "c" * 40, "ref": "fix"}}
            with self.subTest(key=key), self.assertRaisesRegex(cr.ReviewError, "stale"):
                cr.GitHubClient(FakeHTTP([info]), "token").post(snapshot(), "Review")

    def test_invalid_comment_receipt(self):
        for receipt in ({}, {"id": False}, {"id": -1}):
            with self.subTest(receipt=receipt), self.assertRaisesRegex(cr.ReviewError, "receipt"):
                cr.GitHubClient(FakeHTTP([INFO, receipt]), "token").post(snapshot(), "Review")


class TestModels(unittest.TestCase):
    def test_api_request_and_response(self):
        http = FakeHTTP([{"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "name": "submit_review", "input": DATA}]}])
        self.assertEqual(cr.anthropic_review(request(), http, "sk-ant-unit-test-only-value", "test-model"), cr.Review.from_data(DATA))
        sent = http.calls[0][2]
        self.assertEqual(sent["data"]["tool_choice"], {"type": "tool", "name": "submit_review"})
        self.assertNotIn("sk-ant-unit-test-only-value", json.dumps(sent["data"]))
        self.assertEqual(sent["headers"]["x-api-key"], "sk-ant-unit-test-only-value")

    def test_api_missing_key(self):
        with self.assertRaises(cr.ReviewError) as error:
            cr.anthropic_review(request(), FakeHTTP([]), None, "model")
        self.assertEqual(error.exception.code, 4)

    def test_api_refused_truncated_or_unexpected(self):
        for raw in ({"stop_reason": "max_tokens", "content": []},
                    {"stop_reason": "end_turn", "content": []},
                    {"stop_reason": "tool_use", "content": []},
                    {"stop_reason": "tool_use", "content": [{"type": "tool_use", "name": "Bash"}]},
                    {"stop_reason": "tool_use", "content": "bad"}):
            with self.subTest(raw=raw), self.assertRaises(cr.ReviewError):
                cr.anthropic_review(request(), FakeHTTP([raw]), "key", "model")

    def test_claude_missing_binary(self):
        with self.assertRaisesRegex(cr.ReviewError, "not found"):
            cr.claude_code_review(request(), 90, "sonnet", {}, which=lambda _: None)

    def runner(self, raw=None, exit_code=0):
        def run(args, **kwargs):
            self.assertEqual(args[args.index("--tools") + 1], "")
            self.assertIn("--bare", args)
            self.assertIn("--no-session-persistence", args)
            self.assertIn("--strict-mcp-config", args)
            self.assertEqual(args[args.index("--setting-sources") + 1], "")
            self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
            self.assertNotIn("UNRELATED_SECRET", kwargs["env"])
            self.assertEqual(json.loads(kwargs["input"]), request()["context"])
            self.assertTrue(Path(kwargs["cwd"]).is_dir())
            self.assertFalse(kwargs.get("shell", False))
            content = raw if raw is not None else json.dumps({"subtype": "success", "is_error": False,
                                                             "structured_output": DATA}).encode()
            kwargs["stdout"].write(content)
            kwargs["stderr"].write(b"sensitive raw diagnostics")
            return subprocess.CompletedProcess(args, exit_code)
        return run

    def test_claude_safe_process_contract(self):
        env = {"PATH": "/usr/bin", "HOME": "/tmp", "GITHUB_TOKEN": "private",
               "UNRELATED_SECRET": "private", "ANTHROPIC_API_KEY": "key"}
        result = cr.claude_code_review(request(), 90, "sonnet", env,
                                       run=self.runner(), which=lambda _: "/usr/bin/claude")
        self.assertEqual(result, cr.Review.from_data(DATA))

    def test_claude_nonzero_exit(self):
        with self.assertRaises(cr.ReviewError) as error:
            cr.claude_code_review(request(), 90, "sonnet", {},
                                 run=self.runner(exit_code=1), which=lambda _: "claude")
        self.assertEqual(error.exception.code, 4)
        self.assertNotIn("sensitive", str(error.exception))

    def test_claude_timeout(self):
        with self.assertRaisesRegex(cr.ReviewError, "timed out"):
            cr.claude_code_review(request(), 90, "sonnet", {},
                                 run=Mock(side_effect=subprocess.TimeoutExpired("claude", 90)),
                                 which=lambda _: "claude")

    def test_claude_launch_failure(self):
        with self.assertRaisesRegex(cr.ReviewError, "launch"):
            cr.claude_code_review(request(), 90, "sonnet", {}, run=Mock(side_effect=OSError()),
                                 which=lambda _: "claude")

    def test_claude_invalid_output(self):
        for raw in (b"not json", b"\xff", b"{}", b'{"is_error":true}',
                    b'{"subtype":"error_max_turns"}', b"x" * (cr.MAX_RESPONSE + 1)):
            with self.subTest(raw=raw[:40]), self.assertRaises(cr.ReviewError):
                cr.claude_code_review(request(), 90, "sonnet", {},
                                     run=self.runner(raw=raw), which=lambda _: "claude")


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.snap = self.root / "snapshot.json"
        self.snap.write_text(json.dumps(snapshot().to_data()), encoding="utf-8")
        self.recording = self.root / "response.json"
        self.recording.write_text(json.dumps({"schema_version": 1,
            "request_sha256": request()["request_sha256"], "reviewer": "test model",
            "review": DATA}), encoding="utf-8")

    def invoke(self, args, env=None, http=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cr.main(args, env={} if env is None else env, http=http)
        return code, stdout.getvalue(), stderr.getvalue()

    def replay_args(self):
        return ["--pr", URL, "--snapshot", str(self.snap), "--response-file", str(self.recording)]

    def test_full_cli_replay(self):
        code, output, error = self.invoke(self.replay_args())
        self.assertEqual(code, 0, error)
        self.assertIn("## Improvement Suggestions", output)
        self.assertIn("NOT a live Claude run", output)
        self.assertEqual(error, "")

    def test_export_request_without_credentials(self):
        output = self.root / "request.json"
        code, _, error = self.invoke(["--pr", URL, "--snapshot", str(self.snap),
                                      "--export-request", str(output)])
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output.read_text()), request())

    def test_export_with_output_rejected(self):
        code, _, _ = self.invoke(["--pr", URL, "--export-request", "a", "--output", "b"])
        self.assertEqual(code, 2)

    def test_write_markdown(self):
        target = self.root / "review.md"
        code, output, error = self.invoke(self.replay_args() + ["--output", str(target)])
        self.assertEqual(code, 0, error)
        self.assertEqual(output, "")
        self.assertIn("## Confidence", target.read_text())

    def test_recording_must_match_request(self):
        self.recording.write_text(json.dumps({"schema_version": 1, "request_sha256": "wrong",
                                             "reviewer": "test", "review": DATA}))
        code, _, error = self.invoke(self.replay_args())
        self.assertEqual(code, 5)
        self.assertIn("does not match", error)

    def test_snapshot_cannot_target_different_pr(self):
        args = self.replay_args()
        args[1] = URL + "9"
        self.assertEqual(self.invoke(args)[0], 3)

    def test_snapshot_cannot_be_posted(self):
        self.assertEqual(self.invoke(self.replay_args() + ["--post"], env={"GH_TOKEN": "key"})[0], 2)

    def test_post_without_token_fails_before_fetch(self):
        self.assertEqual(self.invoke(["--pr", URL, "--post"], http=FakeHTTP([]))[0], 2)

    def test_model_validation(self):
        self.assertEqual(self.invoke(["--pr", URL, "--model", "bad model"])[0], 2)

    def test_missing_api_key(self):
        self.assertEqual(self.invoke(["--pr", URL, "--backend", "anthropic"], http=FakeHTTP([]))[0], 4)

    def test_bare_mode_requires_api_key_before_network(self):
        code, _, error = self.invoke(["--pr", URL], http=FakeHTTP([]))
        self.assertEqual(code, 4)
        self.assertIn("does not use subscription login", error)

    def test_credential_newline_redacted(self):
        code, _, error = self.invoke(["--pr", URL], env={"GITHUB_TOKEN": "private\nsecret"})
        self.assertEqual(code, 2)
        self.assertNotIn("private", error)

    def test_credential_fallback(self):
        self.assertEqual(cr.credential({"GH_TOKEN": "fallback"}, "GITHUB_TOKEN", "GH_TOKEN"), "fallback")
        self.assertEqual(cr.credential({"GITHUB_TOKEN": "first", "GH_TOKEN": "second"},
                                       "GITHUB_TOKEN", "GH_TOKEN"), "first")

    def test_live_api_cli_contract_and_post(self):
        http = FakeHTTP([INFO, DIFF, INFO, {"stop_reason": "tool_use", "content": [
            {"type": "tool_use", "name": "submit_review", "input": DATA}]}, INFO, {"id": 55}])
        code, output, error = self.invoke(["--pr", URL, "--backend", "anthropic", "--post"],
                                           env={"ANTHROPIC_API_KEY": "key", "GITHUB_TOKEN": "token"}, http=http)
        self.assertEqual(code, 0, error)
        self.assertIn("Anthropic API", output)
        self.assertIn("#issuecomment-55", error)
        self.assertEqual(len(http.calls), 6)

    def test_live_claude_cli_contract(self):
        with patch.object(cr, "claude_code_review", return_value=cr.Review.from_data(DATA)) as model:
            code, output, error = self.invoke(["--pr", URL], env={"ANTHROPIC_API_KEY": "api-key"}, http=FakeHTTP([INFO, DIFF, INFO]))
        self.assertEqual(code, 0, error)
        self.assertIn("Claude Code", output)
        model.assert_called_once()

    def test_post_failure_preserves_output(self):
        http = FakeHTTP([INFO, DIFF, INFO, INFO, cr.ReviewError("GitHub HTTP 403", 3)])
        with patch.object(cr, "claude_code_review", return_value=cr.Review.from_data(DATA)):
            code, output, error = self.invoke(["--pr", URL, "--post"], env={"GH_TOKEN": "key", "ANTHROPIC_API_KEY": "api-key"}, http=http)
        self.assertEqual(code, 3)
        self.assertIn("## Summary", output)
        self.assertIn("403", error)

    def test_bad_url_exit_code(self):
        self.assertEqual(self.invoke(["--pr", "invalid"])[0], 2)

    def test_missing_snapshot(self):
        self.snap.unlink()
        self.assertEqual(self.invoke(self.replay_args())[0], 6)

    def test_output_directory_missing(self):
        self.assertEqual(self.invoke(self.replay_args() + ["--output", str(self.root / "missing" / "out")])[0], 6)

    def test_keyboard_interrupt(self):
        with patch.object(cr.GitHubClient, "snapshot", side_effect=KeyboardInterrupt):
            self.assertEqual(self.invoke(["--pr", URL], env={"ANTHROPIC_API_KEY": "api-key"})[0], 130)

    def test_broken_pipe(self):
        with patch.object(cr.sys, "stdout") as stdout:
            stdout.write.side_effect = BrokenPipeError()
            self.assertEqual(cr.main(self.replay_args(), env={}), 0)

    def test_parser_defaults(self):
        args = cr.parser().parse_args(["--pr", URL])
        self.assertEqual(args.backend, "claude-code")
        self.assertEqual(args.timeout, 90)
        self.assertFalse(args.post)

    def test_parser_errors(self):
        for args in ([], ["--pr", URL, "--unknown"], ["--pr", URL, "--backend", "fake"],
                     ["--pr", URL, "--timeout", "nan"], ["--pr", URL, "--timeout", "inf"],
                     ["--pr", URL, "--timeout", "0"], ["--pr", URL, "--timeout", "oops"],
                     ["--pr", URL, "--max-diff-bytes", "2"], ["--pr", URL, "--max-diff-bytes", "bad"],
                     ["--pr", URL, "--response-file", "a", "--export-request", "b"],
                     ["--pr", URL, "--out", "a"]):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
                cr.parser().parse_args(args)
            self.assertEqual(e.exception.code, 2)

    def test_parser_valid_custom_limits(self):
        args = cr.parser().parse_args(["--pr", URL, "--timeout", "12.5", "--max-diff-bytes", "2048"])
        self.assertEqual(args.timeout, 12.5)
        self.assertEqual(args.max_diff_bytes, 2048)

    def test_version_and_help(self):
        for flag in ("--version", "--help"):
            with self.subTest(flag=flag), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e:
                cr.main([flag], env={})
            self.assertEqual(e.exception.code, 0)


class TestFiles(unittest.TestCase):
    def test_atomic_replace_and_symlink_safety(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "keep"
            target.write_text("original")
            link = root / "link"
            link.symlink_to(target)
            cr.write_atomic(link, "new")
            self.assertEqual(target.read_text(), "original")
            self.assertEqual(link.read_text(), "new")
            self.assertFalse(link.is_symlink())
            self.assertEqual(link.stat().st_mode & 0o777, 0o600)

    def test_atomic_cleanup_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(cr.os, "replace", side_effect=OSError), self.assertRaises(cr.ReviewError):
                cr.write_atomic(Path(temp) / "out", "text")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_read_invalid_encoding_and_size(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input"
            for raw in (b"\xff", b"x" * (cr.MAX_RESPONSE + 1)):
                path.write_bytes(raw)
                with self.subTest(size=len(raw)), self.assertRaises(cr.ReviewError) as error:
                    cr.read_object(path, "input")
                self.assertEqual(error.exception.code, 6)


if __name__ == "__main__":
    unittest.main()
