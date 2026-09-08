from __future__ import annotations

import email.message
import hashlib
import io
import json
import shutil
import subprocess
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from claude_review import __version__, core
from claude_review.cli import main
from claude_review.core import (
    EmptyDiffError,
    InputValidationError,
    MissingSnapshotError,
    OutputValidationError,
    PullRef,
    load_offline,
    parse_diff,
    parse_files,
    parse_metadata,
    parse_pr_url,
    render_report,
    scan,
    validate_report,
)
from claude_review.github import RateLimited, _request, fetch_pull

SOLUTION = Path(__file__).resolve().parents[1]
REF = PullRef("owner", "repo", 123)
VALID_METADATA = {
    "html_url": "https://github.com/owner/repo/pull/123",
    "number": 123,
    "title": "Example",
    "head": {"sha": "a" * 40},
    "base": {"sha": "b" * 40},
    "updated_at": "2026-09-01T12:00:00Z",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OfflineSnapshotTests(unittest.TestCase):
    def test_url_parsing_accepts_canonical_github_pr(self) -> None:
        actual = parse_pr_url("https://github.com/Owner/Repo/pull/123?x=1#fragment")
        self.assertEqual(actual, PullRef("Owner", "Repo", 123))

    def test_url_parsing_rejects_non_pr_and_non_github(self) -> None:
        for url in (
            "http://github.com/owner/repo/pull/123",
            "https://gitlab.com/owner/repo/pull/123",
            "https://github.com/owner/repo/issues/123",
            "https://github.com/owner/repo/pull/zero",
            "https://github.com/owner/repo/pull/123/extra",
        ):
            with self.assertRaises(core.ReviewError):
                parse_pr_url(url)

    def test_metadata_and_file_records_parse(self) -> None:
        metadata = dict(VALID_METADATA)
        title, head, base, updated_at = parse_metadata(json.dumps(metadata).encode(), REF)
        self.assertEqual(
            (title, head, base, updated_at),
            ("Example", "a" * 40, "b" * 40, "2026-09-01T12:00:00Z"),
        )
        files = parse_files(json.dumps([{"filename": "x.txt", "status": "added", "additions": 2}]).encode())
        self.assertEqual(files[0].filename, "x.txt")

    def test_both_real_snapshots_load(self) -> None:
        for number, files, additions, deletions in ((4082, 10, 884, 2), (4122, 3, 206, 0)):
            ref = PullRef("claude-builders-bounty", "claude-builders-bounty", number)
            data = load_offline(ref, SOLUTION / "tests/fixtures" / f"pr-{number}")
            self.assertEqual(len(data.files), files)
            self.assertEqual(sum(item.additions for item in data.files), additions)
            self.assertEqual(sum(item.deletions for item in data.files), deletions)

    def test_binary_and_rename_markers_are_labeled_not_scanned_as_content(self) -> None:
        files = parse_files(json.dumps([
            {"filename": "logo.png", "status": "added", "additions": 0, "deletions": 0, "binary": True},
            {"filename": "new.txt", "previous_filename": "old.txt", "status": "renamed", "additions": 0, "deletions": 0},
        ]).encode())
        diff = (
            "diff --git a/logo.png b/logo.png\nBinary files a/logo.png and b/logo.png differ\n"
            "diff --git a/old.txt b/new.txt\nsimilarity index 100%\nrename from old.txt\nrename to new.txt\n"
        )
        hunks, merged = parse_diff(diff, files)
        self.assertEqual(hunks["logo.png"], ())
        self.assertEqual(hunks["new.txt"], ())
        findings = scan(core.ReviewData(REF, "Example", "a" * 40, "b" * 40, "2026-09-01T12:00:00Z", merged, hunks))
        self.assertEqual({item["rule"] for item in findings}, {"binary", "rename"})

    def test_findings_cite_exact_changed_line_and_uncertainty(self) -> None:
        files = parse_files(json.dumps([
            {"filename": "safe.py", "status": "added", "additions": 2, "deletions": 0},
            {"filename": "empty.py", "status": "added", "additions": 1, "deletions": 0},
        ]).encode())
        diff = (
            "diff --git a/safe.py b/safe.py\nnew file mode 100644\n--- /dev/null\n+++ b/safe.py\n"
            "@@ -0,0 +1,2 @@\n+result = subprocess.run(cmd, shell=True)\n+no_risk = True\n"
            "diff --git a/empty.py b/empty.py\nnew file mode 100644\n--- /dev/null\n+++ b/empty.py\n"
        )
        hunks, merged = parse_diff(diff, files)
        findings = scan(core.ReviewData(REF, "Example", "a" * 40, "b" * 40, "2026-09-01T12:00:00Z", merged, hunks))
        self.assertEqual(findings[0]["evidence"], "result = subprocess.run(cmd, shell=True)")
        self.assertIn("new line 1", findings[0]["anchor"])
        self.assertEqual(findings[-1]["rule"], "missing_hunk")

    def test_pattern_mentions_in_strings_do_not_become_findings(self) -> None:
        files = parse_files(json.dumps([{"filename": "x.py", "status": "added", "additions": 1}]).encode())
        diff = "diff --git a/x.py b/x.py\n@@ -0,0 +1 @@\n+message = 'except Exception:'\n"
        hunks, merged = parse_diff(diff, files)
        self.assertEqual(scan(core.ReviewData(REF, "Example", "a" * 40, "b" * 40, "2026-09-01T12:00:00Z", merged, hunks)), [])


class ReportContractTests(unittest.TestCase):
    def sample_reports(self) -> list[str]:
        return [
            render_report(load_offline(PullRef("claude-builders-bounty", "claude-builders-bounty", number), SOLUTION / "tests/fixtures" / f"pr-{number}"))
            for number in (4082, 4122)
        ]

    def test_exact_headings_summary_and_confidence(self) -> None:
        expected = ["## Summary of changes", "## Identified risks", "## Improvement suggestions", "## Confidence score"]
        for report in self.sample_reports():
            self.assertEqual([line for line in report.splitlines() if line.startswith("## ")], expected)
            body = report.split("## Summary of changes", 1)[1].split("## Identified risks", 1)[0]
            self.assertTrue(2 <= len([part for part in body.split(".") if part.strip()]) <= 3)
            validate_report(report)
            self.assertRegex(report, r"Confidence score: (Low|Medium|High)\b")

    def test_real_reports_are_evidence_grounded_and_differ(self) -> None:
        first, second = self.sample_reports()
        self.assertNotEqual(first, second)
        self.assertIn("`test_agent.py`", second)
        self.assertIn('"~/.bashrc"', second)

    def test_report_order_is_stable(self) -> None:
        report_a = self.sample_reports()[0]
        report_b = self.sample_reports()[0]
        self.assertEqual(report_a, report_b)

    def test_oversized_finding_output_is_explicitly_truncated(self) -> None:
        original = core.MAX_FINDINGS
        core.MAX_FINDINGS = 1
        try:
            data = load_offline(PullRef("claude-builders-bounty", "claude-builders-bounty", 4082), SOLUTION / "tests/fixtures/pr-4082")
            report = render_report(data)
            self.assertIn("[Output truncated:", report)
            self.assertIn("lower-priority finding(s) omitted", report)
        finally:
            core.MAX_FINDINGS = original


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.status = 200

    def read(self, amount: int = -1) -> bytes:
        return self.payload[:amount]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, payloads: list[bytes]):
        self.payloads = payloads
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append((request.full_url, dict(request.header_items()), timeout))
        return FakeResponse(self.payloads.pop(0))


