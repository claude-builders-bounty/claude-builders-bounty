"""Offline integration checks for committed real-PR inputs and generated artifacts."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

import claude_review as cr

ROOT = Path(__file__).resolve().parents[1]


class TestArtifacts(unittest.TestCase):
    def test_real_pr_snapshot_statistics(self):
        for number, stats in ((6731, (1, 31, 15)), (6710, (1, 31, 6))):
            with self.subTest(pr=number):
                pr = cr.parse_pr_url(f"https://github.com/psf/requests/pull/{number}")
                data = cr.read_object(ROOT / "examples/fixtures" / f"requests-{number}.snapshot.json", "fixture")
                snapshot = cr.Snapshot.from_data(pr, data)
                self.assertEqual(cr.validate_diff(snapshot.diff), stats)

    def test_generated_reviews_match_and_disclose_recorded_backend(self):
        for number, name in ((6731, "pr-review-1.md"), (6710, "pr-review-2.md")):
            with self.subTest(pr=number):
                fixture = ROOT / "examples/fixtures" / f"requests-{number}"
                pr = cr.parse_pr_url(f"https://github.com/psf/requests/pull/{number}")
                snapshot = cr.Snapshot.from_data(pr, cr.read_object(fixture.with_suffix(".snapshot.json"), "fixture"))
                request = cr.make_request(snapshot)
                review, label = cr.imported_review(fixture.with_suffix(".response.json"), request)
                text = cr.render(review, request, label)
                self.assertEqual(text, (ROOT / "examples" / name).read_text(encoding="utf-8"))
                self.assertIn("NOT a live Claude run", text)
                self.assertEqual([line for line in text.splitlines() if line.startswith("## ")],
                                 ["## Summary", "## Risks", "## Improvement Suggestions", "## Confidence"])
                self.assertEqual(len(review.summary), 2)

    def test_reproduction_command(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/reproduce_examples.py"), "--check"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("PASS:"), 2)

    def test_workflow_never_checks_out_pr_head(self):
        text = (ROOT / "workflows/claude-review.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("pull_request_target", text)
        self.assertNotIn("pull_request.head", text)
        self.assertIn("github.event.repository.default_branch", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn('"$PR_URL"', text)
        self.assertNotIn('claude-review --pr ${{', text)

    def test_no_distribution_runtime_dependencies(self):
        import tomllib
        config = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(config["project"]["dependencies"], [])
        self.assertEqual(config["project"]["scripts"]["claude-review"], "claude_review:main")

    def test_metadata_source_urls_match_reviews(self):
        for number in (6731, 6710):
            data = json.loads((ROOT / "examples/fixtures" / f"requests-{number}.snapshot.json").read_text())
            self.assertEqual(data["metadata"]["html_url"], f"https://github.com/psf/requests/pull/{number}")

    def test_json_unicode_and_numeric_overflow_rejected(self):
        for raw in ('{"value": "\\ud800"}', '{"value": 1e9999}', '{"value": -1e9999}'):
            with self.subTest(raw=raw), self.assertRaises(cr.ReviewError):
                cr.object_json(raw)

    def test_json_valid_non_ascii_and_floats(self):
        self.assertEqual(cr.object_json('{"name":"München", "value": 1.5}'),
                         {"name": "München", "value": 1.5})


if __name__ == "__main__":
    unittest.main()
