#!/usr/bin/env python3
"""End-to-end delivery verification for bounty #4 fleet handoff."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
CI_SCRIPT = AGENT_DIR / "tests" / "run-ci-checks.sh"
PEER_REVIEW_TEST = AGENT_DIR / "tests" / "test_peer_review_acceptance.py"
UNIT_TEST = AGENT_DIR / "tests" / "test_claude_review.py"
PROOF_DOC = AGENT_DIR / "PROOF.md"


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


class DeliveryVerificationTests(unittest.TestCase):
    """Guards fleet delivery: npm test wiring, CI summaries, and CLI behavior."""

    def test_regression_suite_has_minimum_coverage(self):
        unit_tests = count_test_methods(UNIT_TEST)
        peer_review_tests = count_test_methods(PEER_REVIEW_TEST)
        self.assertGreaterEqual(unit_tests, 35)
        self.assertGreaterEqual(peer_review_tests, 12)

    def test_ci_script_exists_and_declares_delivery_checks(self):
        self.assertTrue(CI_SCRIPT.is_file())
        text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("delivery verification tests", text)
        self.assertIn("unit tests — OK", text)
        self.assertIn("peer review acceptance tests passed", text)
        self.assertIn("tests passed", text)

    def test_repo_root_exposes_npm_test_entry_points(self):
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test:ci"])

    def test_repo_root_keeps_reproducible_test_wiring(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("ci-validate:", makefile)
        self.assertTrue((REPO_ROOT / "package-lock.json").is_file())
        self.assertIn("node_modules/", gitignore)
        self.assertIn("internal/", gitignore)

    def test_cli_help_and_local_diff_review(self):
        result = subprocess.run(
            [str(REPO_ROOT / "claude-review"), "--help"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            check=True,
        )
        self.assertIn("--pr", result.stdout)
        self.assertIn("--diff-file", result.stdout)

    def test_ci_runner_total_matches_discovered_test_counts(self):
        unit_tests = count_test_methods(UNIT_TEST)
        delivery_tests = count_test_methods(Path(__file__))
        peer_review_tests = count_test_methods(PEER_REVIEW_TEST)
        expected_total = unit_tests + delivery_tests + peer_review_tests

        ci_text = CI_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("total_tests=$((unit_tests + delivery_tests + peer_review_tests))", ci_text)
        self.assertIn('echo "OK: ${total_tests} tests passed"', ci_text)

        proof = PROOF_DOC.read_text(encoding="utf-8")
        self.assertIn(f"Ran {unit_tests} unit tests — OK", proof)
        self.assertIn(f"Ran {delivery_tests} delivery verification tests — OK", proof)
        self.assertIn(f"Ran {peer_review_tests} tests — OK", proof)
        self.assertIn(f"OK: {expected_total} tests passed", proof)


if __name__ == "__main__":
    unittest.main()
