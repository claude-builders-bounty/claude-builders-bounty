#!/usr/bin/env python3
"""Acceptance tests for issue #2853 read tool hook (zeroeye cross-repo bounty)."""

from __future__ import annotations

import json
import os
import re
import subprocess
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

    def test_zeroeye_has_committed_build_diagnostics(self) -> None:
        diagnostic_dir = ZEROEYE_ROOT / "diagnostic"
        self.assertTrue(diagnostic_dir.is_dir())

        logd_files = sorted(diagnostic_dir.glob("build-*.logd"))
        json_files = sorted(diagnostic_dir.glob("build-*.json"))
        self.assertGreater(len(logd_files), 0, "expected at least one build-*.logd")
        self.assertGreater(len(json_files), 0, "expected at least one build-*.json")

        latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
        metadata = json.loads(latest_json.read_text(encoding="utf-8"))
        self.assertEqual(metadata.get("failed"), 0)
        self.assertGreater(metadata.get("passed", 0), 0)
        self.assertIn("password", metadata)
        self.assertIn("diagnostic_logd", metadata)

        logd_path = ZEROEYE_ROOT / metadata["diagnostic_logd"]
        self.assertTrue(logd_path.is_file())
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


if __name__ == "__main__":
    unittest.main()
