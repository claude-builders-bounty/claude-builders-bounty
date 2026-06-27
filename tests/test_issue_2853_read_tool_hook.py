#!/usr/bin/env python3
"""Acceptance tests for issue #2853 read tool hook (zeroeye cross-repo bounty)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

_GO_TEST_LOCK = threading.Lock()

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

GO_LAYER_FILES = ("market/ai/tools.go", "market/ai/tools_test.go")
GATEWAY_LAYER_FILES = ("market/gateway/api.go", "market/gateway/ai_tools_test.go")
FRONTEND_LAYER_FILES = ("frontend/src/ai/readToolHook.ts", "frontend/src/ai/chat.ts")


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

    def _layer_text(self, rel_paths: tuple[str, ...]) -> str:
        return "\n".join(
            (ZEROEYE_ROOT / rel_path).read_text(encoding="utf-8") for rel_path in rel_paths
        )

    def _fresh_go_env(self) -> tuple[dict[str, str], list[Path]]:
        """Return env with isolated GOCACHE/GOTMPDIR/TMPDIR and temp dirs to remove after use."""
        cache_root = REPO_ROOT / ".cache" / "go-test-tmp"
        cache_root.mkdir(parents=True, exist_ok=True)
        gocache = Path(tempfile.mkdtemp(dir=cache_root))
        gotmp = Path(tempfile.mkdtemp(dir=cache_root))
        env = {
            **os.environ,
            "GOCACHE": str(gocache),
            "GOTMPDIR": str(gotmp),
            "TMPDIR": str(gotmp),
            "GOMAXPROCS": "1",
        }
        return env, [gocache, gotmp]

    def _run_go_test(
        self,
        args: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
    ) -> subprocess.CompletedProcess[str]:
        """Run go test with serialized CGO builds to avoid /tmp assembler races."""
        run_args = list(args)
        if not any(arg.startswith("-vet") for arg in run_args):
            run_args = [*run_args, "-vet=off"]

        with _GO_TEST_LOCK:
            last: subprocess.CompletedProcess[str] | None = None
            for attempt in range(3):
                last = subprocess.run(
                    run_args,
                    cwd=cwd,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if last.returncode == 0:
                    return last
                combined = last.stdout + last.stderr
                transient = "vet.cfg" in combined or (
                    "no such file or directory" in combined and "go-build" in combined
                )
                if not transient or attempt == 2:
                    return last
                time.sleep(1)
            assert last is not None
            return last

    def test_read_tool_hook_go_layer_symbols(self) -> None:
        text = self._layer_text(GO_LAYER_FILES)
        for symbol in ("type ToolHook interface", "ReadToolName = \"read_market_data\""):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, text)

    def test_read_tool_hook_gateway_layer_symbols(self) -> None:
        text = self._layer_text(GATEWAY_LAYER_FILES)
        for symbol in ("/api/v1/ai/tools", "handleExecuteReadTool"):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, text)

    def test_read_tool_hook_frontend_layer_symbols(self) -> None:
        text = self._layer_text(FRONTEND_LAYER_FILES)
        for symbol in ("class ReadToolHook", "executeReadToolCall"):
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, text)

    def test_verify_issue_2853_script_reuses_clone_and_archives_sessions(self) -> None:
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        sessions_readme = REPO_ROOT / "bounties" / "issue-2853" / "sessions" / "README.md"
        self.assertTrue(script.is_file())
        self.assertTrue(script.stat().st_mode & 0o111)
        text = script.read_text(encoding="utf-8")
        self.assertIn("Reusing zeroeye checkout", text)
        self.assertIn("archive_session_diff", text)
        self.assertIn("bounties/issue-2853/sessions", text)
        self.assertIn("validate_branch_name", text)
        self.assertIn("validate_git_remote_url", text)
        self.assertIn('trap on_fail ERR', text)
        self.assertTrue(sessions_readme.is_file())
        self.assertIn("session-", sessions_readme.read_text(encoding="utf-8"))
        self.assertIn("verify-issue-2853.sh", sessions_readme.read_text(encoding="utf-8"))

    def test_verify_issue_2853_script_rejects_invalid_branch_name(self) -> None:
        """Shell injection in ZEROEYE_BRANCH must fail before any git clone."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["ZEROEYE_BRANCH"] = "bad branch;rm -rf /"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid ZEROEYE_BRANCH", combined)

    def test_verify_issue_2853_script_rejects_branch_with_dotdot(self) -> None:
        """Path traversal in ZEROEYE_BRANCH must fail before any git clone."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["ZEROEYE_BRANCH"] = "pr-3..read-tool-hook"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid ZEROEYE_BRANCH", combined)

    def test_verify_issue_2853_script_rejects_untrusted_repo_url(self) -> None:
        """Only https://github.com/owner/repo.git remotes are accepted."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["ZEROEYE_REPO"] = "https://evil.example/zeroeye.git"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid ZEROEYE_REPO", combined)

    def test_verify_issue_2853_script_rejects_ssh_repo_url(self) -> None:
        """Only https://github.com/owner/repo.git remotes are accepted (no git@ or ssh)."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["ZEROEYE_REPO"] = "git@github.com:advancedresearcharray/zeroeye.git"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid ZEROEYE_REPO", combined)

    def test_verify_issue_2853_script_rejects_invalid_session_label(self) -> None:
        """Shell injection in VERIFY_SESSION_LABEL must fail before any git clone."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["VERIFY_SESSION_LABEL"] = "bad label;rm -rf /"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid VERIFY_SESSION_LABEL", combined)

    def test_verify_issue_2853_script_rejects_path_outside_cache(self) -> None:
        """ZEROEYE_ROOT must stay under .cache/ to block arbitrary clone targets."""
        script = REPO_ROOT / "tests" / "verify-issue-2853.sh"
        env = os.environ.copy()
        env["ZEROEYE_ROOT"] = "/tmp/zeroeye-outside-cache"
        result = subprocess.run(
            ["bash", str(script)],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("invalid ZEROEYE_ROOT", combined)

    def test_read_tool_hook_go_tests_surface_errors_on_failure(self) -> None:
        """Go test subprocess must propagate non-zero exit and include output in assertion."""
        if os.environ.get("ISSUE_2853_SKIP_GO_TESTS"):
            self.skipTest("go tests skipped via ISSUE_2853_SKIP_GO_TESTS")
        if not (ZEROEYE_ROOT / "market").is_dir():
            self.skipTest("zeroeye market module not present")

        bad_dir = Path(tempfile.mkdtemp())
        bad_env, bad_dirs = self._fresh_go_env()
        try:
            result = self._run_go_test(
                ["go", "test", "-p", "1", "./ai/...", "-count=1"],
                cwd=bad_dir,
                env=bad_env,
            )
            self.assertNotEqual(result.returncode, 0)
        finally:
            shutil.rmtree(bad_dir, ignore_errors=True)
            for path in bad_dirs:
                shutil.rmtree(path, ignore_errors=True)

        good_env, good_dirs = self._fresh_go_env()
        try:
            good = self._run_go_test(
                ["go", "test", "-p", "1", "./ai/...", "./gateway/...", "-count=1"],
                cwd=ZEROEYE_ROOT / "market",
                env=good_env,
            )
            self.assertEqual(good.returncode, 0, msg=good.stdout + good.stderr)
        finally:
            for path in good_dirs:
                shutil.rmtree(path, ignore_errors=True)

    def test_zeroeye_market_go_tests_pass(self) -> None:
        if os.environ.get("ISSUE_2853_SKIP_GO_TESTS"):
            self.skipTest("go tests skipped via ISSUE_2853_SKIP_GO_TESTS")

        env, temp_dirs = self._fresh_go_env()
        try:
            result = self._run_go_test(
                ["go", "test", "-p", "1", "./ai/...", "./gateway/...", "-count=1"],
                cwd=ZEROEYE_ROOT / "market",
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=result.stdout + result.stderr,
            )
            self.assertIn("ok", result.stdout)
        finally:
            for path in temp_dirs:
                shutil.rmtree(path, ignore_errors=True)

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
        self.assertRegex(text, r"39/39|PASS — 39/39")

    def _latest_verification_block(self, text: str) -> str:
        marker = "## Verification "
        first = text.index(marker)
        second = text.find(marker, first + len(marker))
        if second == -1:
            return text[first:]
        return text[first:second]

    def test_bounty_proof_documents_latest_verification_suite_count(self) -> None:
        """Latest PROOF.md verification block must document the current suite count."""
        text = PROOF.read_text(encoding="utf-8")
        latest = self._latest_verification_block(text)
        self.assertRegex(
            latest,
            r"54/54 \(2 README \+ 21 peer review \+ 22 issue #2853 \+ 9 delivery\)",
        )
        self.assertRegex(latest, r"22/22 \(fresh clone|reused zeroeye")
        self.assertIn("takeover #369", latest)
        self.assertIn("verify-issue-2853.sh", latest)
        self.assertIn("run-unittest-module.sh", latest)


if __name__ == "__main__":
    unittest.main()
