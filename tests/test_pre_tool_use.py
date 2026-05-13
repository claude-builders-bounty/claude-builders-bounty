from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "block-destructive" / "pre-tool-use.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pre_tool_use_hook", HOOK_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load hook module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HookLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_rm_rf_is_blocked(self) -> None:
        decision = self.module.inspect_command("rm -rf /tmp/demo")
        self.assertIsNotNone(decision)
        self.assertIn("rm -rf", decision.reason)

    def test_git_push_force_short_flag_is_blocked(self) -> None:
        decision = self.module.inspect_command("git push -f origin main")
        self.assertIsNotNone(decision)
        self.assertIn("git push --force", decision.reason)

    def test_delete_with_where_is_allowed(self) -> None:
        decision = self.module.inspect_command('psql -c "DELETE FROM users WHERE id = 1"')
        self.assertIsNone(decision)

    def test_echoing_sql_text_is_allowed(self) -> None:
        decision = self.module.inspect_command('echo "DROP TABLE users"')
        self.assertIsNone(decision)


class HookProcessTests(unittest.TestCase):
    def run_hook(self, payload: dict) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                ["python3", str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            return result.returncode, result.stdout.strip(), log_text

    def test_safe_command_has_no_output(self) -> None:
        rc, stdout, log_text = self.run_hook(
            {
                "tool_name": "Bash",
                "cwd": "/tmp/project",
                "tool_input": {"command": "echo safe"},
            }
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_delete_without_where_is_logged_and_denied(self) -> None:
        rc, stdout, log_text = self.run_hook(
            {
                "tool_name": "Bash",
                "cwd": "/tmp/project",
                "tool_input": {"command": 'psql -c "DELETE FROM users;"'},
            }
        )
        self.assertEqual(rc, 0)
        payload = json.loads(stdout)
        hook_output = payload["hookSpecificOutput"]
        self.assertEqual(hook_output["permissionDecision"], "deny")
        self.assertIn("DELETE FROM without WHERE", hook_output["permissionDecisionReason"])
        lines = log_text.strip().splitlines()
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["project_path"], "/tmp/project")
        self.assertIn("DELETE FROM users", entry["command"])

    def test_non_bash_events_pass_through(self) -> None:
        rc, stdout, log_text = self.run_hook(
            {
                "tool_name": "Read",
                "cwd": "/tmp/project",
                "tool_input": {"file_path": "README.md"},
            }
        )
        self.assertEqual(rc, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")


if __name__ == "__main__":
    unittest.main()
