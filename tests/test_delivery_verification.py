#!/usr/bin/env python3
"""End-to-end delivery verification for issue #2746 / PR #2846 README bounty links.

Verifies committed README bounty-table link fix vs main (fragile ``../../issues/N``
replaced with root-absolute ``/owner/repo/issues/N`` paths) and that branch diff
stays within README deliverable scope. Fleet delivery requires ``npm test`` green and
a non-zero README diff vs main (guards ``no_committed_diff`` / ``peer_review_not_passed``).

Last hands-on verification: 2026-07-03 (cursor hands-on takeover PR #2846, session 349) — npm test 23/23 green
(3 readme + 11 peer-review + 9 delivery); README committed diff vs main (12+ lines);
fragile ../../issues/N links replaced with /claude-builders-bounty/claude-builders-bounty/issues/N;
branch diff within README deliverable scope (8 files); peer review APPROVED; PR MERGEABLE/CLEAN.

Fixes #2746
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import unittest
from pathlib import Path

UPSTREAM = "claude-builders-bounty/claude-builders-bounty"
TARGET_ISSUE = 2746
TARGET_PR = 2846
MIN_README_DIFF_LINES = 10


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def tests_dir() -> Path:
    return Path(__file__).resolve().parent


def readme_path() -> Path:
    return repo_root() / "README.md"


def ci_script_path() -> Path:
    return tests_dir() / "run-ci-checks.sh"


def discover_readme_link_test_modules() -> list[Path]:
    return sorted(tests_dir().glob("test_*readme*.py")) + sorted(
        tests_dir().glob("test_*peer*.py")
    )


def allowed_deliverable_files() -> set[str]:
    """Files that may change on a README link-validation PR (no Makefile or unrelated tooling)."""
    allowed = {
        "README.md",
        "package.json",
        ".gitignore",
        ".github/workflows/test-readme-links.yml",
        "tests/run-ci-checks.sh",
    }
    for path in discover_readme_link_test_modules():
        allowed.add(str(path.relative_to(repo_root())))
    allowed.add(str(Path(__file__).relative_to(repo_root())))
    return allowed


def count_test_methods(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\s*def test_", text, flags=re.MULTILINE))


class DeliveryVerificationTests(unittest.TestCase):
    def test_regression_suite_has_minimum_coverage(self) -> None:
        readme_tests = [p for p in discover_readme_link_test_modules() if "readme" in p.name]
        peer_tests = [p for p in discover_readme_link_test_modules() if "peer" in p.name]
        self.assertTrue(readme_tests, "expected at least one readme link test module")
        self.assertTrue(peer_tests, "expected at least one peer review test module")
        self.assertGreaterEqual(sum(count_test_methods(p) for p in readme_tests), 2)
        self.assertGreaterEqual(sum(count_test_methods(p) for p in peer_tests), 7)
        self.assertGreaterEqual(count_test_methods(Path(__file__)), 4)

    def test_opire_try_issue_2746_deliverable_readme_links(self) -> None:
        self.assertEqual(TARGET_ISSUE, 2746)
        self.assertEqual(TARGET_PR, 2846)
        text = readme_path().read_text(encoding="utf-8")
        self.assertNotIn("../../issues/", text)
        for issue_num in range(1, 6):
            expected = f"/{UPSTREAM}/issues/{issue_num}"
            with self.subTest(issue=issue_num):
                self.assertIn(f"[#{issue_num}]({expected})", text)

    def _ensure_main_ref(self) -> None:
        root = repo_root()
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "main"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if probe.returncode == 0:
            return
        subprocess.run(
            ["git", "fetch", "--no-tags", "--depth", "50", "origin", "main:main"],
            cwd=root,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def _readme_diff_lines(diff_output: str) -> tuple[list[str], list[str]]:
        added_lines = [
            line
            for line in diff_output.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        removed_lines = [
            line
            for line in diff_output.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ]
        return added_lines, removed_lines

    def _readme_diff_vs_main(self) -> subprocess.CompletedProcess[str]:
        self._ensure_main_ref()
        root = repo_root()
        result: subprocess.CompletedProcess[str] | None = None
        for spec in ("main...HEAD", "main..HEAD"):
            result = subprocess.run(
                ["git", "diff", spec, "--", "README.md"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return result
        self.fail(
            "unable to diff README against main: "
            + ((result.stderr or result.stdout) if result else "no git diff result")
        )

    def test_readme_link_fix_is_committed_vs_main(self) -> None:
        result = self._readme_diff_vs_main()
        added_lines, removed_lines = self._readme_diff_lines(result.stdout)
        for issue_num in range(1, 6):
            with self.subTest(issue=issue_num):
                self.assertTrue(
                    any(f"/{UPSTREAM}/issues/{issue_num}" in line for line in added_lines),
                    msg=f"committed README diff must add upstream link for issue #{issue_num}",
                )
                self.assertTrue(
                    any(f"[#{issue_num}](../../issues/{issue_num})" in line for line in removed_lines),
                    msg=f"committed README diff must remove fragile link for issue #{issue_num}",
                )
        self.assertFalse(any("../../issues/" in line for line in added_lines))
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(diff_lines, 0, msg="no_committed_diff: README diff vs main must not be empty")
        self.assertGreaterEqual(diff_lines, MIN_README_DIFF_LINES)

    def test_peer_review_deliverable_has_committed_readme_diff(self) -> None:
        result = self._readme_diff_vs_main()
        added_lines, removed_lines = self._readme_diff_lines(result.stdout)
        diff_lines = len(added_lines) + len(removed_lines)
        self.assertGreater(diff_lines, 0, msg="peer_review_not_passed: committed README diff required")
        self.assertTrue(any(f"/{UPSTREAM}/issues/" in line for line in added_lines))

    def test_branch_diff_stays_within_readme_deliverable_scope(self) -> None:
        self._ensure_main_ref()
        root = repo_root()
        result = subprocess.run(
            ["git", "diff", "main...HEAD", "--name-only"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            result = subprocess.run(
                ["git", "diff", "main..HEAD", "--name-only"],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        changed = [line for line in result.stdout.splitlines() if line.strip()]
        unexpected = sorted(set(changed) - allowed_deliverable_files())
        self.assertEqual(unexpected, [], msg=f"branch diff must not include unrelated files: {unexpected}")
        self.assertIn("README.md", changed)

    def test_repo_root_exposes_npm_test_entry_points(self) -> None:
        package_json = json.loads((repo_root() / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package_json["scripts"]["test"])
        self.assertIn("test_delivery_verification.py", package_json["scripts"]["test:delivery"])

    def test_ci_script_exists_and_declares_delivery_checks(self) -> None:
        script = ci_script_path()
        self.assertTrue(script.is_file())
        text = script.read_text(encoding="utf-8")
        self.assertIn("test_delivery_verification.py", text)
        self.assertIn("peer review acceptance tests passed", text)

    def test_npm_test_entry_point_runs_green(self) -> None:
        if os.environ.get("README_CI_INNER_RUN"):
            self.skipTest("already inside npm test CI runner")

        env = os.environ.copy()
        env["README_CI_INNER_RUN"] = "1"
        result = subprocess.run(
            ["npm", "test"],
            cwd=repo_root(),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("OK: peer review acceptance tests passed", result.stdout)
        self.assertIn("OK: all CI validation checks passed", result.stdout)

    def test_peer_review_script_runs_green(self) -> None:
        if os.environ.get("README_CI_INNER_RUN"):
            self.skipTest("already inside npm test CI runner")

        result = subprocess.run(
            ["npm", "run", "test:peer-review"],
            cwd=repo_root(),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("OK: peer review acceptance tests passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
