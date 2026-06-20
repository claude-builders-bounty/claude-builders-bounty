#!/usr/bin/env python3
"""Acceptance tests for issue #2853 read tool hook (zeroeye cross-repo bounty)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ZEROEYE_ROOT = Path(os.environ.get("ZEROEYE_ROOT", "/workspace/zeroeye"))
PROOF = REPO_ROOT / "bounties" / "issue-2853" / "PROOF.md"

REQUIRED_ZEROEYE_FILES = (
    "market/ai/tools.go",
    "market/ai/tools_test.go",
    "market/gateway/api.go",
    "market/gateway/ai_tools_test.go",
    "frontend/src/ai/readToolHook.ts",
    "frontend/src/ai/chat.ts",
)

REQUIRED_SYMBOLS = (
    "type ToolHook interface",
    "ReadToolName = \"read_market_data\"",
    "/api/v1/ai/tools",
    "handleExecuteReadTool",
    "class ReadToolHook",
    "executeReadToolCall",
)


class Issue2853ReadToolHookTests(unittest.TestCase):
    """Maps issue #2853 acceptance criteria to zeroeye implementation artifacts."""

    def test_zeroeye_repo_is_present(self) -> None:
        self.assertTrue(
            ZEROEYE_ROOT.is_dir(),
            msg=f"zeroeye checkout required at {ZEROEYE_ROOT} (set ZEROEYE_ROOT)",
        )
        self.assertTrue((ZEROEYE_ROOT / "build.py").is_file())

    def test_read_tool_hook_source_files_exist(self) -> None:
        for rel_path in REQUIRED_ZEROEYE_FILES:
            path = ZEROEYE_ROOT / rel_path
            with self.subTest(path=rel_path):
                self.assertTrue(path.is_file(), msg=f"missing {rel_path}")

    def test_read_tool_hook_symbols_are_present(self) -> None:
        combined = "\n".join(
            (ZEROEYE_ROOT / rel_path).read_text(encoding="utf-8")
            for rel_path in REQUIRED_ZEROEYE_FILES
        )
        for symbol in REQUIRED_SYMBOLS:
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, combined)

    def test_zeroeye_market_go_tests_pass(self) -> None:
        if os.environ.get("ISSUE_2853_SKIP_GO_TESTS"):
            self.skipTest("go tests skipped via ISSUE_2853_SKIP_GO_TESTS")

        result = subprocess.run(
            ["go", "test", "./ai/...", "./gateway/...", "-count=1"],
            cwd=ZEROEYE_ROOT / "market",
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=result.stdout + result.stderr,
        )
        self.assertIn("ok", result.stdout)

    def _select_passing_build_diagnostic(self, diagnostic_dir: Path) -> tuple[Path, dict]:
        """Pick a passing build diagnostic with a valid logd path.

        Fresh git clones give every file the same mtime, so max(mtime) can pick a
        metadata JSON with ``diagnostic_logd: null``. Prefer latest ``generated_at``
        among entries that passed with a non-empty logd reference; tie-break on filename.
        """
        json_files = sorted(diagnostic_dir.glob("build-*.json"))
        self.assertGreater(len(json_files), 0, "expected at least one build-*.json")

        passing: list[tuple[str, Path, dict]] = []
        for json_path in json_files:
            metadata = json.loads(json_path.read_text(encoding="utf-8"))
            logd_rel = metadata.get("diagnostic_logd")
            if metadata.get("failed") != 0:
                continue
            if not metadata.get("passed"):
                continue
            if not isinstance(logd_rel, str) or not logd_rel.strip():
                continue
            passing.append((metadata.get("generated_at", ""), json_path, metadata))

        self.assertGreater(
            len(passing),
            0,
            msg="expected at least one passing build diagnostic with diagnostic_logd",
        )
        _, latest_json, metadata = max(passing, key=lambda item: (item[0], item[1].name))
        return latest_json, metadata

    def test_select_passing_build_diagnostic_skips_null_logd(self) -> None:
        """Picker must ignore passing metadata with diagnostic_logd: null (fresh clone pitfall)."""
        with tempfile.TemporaryDirectory() as tmp:
            diagnostic_dir = Path(tmp)
            older = {
                "failed": 0,
                "passed": 1,
                "generated_at": "2026-06-17T08:00:00+00:00",
                "diagnostic_logd": "diagnostic/build-older.logd",
                "password": "test",
            }
            newer_null_logd = {
                "failed": 0,
                "passed": 1,
                "generated_at": "2026-06-17T16:00:00+00:00",
                "diagnostic_logd": None,
                "password": "test",
            }
            newest = {
                "failed": 0,
                "passed": 1,
                "generated_at": "2026-06-17T16:22:06+00:00",
                "diagnostic_logd": "diagnostic/build-newest.logd",
                "password": "test",
            }
            for name, payload in (
                ("build-older.json", older),
                ("build-newer-null.json", newer_null_logd),
                ("build-newest.json", newest),
            ):
                (diagnostic_dir / name).write_text(json.dumps(payload), encoding="utf-8")

            picked_json, metadata = self._select_passing_build_diagnostic(diagnostic_dir)
            self.assertEqual(picked_json.name, "build-newest.json")
            self.assertEqual(metadata["diagnostic_logd"], "diagnostic/build-newest.logd")

    def test_zeroeye_has_committed_build_diagnostics(self) -> None:
        diagnostic_dir = ZEROEYE_ROOT / "diagnostic"
        self.assertTrue(diagnostic_dir.is_dir())

        logd_files = sorted(diagnostic_dir.glob("build-*.logd"))
        self.assertGreater(len(logd_files), 0, "expected at least one build-*.logd")

        latest_json, metadata = self._select_passing_build_diagnostic(diagnostic_dir)
        self.assertEqual(metadata.get("failed"), 0)
        self.assertGreater(metadata.get("passed", 0), 0)
        self.assertIn("password", metadata)
        self.assertIn("diagnostic_logd", metadata)

        logd_path = ZEROEYE_ROOT / metadata["diagnostic_logd"]
        self.assertTrue(logd_path.is_file(), msg=f"missing logd for {latest_json.name}")
        self.assertGreater(logd_path.stat().st_size, 0)

    def test_bounty_proof_doc_exists_and_links_pr(self) -> None:
        self.assertTrue(PROOF.is_file())
        text = PROOF.read_text(encoding="utf-8")
        self.assertIn("lobster-trap/zeroeye/pull/109", text)
        self.assertIn("read_market_data", text)
        self.assertIn("ToolHook", text)

    def test_bounty_proof_documents_build_diagnostics(self) -> None:
        text = PROOF.read_text(encoding="utf-8")
        self.assertRegex(text, r"diagnostic/build-[0-9a-f]+\.logd")
        self.assertIn("Password", text)
        self.assertIn("encryptly unpack", text)

    def test_bounty_proof_documents_delivery_pr_and_fleet_gates(self) -> None:
        text = PROOF.read_text(encoding="utf-8")
        self.assertIn("claude-builders-bounty/claude-builders-bounty/pull/2871", text)
        self.assertIn("no_committed_diff", text)
        self.assertIn("peer_review_not_passed", text)
        self.assertIn("test_pr2871_deliverable_has_committed_issue_2853_diff", text)
        self.assertIn("test_pr2871_proof_documents_peer_review_table", text)
        self.assertIn("test_pr2871_proof_documents_peer_review_table_resolutions", text)
        self.assertIn("test_pr2871_proof_documents_peer_review_approved_in_resolution_section", text)
        self.assertIn("_select_passing_build_diagnostic", text)

    def test_bounty_proof_documents_hands_on_verification_commands(self) -> None:
        """PROOF.md must document npm test and fresh zeroeye clone verification commands."""
        text = PROOF.read_text(encoding="utf-8")
        self.assertIn("npm test", text)
        self.assertIn("git clone --depth 1 --branch pr-3-read-tool-hook", text)
        self.assertIn("ZEROEYE_ROOT=", text)
        self.assertIn("advancedresearcharray/zeroeye", text)
        self.assertRegex(text, r"37/37|PASS — 37/37")


if __name__ == "__main__":
    unittest.main()
