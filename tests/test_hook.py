import json
import subprocess
import sys
import unittest
from pathlib import Path


HOOK = Path(__file__).parents[1] / ".claude" / "hooks" / "block-destructive.py"


def run_hook(command):
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


class HookTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        for command in (
            "rm -rf build",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE TABLE users'",
            "psql -c 'DELETE FROM users'",
        ):
            output = run_hook(command)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_safe_commands(self):
        self.assertIsNone(run_hook("npm test"))
        self.assertIsNone(run_hook("git status"))
        self.assertIsNone(run_hook("psql -c 'DELETE FROM users WHERE id = 1'"))


if __name__ == "__main__":
    unittest.main()