class OnlineTests(unittest.TestCase):
    def test_request_construction_is_unauthenticated(self) -> None:
        request = _request("https://api.github.com/example", "application/vnd.github+json")
        self.assertEqual(request.get_method(), "GET")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(request.headers["User-agent"], "claude-review/1.0.0")

    def test_online_fetch_uses_three_unauthenticated_endpoints(self) -> None:
        metadata = dict(VALID_METADATA)
        files = [{"filename": "x.txt", "status": "added", "additions": 1, "deletions": 0}]
        diff = "diff --git a/x.txt b/x.txt\nnew file mode 100644\n--- /dev/null\n+++ b/x.txt\n@@ -0,0 +1 @@\n+hello\n"
        opener = FakeOpener([json.dumps(metadata).encode(), json.dumps(files).encode(), diff.encode()])
        data = fetch_pull(REF, opener)
        self.assertEqual(data.title, "Example")
        self.assertEqual(data.hunks["x.txt"][0].new_start, 1)
        self.assertEqual(opener.requests[0][0], "https://api.github.com/repos/owner/repo/pulls/123")
        self.assertIn("page=1", opener.requests[1][0])
        self.assertEqual(opener.requests[2][0], "https://github.com/owner/repo/pull/123.diff")
        for _, headers, _ in opener.requests:
            self.assertNotIn("Authorization", headers)

    def test_rate_limit_is_controlled(self) -> None:
        headers = email.message.Message()
        headers["X-RateLimit-Remaining"] = "0"
        class RateOpener:
            def open(self, request, timeout=None):
                raise urllib.error.HTTPError(request.full_url, 403, "rate limited", headers, io.BytesIO(b""))
        with self.assertRaises(RateLimited):
            fetch_pull(REF, RateOpener())


