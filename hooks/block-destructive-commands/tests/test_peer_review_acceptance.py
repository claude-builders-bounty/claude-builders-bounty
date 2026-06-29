#!/usr/bin/env python3
"""Peer-review acceptance cases for bounty #3 destructive-command hook."""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_PATH = HOOK_DIR / "pre-tool-use.py"
TARGET_ISSUE = 3
TARGET_PR = 2556


def load_hook_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def resolve_branch_diff_base_ref() -> str:
    """Pick a merge-base ref that exists locally (CI shallow clones omit main)."""
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if github_base:
        candidates.extend((github_base, f"origin/{github_base}"))
    candidates.extend(("main", "origin/main", "master", "origin/master"))
    for ref in candidates:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return ref
    raise RuntimeError(
        "no git base ref found for branch diff scope check; "
        "fetch the default branch (e.g. git fetch origin main:main) before running tests"
    )


def list_branch_changed_files(base_ref: str) -> list[str]:
    """List paths changed on HEAD since base_ref (needs full git history for ... syntax)."""
    triple_dot = subprocess.run(
        ["git", "diff", f"{base_ref}...HEAD", "--name-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if triple_dot.returncode == 0:
        return [line.strip() for line in triple_dot.stdout.splitlines() if line.strip()]

    raise RuntimeError(
        f"git diff {base_ref}...HEAD failed ({triple_dot.stderr.strip()}); "
        "use fetch-depth: 0 in CI checkout so merge-base exists"
    )


class PeerReviewAcceptanceTests(unittest.TestCase):
    """Maps bounty #3 acceptance criteria to repo artifacts and CLI behavior."""

    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook_module()

    def test_required_destructive_patterns_block(self):
        blocked = (
            "rm -rf /tmp",
            "rm --recursive --force /tmp",
            "rm --recursive=always --force /srv",
            'env bash -lc "rm --recursive --force /tmp"',
            "DROP TABLE users",
            "git push --force origin main",
            "TRUNCATE sessions",
            "DELETE FROM users",
            "sh -c 'DROP TABLE users'",
            "sudo DROP TABLE users",
            'docker exec db psql -c "DROP TABLE users"',
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(
                    self.hook.check_command(command),
                    f"expected block: {command!r}",
                )

    def test_is_rm_rf_gnu_long_options_in_hook_source(self):
        """Peer review: is_rm_rf must recognize GNU --recursive/--force long flags."""
        text = HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("def is_rm_rf(", text)
        self.assertIn("--recursive", text)
        self.assertIn("--force", text)
        self.assertTrue(self.hook.is_rm_rf("rm --recursive=always --force /tmp"))
        self.assertFalse(self.hook.is_rm_rf("rm --recursive /tmp"))

    def test_safe_variants_allow(self):
        allowed = (
            "git status",
            "rm -f file.txt",
            "rm --recursive build",
            "git push --force-with-lease origin main",
            'grep "DELETE FROM users" schema.sql',
            "npm run truncate-logs",
            "echo DROP TABLE users",
            "DELETE FROM users WHERE id=1",
            'find . -name "*.sql" | xargs grep DROP TABLE',
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(
                    self.hook.check_command(command),
                    f"expected allow: {command!r}",
                )

    def test_hook_script_uses_official_schema(self):
        self.assertTrue(HOOK_PATH.is_file())
        text = HOOK_PATH.read_text(encoding="utf-8")
        self.assertIn("PreToolUse", text)
        self.assertIn("hookSpecificOutput", text)
        self.assertIn("permissionDecision", text)
        self.assertIn("blocked.log", text)

    def test_install_script_supports_two_command_setup(self):
        install = HOOK_DIR / "install.sh"
        self.assertTrue(install.is_file())
        text = install.read_text(encoding="utf-8")
        self.assertIn("PreToolUse", text)
        self.assertIn("settings.json", text)
        self.assertIn("--uninstall", text)

    def test_readme_documents_install_and_blocked_log(self):
        readme = (HOOK_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("git clone", readme)
        self.assertIn("install.sh", readme)
        self.assertIn("blocked.log", readme)
        self.assertIn("hookSpecificOutput", readme)

    def test_readme_documents_operator_tradeoffs(self):
        readme = (HOOK_DIR / "README.md").read_text(encoding="utf-8")
        self.assertIn("Silent failures on malformed input or internal errors", readme)
        self.assertIn("fails open", readme)
        self.assertIn("Regex and substring matching limits", readme)
        self.assertIn("x=rm; $x -rf /", readme)

    def test_readme_documents_minimum_regression_test_floor(self):
        """README must not under-report regression coverage (stale counts fail peer review)."""
        readme = (HOOK_DIR / "README.md").read_text(encoding="utf-8")
        tests_dir = HOOK_DIR / "tests"
        total = sum(
            len(re.findall(r"^\s*def test_", path.read_text(encoding="utf-8"), flags=re.MULTILINE))
            for path in tests_dir.glob("test_*.py")
        )
        self.assertGreaterEqual(total, 150)
        match = re.search(r"(\d+)\+\s*regression tests", readme)
        self.assertIsNotNone(match, msg="README must document N+ regression tests")
        documented = int(match.group(1))
        self.assertGreaterEqual(
            documented,
            150,
            msg=f"README regression floor {documented}+ is below suite size {total}",
        )

    def test_documented_regex_evasion_limitation(self):
        """Indirect destructive commands documented in README are not blocked."""
        self.assertIsNone(self.hook.check_command("x=rm; $x -rf /"))

    def test_ci_workflow_uses_pull_request_not_target(self):
        workflow = REPO_ROOT / ".github/workflows/test-block-destructive-commands.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertNotIn("pull_request_target:", text)

    def test_settings_json_registers_bash_pretooluse_hook(self):
        settings = json.loads((HOOK_DIR / "settings.json").read_text(encoding="utf-8"))
        pre_tool_use = settings["hooks"]["PreToolUse"]
        bash_hooks = [item for item in pre_tool_use if item.get("matcher") == "Bash"]
        self.assertTrue(bash_hooks)
        commands = [
            hook.get("command", "")
            for item in bash_hooks
            for hook in item.get("hooks", [])
        ]
        self.assertTrue(any("pre-tool-use.py" in command for command in commands))

    def test_ci_workflow_runs_unified_validation(self):
        workflow = REPO_ROOT / ".github/workflows/test-block-destructive-commands.yml"
        self.assertTrue(workflow.is_file())
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("run-ci-checks.sh", text)
        self.assertIn("hooks/block-destructive-commands", text)

    def test_ci_workflow_fetches_full_git_history(self):
        """Branch scope check needs merge-base; shallow checkout breaks peer review."""
        workflow = REPO_ROOT / ".github/workflows/test-block-destructive-commands.yml"
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("fetch-depth: 0", text)

    def test_makefile_exposes_test_and_ci_validate(self):
        makefile = (HOOK_DIR / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test:", makefile)
        self.assertIn("ci-validate:", makefile)
        self.assertIn("run-ci-checks.sh", makefile)

    def test_repo_root_makefile_exposes_test_and_ci_validate(self):
        makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("test:", makefile)
        self.assertIn("ci-validate:", makefile)
        self.assertIn("run-ci-checks.sh", makefile)

    def test_package_json_exposes_npm_test_entry_point(self):
        package = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn("run-ci-checks.sh", package["scripts"]["test"])
        self.assertIn("run-ci-checks.sh", package["scripts"]["test:ci"])

    def test_run_ci_checks_script_exists_and_is_executable(self):
        script = HOOK_DIR / "tests/run-ci-checks.sh"
        self.assertTrue(script.is_file())
        self.assertTrue(script.stat().st_mode & 0o111)

    def test_run_ci_checks_guards_attribution_and_peer_review(self):
        script = (HOOK_DIR / "tests/run-ci-checks.sh").read_text(encoding="utf-8")
        self.assertIn("peer review acceptance tests passed", script)
        self.assertIn("git log -1 --format='%B'", script)
        self.assertIn("Ran ${peer_review_tests} tests — OK", script)
        self.assertIn("Forbidden agent attribution trailer found in HEAD commit message", script)

    def test_bounty_acceptance_suite_exists(self):
        bounty_test = HOOK_DIR / "tests/test_bounty_acceptance.py"
        self.assertTrue(bounty_test.is_file())
        text = bounty_test.read_text(encoding="utf-8")
        self.assertIn("rm -rf /tmp", text)
        self.assertIn("git push --force-with-lease", text)

    def test_hook_cli_blocks_destructive_command(self):
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "rm -rf /tmp/build"},
                        "cwd": "/workspace/demo",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_file.is_file())
            self.assertIn("rm -rf /tmp/build", log_file.read_text(encoding="utf-8"))
            self.assertIn("/workspace/demo", log_file.read_text(encoding="utf-8"))

    def test_hook_log_sanitizes_injection_attempts(self):
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "rm -rf /\n[FAKE] injected"},
                        "cwd": "/workspace/demo\n[FAKE] path",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            log_text = (
                Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            ).read_text(encoding="utf-8")
            self.assertEqual(len(log_text.strip().splitlines()), 1)
            self.assertNotIn("\n[FAKE]", log_text)
            self.assertIn("rm -rf /\\n[FAKE] injected", log_text)
            self.assertIn("/workspace/demo\\n[FAKE] path", log_text)

    def test_hook_cli_allows_safe_command(self):
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(
                    {
                        "tool_name": "Bash",
                        "tool_input": {"command": "git status"},
                        "cwd": "/workspace/demo",
                    }
                ),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")
            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            self.assertFalse(log_file.exists())

    def test_branch_diff_scoped_to_hook_only(self):
        """Peer review: PR diff must not include unrelated paths (e.g. internal/exporter)."""
        base_ref = resolve_branch_diff_base_ref()
        changed = list_branch_changed_files(base_ref)

        allowed_prefixes = (
            "hooks/block-destructive-commands/",
            ".github/workflows/test-block-destructive-commands.yml",
            "package.json",
            "Makefile",
            ".gitignore",
        )
        for path in changed:
            self.assertFalse(
                path.startswith("internal/"),
                f"unrelated path in PR diff: {path!r}",
            )
            self.assertTrue(
                any(path == prefix or path.startswith(prefix) for prefix in allowed_prefixes),
                f"unexpected path in PR diff: {path!r}",
            )

    def test_peer_review_deliverable_has_committed_hook_source(self):
        """Peer review gate: fleet sessions must commit hook source, not docs-only proof."""
        base_ref = resolve_branch_diff_base_ref()
        result = subprocess.run(
            ["git", "diff", f"{base_ref}...HEAD", "--", str(HOOK_PATH.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        added_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        self.assertGreater(
            len(added_lines),
            0,
            msg=(
                f"peer_review_not_passed: committed pre-tool-use.py additions required "
                f"for issue #{TARGET_ISSUE} / PR #{TARGET_PR}"
            ),
        )
        combined = "\n".join(added_lines)
        self.assertIn(
            "hookSpecificOutput",
            combined,
            msg="peer review requires official Claude hook denial schema in committed source",
        )


if __name__ == "__main__":
    unittest.main()
