#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / "hooks" / "block_destructive_bash.py"


class BlockDestructiveBashHookTest(unittest.TestCase):
    def run_hook(self, event: dict, home: str, config: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = home
        if config is not None:
            env["DESTRUCTIVE_BASH_HOOK_CONFIG"] = str(config)
        return subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def bash_event(self, command: str) -> dict:
        return {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }

    def assert_blocked(self, result: subprocess.CompletedProcess[str], reason: str) -> None:
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(reason, output["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_normal_bash_commands(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(self.bash_event("ls && cat README.md && npm test"), home)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout, "")

    def test_allows_searching_for_dangerous_sql_text(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(self.bash_event("grep -R 'DROP TABLE' migrations/"), home)

        self.assertEqual(result.returncode, 0)

    def test_allows_echoing_dangerous_shell_text(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(self.bash_event("echo 'rm -rf ./dist'"), home)

        self.assertEqual(result.returncode, 0)

    def test_blocks_rm_rf_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(self.bash_event("rm -rf ./dist"), home)
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log = json.loads(log_path.read_text(encoding="utf-8").strip())

        self.assert_blocked(result, "recursive forced removal")
        self.assertEqual(log["command"], "rm -rf ./dist")
        self.assertEqual(log["project_path"], "/tmp/example-project")
        self.assertEqual(log["reason"], "recursive forced removal")
        self.assertIsNotNone(datetime.fromisoformat(log["timestamp"]))

    def test_blocks_rm_force_recursive_variants(self) -> None:
        variants = [
            "rm -fr ./dist",
            "rm -r -f ./dist",
            "rm -f -r ./dist",
            "sudo rm -rf ./dist",
            "command rm --recursive --force ./dist",
        ]
        for command in variants:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as home:
                result = self.run_hook(self.bash_event(command), home)
                self.assert_blocked(result, "recursive forced removal")

    def test_blocks_required_sql_patterns(self) -> None:
        destructive_commands = [
            "DROP TABLE users",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM audit_log'",
            "echo 'DROP TABLE users' | psql",
        ]
        for command in destructive_commands:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as home:
                result = self.run_hook(self.bash_event(command), home)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_delete_with_where_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(self.bash_event("psql -c 'DELETE FROM sessions WHERE id = 1'"), home)

        self.assertEqual(result.returncode, 0)

    def test_blocks_force_push(self) -> None:
        force_pushes = [
            "git push origin main --force-with-lease",
            "git push origin main -f",
            "git -C ../repo push origin main --force",
        ]
        for command in force_pushes:
            with self.subTest(command=command), tempfile.TemporaryDirectory() as home:
                result = self.run_hook(self.bash_event(command), home)

            self.assert_blocked(result, "forced git push")

    def test_custom_allow_rule_overrides_default_deny_rule(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            config = Path(home) / "hook-config.json"
            config.write_text(
                json.dumps({"allow": [{"name": "fixture cleanup", "pattern": r"^rm -rf \.pytest_cache$"}]}),
                encoding="utf-8",
            )
            result = self.run_hook(self.bash_event("rm -rf .pytest_cache"), home, config)

        self.assertEqual(result.returncode, 0)

    def test_ignores_non_bash_tools(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook({"tool_name": "Read", "tool_input": {"command": "rm -rf ."}}, home)

        self.assertEqual(result.returncode, 0)

    def test_installer_writes_hook_and_settings(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                ["python3", str(REPO_ROOT / "scripts" / "install_block_destructive_bash_hook.py")],
                text=True,
                capture_output=True,
                env={**os.environ, "HOME": home},
                check=False,
            )
            settings_path = Path(home) / ".claude" / "settings.json"
            hook_path = Path(home) / ".claude" / "hooks" / "block_destructive_bash.py"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(hook_path.exists())
            self.assertIn("PreToolUse", settings["hooks"])
            self.assertEqual(settings["hooks"]["PreToolUse"][0]["matcher"], "Bash")

    def test_installer_preserves_existing_hooks_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            settings_path = Path(home) / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps(
                    {
                        "theme": "dark",
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Read",
                                    "hooks": [{"type": "command", "command": "echo read"}],
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )

            for _ in range(2):
                result = subprocess.run(
                    ["python3", str(REPO_ROOT / "scripts" / "install_block_destructive_bash_hook.py")],
                    text=True,
                    capture_output=True,
                    env={**os.environ, "HOME": home},
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            pre_tool_use = settings["hooks"]["PreToolUse"]
            bash_blocks = [item for item in pre_tool_use if item["matcher"] == "Bash"]

            self.assertEqual(settings["theme"], "dark")
            self.assertEqual(pre_tool_use[0]["matcher"], "Read")
            self.assertEqual(len(bash_blocks), 1)
            self.assertEqual(len(bash_blocks[0]["hooks"]), 1)


if __name__ == "__main__":
    unittest.main()
