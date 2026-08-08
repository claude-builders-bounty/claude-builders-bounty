from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block-destructive.py"
SETTINGS = ROOT / ".claude" / "settings.json"


def run_hook(command: str, *, cwd: str = "/tmp/example") -> tuple[dict, str]:
    with tempfile.TemporaryDirectory() as temp_dir:
        env = os.environ.copy()
        env["CLAUDE_HOOK_LOG"] = str(Path(temp_dir) / "blocked.log")
        event = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd})
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=event,
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        log = Path(env["CLAUDE_HOOK_LOG"])
        return (json.loads(result.stdout) if result.stdout.strip() else {}, log.read_text(encoding="utf-8") if log.exists() else "")


class BlockDestructiveHookTests(unittest.TestCase):
    def test_rm_rf_is_denied_and_logged(self) -> None:
        response, log = run_hook("rm -rf ./build")
        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn('"command": "rm -rf ./build"', log)
        self.assertIn('"project_path": "/tmp/example"', log)

    def test_other_destructive_patterns_are_denied(self) -> None:
        for command in (
            "DROP TABLE users",
            "git push origin main --force",
            "TRUNCATE TABLE sessions",
            "psql -c 'DELETE FROM users'",
        ):
            with self.subTest(command=command):
                response, _ = run_hook(command)
                self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_delete_with_where_is_allowed(self) -> None:
        response, log = run_hook("psql -c \"DELETE FROM users WHERE id = 1\"")
        self.assertEqual(response, {})
        self.assertEqual(log, "")

    def test_normal_commands_are_allowed(self) -> None:
        response, log = run_hook("git status && npm test")
        self.assertEqual(response, {})
        self.assertEqual(log, "")

    def test_malformed_input_fails_open(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")

    def test_settings_wire_user_hook_for_bash_and_powershell(self) -> None:
        settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
        matcher = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(matcher["matcher"], "Bash|PowerShell")
        command = matcher["hooks"][0]["command"]
        self.assertIn("$HOME/.claude/hooks/block-destructive.py", command)


if __name__ == "__main__":
    unittest.main()
