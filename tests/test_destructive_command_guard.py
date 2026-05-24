import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "destructive_command_guard.py"


def load_hook_module():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def run_hook(command, tmp_path):
    event = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/workspace/example",
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        env={"HOME": str(tmp_path)},
        check=False,
    )


class DestructiveCommandGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook_module()

    def test_blocks_rm_recursive_force_variants(self):
        self.assertTrue(self.hook.blocked_reason("rm -rf /tmp/build"))
        self.assertTrue(self.hook.blocked_reason("sudo rm -fr ./dist"))
        self.assertTrue(self.hook.blocked_reason("env FOO=1 rm -rf ./dist"))
        self.assertTrue(self.hook.blocked_reason("env -- rm -rf ./dist"))
        self.assertTrue(self.hook.blocked_reason("env -u FOO BAR=1 rm -Rf ./dist"))
        self.assertTrue(self.hook.blocked_reason("rm --recursive --force ./cache"))

    def test_blocks_sql_and_force_push_patterns(self):
        self.assertTrue(self.hook.blocked_reason("psql -c 'DROP TABLE users'"))
        self.assertTrue(self.hook.blocked_reason("mysql -e 'TRUNCATE TABLE sessions'"))
        self.assertTrue(self.hook.blocked_reason("git push --force origin main"))
        self.assertTrue(self.hook.blocked_reason("git -C repo push --force-with-lease origin main"))
        self.assertTrue(self.hook.blocked_reason("git -c safe.directory=* push -f origin main"))
        self.assertTrue(self.hook.blocked_reason("git --no-pager push -f origin main"))
        self.assertTrue(self.hook.blocked_reason("git push -f origin main"))
        self.assertTrue(self.hook.blocked_reason("psql -c 'DELETE FROM users'"))

    def test_allows_normal_bash_and_delete_with_where(self):
        self.assertIsNone(self.hook.blocked_reason("ls -la && npm test"))
        self.assertIsNone(self.hook.blocked_reason("rm -r ./build"))
        self.assertIsNone(self.hook.blocked_reason("git push origin main"))
        self.assertIsNone(self.hook.blocked_reason("git -C repo status --short"))
        self.assertIsNone(
            self.hook.blocked_reason("psql -c 'DELETE FROM users WHERE id = 1'")
        )

    def test_hook_outputs_denial_and_logs_blocked_attempt(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            result = run_hook("rm -rf /tmp/build", tmp_path)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm command", decision["permissionDecisionReason"])

            log_path = tmp_path / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text().strip())
            self.assertEqual(log_entry["command"], "rm -rf /tmp/build")
            self.assertEqual(log_entry["project_path"], "/workspace/example")

    def test_hook_allows_safe_command_without_output(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            result = run_hook("python3 -m unittest", tmp_path)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((tmp_path / ".claude" / "hooks" / "blocked.log").exists())


if __name__ == "__main__":
    unittest.main()
