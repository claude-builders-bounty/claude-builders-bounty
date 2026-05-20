import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "block-dangerous-bash.py"


spec = importlib.util.spec_from_file_location("block_dangerous_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def payload(command):
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }


class DestructiveCommandGuardTest(unittest.TestCase):
    def test_allows_normal_commands(self):
        result = hook.evaluate(payload("npm test && git status"))
        self.assertIsNone(result)

    def test_blocks_rm_rf_variants(self):
        for command in ("rm -rf dist", "rm -fr dist", "rm -r -f dist", "rm --recursive --force dist"):
            with self.subTest(command=command):
                self.assertEqual(hook.find_block_reason(command), "rm -rf")

    def test_blocks_forced_git_push(self):
        for command in ("git push --force origin main", "git push -f", "git push --force-with-lease"):
            with self.subTest(command=command):
                self.assertEqual(hook.find_block_reason(command), "forced git push")

    def test_blocks_dangerous_sql(self):
        blocked = (
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE sessions'",
            "sqlite3 app.db 'DELETE FROM sessions'",
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.find_block_reason(command))

    def test_allows_delete_with_where(self):
        self.assertIsNone(hook.find_block_reason("sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'"))

    def test_denied_command_is_logged(self):
        with tempfile.TemporaryDirectory() as config_home:
            old_config_home = os.environ.get("CLAUDE_CONFIG_HOME")
            os.environ["CLAUDE_CONFIG_HOME"] = config_home
            try:
                result = hook.evaluate(payload("rm -rf build"))
                output = result["hookSpecificOutput"]
                self.assertEqual(output["permissionDecision"], "deny")

                log_path = Path(config_home) / "hooks" / "blocked.log"
                self.assertTrue(log_path.exists())
                entry = json.loads(log_path.read_text(encoding="utf-8").strip())
                self.assertEqual(entry["command"], "rm -rf build")
                self.assertEqual(entry["project_path"], "/tmp/example-project")
            finally:
                if old_config_home is None:
                    os.environ.pop("CLAUDE_CONFIG_HOME", None)
                else:
                    os.environ["CLAUDE_CONFIG_HOME"] = old_config_home

    def test_cli_returns_pretooluse_decision_json(self):
        process = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload("git push --force")).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        output = json.loads(process.stdout)
        self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_cli_prints_nothing_for_safe_commands(self):
        process = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload("npm test")).encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        self.assertEqual(process.stdout, b"")


if __name__ == "__main__":
    unittest.main()
