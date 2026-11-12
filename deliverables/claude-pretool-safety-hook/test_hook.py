#!/usr/bin/env python3
"""Offline tests for the Claude Code destructive Bash hook."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
HOOK = Path(__file__).with_name("block_destructive.py")

class HookTests(unittest.TestCase):
    def run_hook(self, command, home=None, cwd="/tmp/project"):
        env = os.environ.copy()
        if home:
            env["HOME"] = str(home)
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd}
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, env=env, check=True)
        return json.loads(result.stdout)
    def test_blocks_recursive_force_delete_variants(self):
        for command in ("rm -rf /tmp/data", "rm -fr /tmp/data", "rm -r -f /tmp/data", "rm --recursive --force /tmp/data", "sudo rm -rf /tmp/data", "env FOO=bar rm -rf /tmp/data"):
            with self.subTest(command=command):
                self.assertEqual(self.run_hook(command)["hookSpecificOutput"]["permissionDecision"], "deny")
    def test_blocks_force_push_variants(self):
        for command in ("git push --force origin main", "git push -f origin main", "git push --force-with-lease origin main", "sudo git push origin main --force"):
            with self.subTest(command=command):
                self.assertEqual(self.run_hook(command)["hookSpecificOutput"]["permissionDecision"], "deny")
    def test_blocks_destructive_sql(self):
        for command in ("sqlite3 app.db 'DROP TABLE users;'", "psql -c 'TRUNCATE TABLE sessions;'", "psql -c 'DELETE FROM users;'", "mysql -e 'delete from accounts'"):
            with self.subTest(command=command):
                self.assertEqual(self.run_hook(command)["hookSpecificOutput"]["permissionDecision"], "deny")
    def test_allows_safe_commands(self):
        for command in ("ls -la", "git status", "git push origin feature", "rm file.txt", "rm -i old.txt", "npm test", "psql -c 'DELETE FROM users WHERE id = 7;'", "psql -c 'SELECT * FROM users;'", "echo 'DELETE FROM users'"):
            with self.subTest(command=command):
                self.assertEqual(self.run_hook(command), {})
    def test_blocks_and_logs_required_fields(self):
        with tempfile.TemporaryDirectory() as home:
            output = self.run_hook("rm -rf /tmp/important", home=home)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            log = Path(home) / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            self.assertTrue(record["timestamp"])
            self.assertEqual(record["command"], "rm -rf /tmp/important")
            self.assertEqual(record["project_path"], "/tmp/project")
    def test_ignores_non_bash_tools(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}}
        result = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout), {})

if __name__ == "__main__":
    unittest.main(verbosity=2)
