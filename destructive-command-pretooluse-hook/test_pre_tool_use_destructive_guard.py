import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).with_name("pre_tool_use_destructive_guard.py")
SETTINGS_PATH = Path(__file__).with_name("settings.example.json")


def load_hook():
    spec = importlib.util.spec_from_file_location("guard", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DestructiveGuardTests(unittest.TestCase):
    def test_blocks_required_dangerous_patterns(self):
        hook = load_hook()
        commands = [
            "rm -rf dist",
            "rm -fr /tmp/example",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE TABLE sessions'",
            "git push origin main --force",
            "git push -f origin main",
            "psql -c 'DELETE FROM users'",
        ]

        for command in commands:
            self.assertIsNotNone(hook.find_block_reason(command), command)

    def test_blocks_spacing_and_flag_variants(self):
        hook = load_hook()
        commands = [
            "rm -Rf ./cache",
            "rm -r -f ./cache",
            "psql -c 'drop    table users'",
            "mysql -e 'truncate sessions'",
            "git push --force=matching origin main",
            "psql -c 'DELETE\\nFROM users'",
        ]

        for command in commands:
            self.assertIsNotNone(hook.find_block_reason(command), command)

    def test_allows_normal_bash_commands(self):
        hook = load_hook()
        commands = [
            "git status",
            "rm build.log",
            "git push --force-with-lease origin main",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "echo safe",
        ]

        for command in commands:
            self.assertIsNone(hook.find_block_reason(command), command)

    def test_allows_force_like_non_push_and_where_variants(self):
        hook = load_hook()
        commands = [
            "git fetch --force origin main",
            "git push origin main --force-with-lease=refs/heads/main",
            "psql -c 'DELETE FROM users\\nWHERE id = 1'",
        ]

        for command in commands:
            self.assertIsNone(hook.find_block_reason(command), command)

    def test_non_bash_tool_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_hook(
                {
                    "tool_name": "Read",
                    "tool_input": {"file_path": "rm -rf nope"},
                    "cwd": str(tmp_path),
                },
                tmp_path,
            )

        self.assertEqual(result.stdout, "")
        self.assertEqual(result.returncode, 0)

    def test_denied_command_outputs_pretooluse_json_and_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git push origin main --force"},
                    "cwd": str(tmp_path),
                },
                tmp_path,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn(
                "overwrite remote history", hook_output["permissionDecisionReason"]
            )

            log_path = tmp_path / "blocked.log"
            entries = log_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(entries), 1)
            entry = json.loads(entries[0])
            self.assertEqual(entry["attempted_command"], "git push origin main --force")
            self.assertEqual(entry["project_path"], str(tmp_path))
            self.assertEqual(entry["blocked_pattern"], "git-force-push")

    def test_claude_project_dir_takes_precedence_for_log_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            project_path = tmp_path / "project-from-env"
            result = run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf dist"},
                    "cwd": str(tmp_path / "payload-cwd"),
                },
                tmp_path,
                {"CLAUDE_PROJECT_DIR": str(project_path)},
            )

            self.assertEqual(result.returncode, 0)
            entry = json.loads((tmp_path / "blocked.log").read_text(encoding="utf-8"))
            self.assertEqual(entry["project_path"], str(project_path))

    def test_settings_example_uses_pretooluse_bash_matcher(self):
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        pre_tool_use = settings["hooks"]["PreToolUse"]

        self.assertEqual(pre_tool_use[0]["matcher"], "Bash")
        self.assertEqual(pre_tool_use[0]["hooks"][0]["type"], "command")
        self.assertIn(
            "pre_tool_use_destructive_guard.py",
            pre_tool_use[0]["hooks"][0]["command"],
        )


def run_hook(payload, tmp_path, extra_env=None):
    env = os.environ.copy()
    env["CLAUDE_HOOKS_LOG_PATH"] = str(tmp_path / "blocked.log")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


if __name__ == "__main__":
    unittest.main()
