import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


class BlockDestructiveBashTest(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf /tmp/build",
            "rm -fr node_modules",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "git push --force origin main",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertTrue(hook.blocked_reason(command))

    def test_allows_normal_commands_and_scoped_delete(self):
        allowed = [
            "npm test",
            "rm -r ./dist",
            "git push origin main",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(hook.blocked_reason(command))

    def test_hook_denies_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["USERPROFILE"] = tmp
            env["HOME"] = tmp

            event = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ./dist"},
                "cwd": str(ROOT),
            }

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(event),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )

            output = json.loads(result.stdout)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn(
                "recursive force deletion",
                output["hookSpecificOutput"]["permissionDecisionReason"],
            )

            log = Path(tmp) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log.exists())
            self.assertIn("rm -rf ./dist", log.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