class CliFailureTests(unittest.TestCase):
    def run_main(self, argv: list[str]):
        out, err = io.StringIO(), io.StringIO()
        return main(argv, stdout=out, stderr=err), out.getvalue(), err.getvalue()

    def test_help_and_version(self) -> None:
        for argument, expected in (("--help", "usage:"), ("--version", __version__)):
            result = subprocess.run([str(SOLUTION / "claude-review"), argument], cwd=SOLUTION, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn(expected, result.stdout)

    def test_invalid_url(self) -> None:
        code, _, err = self.run_main(["--pr", "not-a-pr"])
        self.assertEqual(code, 2)
        self.assertIn("Invalid PR URL", err)

    def test_missing_or_private_offline_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            code, _, err = self.run_main(["--pr", VALID_METADATA["html_url"], "--offline", "--context-dir", directory])
            self.assertEqual(code, 3)
            self.assertIn("missing metadata.json", err)

    def test_malformed_json_diff_empty_and_oversized(self) -> None:
        cases = []
        with tempfile.TemporaryDirectory() as root:
            for name in ("malformed-json", "malformed-diff", "empty-diff", "oversized-diff"):
                path = Path(root) / name
                path.mkdir()
                shutil.copy(SOLUTION / "tests/fixtures/pr-4122/metadata.json", path / "metadata.json")
                shutil.copy(SOLUTION / "tests/fixtures/pr-4122/files.json", path / "files.json")
                shutil.copy(SOLUTION / "tests/fixtures/pr-4122/pr.diff", path / "pr.diff")
                cases.append(path)
            (cases[0] / "metadata.json").write_text("{", encoding="utf-8")
            (cases[1] / "pr.diff").write_text("diff --git\n", encoding="utf-8")
            (cases[2] / "pr.diff").write_text("   \n", encoding="utf-8")
            (cases[3] / "pr.diff").write_bytes(b"diff\n" + b"x" * (core.MAX_DIFF_BYTES))
            expected = (4, 4, 5, 4)
            for path, wanted in zip(cases, expected):
                code, _, err = self.run_main([
                    "--pr", "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4122",
                    "--offline", "--context-dir", str(path),
                ])
                self.assertEqual(code, wanted, err)

    def test_output_validation_failure_is_controlled(self) -> None:
        with mock.patch("claude_review.cli.render_report", return_value="not a report"):
            code, _, err = self.run_main([
                "--pr", "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/4122",
                "--offline", "--context-dir", str(SOLUTION / "tests/fixtures/pr-4122"),
            ])
        self.assertEqual(code, 6)
        self.assertIn("Internal output validation failed", err)

    def test_errors_do_not_leak_tracebacks(self) -> None:
        code, _, err = self.run_main(["--pr", "bad"])
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class ProvenanceTests(unittest.TestCase):
    def test_provenance_matches_inputs_outputs_and_metadata(self) -> None:
        required = {
            "canonical_pr_url", "number", "head_sha", "base_sha",
            "metadata_updated_at",
            "capture_source_paths", "input_sha256", "generated_output_sha256", "cli_version", "regeneration_command",
        }
        for number in (4082, 4122):
            data = json.loads((SOLUTION / f"examples/pr-{number}/provenance.json").read_text())
            self.assertTrue(required.issubset(data))
            fixture = SOLUTION / f"tests/fixtures/pr-{number}"
            metadata = json.loads((fixture / "metadata.json").read_text())
            self.assertEqual(data["canonical_pr_url"], metadata["html_url"])
            self.assertEqual(data["head_sha"], metadata["head"]["sha"])
            self.assertEqual(data["base_sha"], metadata["base"]["sha"])
            self.assertEqual(data["metadata_updated_at"], metadata["updated_at"])
            for name in ("metadata.json", "files.json", "pr.diff"):
                self.assertEqual(data["input_sha256"][name], sha256(fixture / name))
            self.assertEqual(data["generated_output_sha256"], sha256(SOLUTION / f"examples/pr-{number}/review.md"))


class ClaudeAgentIntegrationTests(unittest.TestCase):
    def test_pr_reviewer_agent_contract(self) -> None:
        path = SOLUTION / ".claude/agents/pr-reviewer.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        frontmatter = text.split("---\n", 2)[1]
        self.assertIn("name: pr-reviewer", frontmatter)
        self.assertIn("description: Review a GitHub pull request using the deterministic claude-review CLI.", frontmatter)
        self.assertIn("tools: Bash, Read", frontmatter)
        self.assertIn("maxTurns: 4", frontmatter)
        self.assertIn("./claude-review --pr <URL>", text)
        for heading in (
            "## Summary of changes",
            "## Identified risks",
            "## Improvement suggestions",
            "## Confidence score",
        ):
            self.assertIn(heading, text)
        self.assertIn("four-heading Markdown report verbatim", text)
        self.assertIn("Do not add model-derived findings", text)
        self.assertIn("deterministic/static and is not model analysis", text)
        self.assertIn("explicitly requests posting", text)
        self.assertIn("never invent or supply credentials", text)


if __name__ == "__main__":
    unittest.main()
