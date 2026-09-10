import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "block_destructive_bash.py"
if not HOOK_PATH.exists():
    # The local draft keeps the hook under .claude/hooks; the published PR
    # places it at the repository root so the copy command is self-contained.
    HOOK_PATH = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
assert SPEC and SPEC.loader
HOOK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HOOK
SPEC.loader.exec_module(HOOK)


class DetectionTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self):
        for command in ("rm -rf /tmp/build", "rm -fr ./cache", "sudo rm -r -f ./cache"):
            self.assertIsNotNone(HOOK.detect_reason(command), command)

    def test_blocks_force_push(self):
        self.assertIsNotNone(HOOK.detect_reason("git push origin main --force"))
        self.assertIsNotNone(HOOK.detect_reason("git push -f origin main"))

    def test_blocks_destructive_sql(self):
        for command in (
            "DROP TABLE users",
            "TRUNCATE TABLE events",
            'psql -c "DELETE FROM users"',
            'sqlite3 app.db -e "DELETE FROM users;"',
        ):
            self.assertIsNotNone(HOOK.detect_reason(command), command)

    def test_allows_safe_commands_and_delete_with_where(self):
        for command in (
            "echo 'hello world'",
            "rm ./one-file.txt",
            "git push origin main",
            'psql -c "DELETE FROM users WHERE id = 1"',
            "npm test",
        ):
            self.assertIsNone(HOOK.detect_reason(command), command)


class ProcessTests(unittest.TestCase):
    def test_non_bash_tool_is_ignored(self):
        payload = {
            "tool_name": "Read",
            "cwd": "/tmp/project",
            "tool_input": {"command": "rm -rf /tmp/build"},
        }
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")

    def test_safe_input_is_silent(self):
        payload = {"cwd": "/tmp/project", "tool_input": {"command": "printf ok"}}
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(result.stdout, "")

    def test_blocked_input_returns_deny_and_writes_log(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {"cwd": "/tmp/project", "tool_input": {"command": "rm -rf /tmp/build"}}
            env = os.environ | {"HOME": home}
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(record["command"], "rm -rf /tmp/build")
            self.assertEqual(record["project_path"], "/tmp/project")
            self.assertTrue(record["timestamp"])


if __name__ == "__main__":
    unittest.main()
