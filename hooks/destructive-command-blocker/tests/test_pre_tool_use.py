import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "pre_tool_use.py"


spec = importlib.util.spec_from_file_location("pre_tool_use", HOOK)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command, "cwd": "/tmp/project"},
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


class PreToolUseHookTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self):
        self.assertEqual(module.blocked_reason("rm -rf build")[0], "rm -rf")
        self.assertEqual(module.blocked_reason("rm -fr build")[0], "rm -rf")
        self.assertEqual(module.blocked_reason("echo ok && rm -r -f build")[0], "rm -rf")

    def test_blocks_sql_destructive_commands(self):
        self.assertEqual(module.blocked_reason("DROP TABLE users")[0], "DROP TABLE")
        self.assertEqual(module.blocked_reason("truncate table sessions")[0], "TRUNCATE")
        self.assertEqual(module.blocked_reason("DELETE FROM users")[0], "DELETE FROM without WHERE")
        self.assertIsNone(module.blocked_reason("DELETE FROM users WHERE id = 1"))

    def test_blocks_force_push_variants(self):
        self.assertEqual(module.blocked_reason("git push --force origin main")[0], "git push --force")
        self.assertEqual(module.blocked_reason("git push -f origin main")[0], "git push --force")
        self.assertEqual(module.blocked_reason("git push --force-with-lease")[0], "git push --force")

    def test_allows_normal_commands(self):
        self.assertIsNone(module.blocked_reason("git status"))
        self.assertIsNone(module.blocked_reason("rm -r build"))
        self.assertIsNone(module.blocked_reason("SELECT * FROM users"))

    def test_hook_returns_block_decision_for_dangerous_command(self):
        result = run_hook("DROP TABLE users")
        self.assertEqual(result.returncode, 2)
        body = json.loads(result.stdout)
        self.assertEqual(body["decision"], "block")
        self.assertIn("DROP TABLE", body["reason"])

    def test_hook_allows_non_bash_payload(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
