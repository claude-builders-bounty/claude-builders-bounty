import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


from hooks import block_destructive
from hooks import install


class BlockDestructiveHookTests(unittest.TestCase):
    def run_hook(self, command, cwd="/workspace/project"):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": cwd,
        }
        output = io.StringIO()
        with redirect_stdout(output):
            with patch("sys.stdin", io.StringIO(json.dumps(payload))):
                exit_code = block_destructive.main()
        text = output.getvalue().strip()
        return exit_code, json.loads(text) if text else None

    def test_blocks_each_required_destructive_pattern_and_logs_it(self):
        commands = [
            "rm -rf ./build",
            "DROP TABLE users",
            "git push origin main --force",
            "TRUNCATE TABLE sessions",
            "DELETE FROM users",
        ]
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            with patch.dict(os.environ, {"CLAUDE_HOOK_LOG_PATH": str(log_path)}):
                for command in commands:
                    exit_code, result = self.run_hook(command)
                    self.assertEqual(exit_code, 0)
                    self.assertEqual(
                        result["hookSpecificOutput"]["permissionDecision"], "deny"
                    )
                    self.assertIn(command, result["hookSpecificOutput"]["permissionDecisionReason"])

            entries = [json.loads(line) for line in log_path.read_text().splitlines()]
            self.assertEqual(len(entries), len(commands))
            self.assertEqual([entry["attempted_command"] for entry in entries], commands)
            self.assertTrue(all(entry["project_path"] == "/workspace/project" for entry in entries))
            self.assertTrue(all(entry["timestamp"] for entry in entries))

    def test_allows_safe_commands_and_delete_with_where_without_output(self):
        for command in [
            "rm ./build/output.txt",
            "git push origin main",
            "DELETE FROM users WHERE id = 1",
            "python -m pytest",
        ]:
            exit_code, result = self.run_hook(command)
            self.assertEqual(exit_code, 0)
            self.assertIsNone(result)

    def test_blocks_force_variants_and_delete_before_a_semicolon(self):
        for command in [
            "git -C repo push --force-with-lease origin main",
            "DELETE FROM users; SELECT 1",
            "sudo rm -fr /tmp/cache",
        ]:
            exit_code, result = self.run_hook(command)
            self.assertEqual(exit_code, 0)
            self.assertEqual(
                result["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_installer_preserves_existing_settings_and_is_idempotent(self):
        source_dir = Path(__file__).resolve().parents[1] / "hooks"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "home"
            settings_path = home / "settings.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps(
                    {
                        "theme": "dark",
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Write",
                                    "hooks": [{"type": "command", "command": "echo keep"}],
                                }
                            ]
                        },
                    }
                )
            )

            install.install(home=home, source_dir=source_dir)
            install.install(home=home, source_dir=source_dir)

            self.assertTrue((home / "hooks" / "block_destructive.py").exists())
            settings = json.loads(settings_path.read_text())
            self.assertEqual(settings["theme"], "dark")
            self.assertEqual(len(settings["hooks"]["PreToolUse"]), 2)
            self.assertEqual(
                sum(
                    1
                    for group in settings["hooks"]["PreToolUse"]
                    for hook in group["hooks"]
                    if "block_destructive.py" in hook.get("command", "")
                ),
                1,
            )


if __name__ == "__main__":
    unittest.main()
