#!/usr/bin/env python3
import unittest
import subprocess
import json
import os

HOOK_PATH = "./pre-tool-use.py"
LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_PATH = os.path.join(LOG_DIR, "blocked.log")

class TestSecurityHook(unittest.TestCase):
    
    def setUp(self):
        os.chmod(HOOK_PATH, 0o755)
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
            
    def run_hook(self, input_json):
        process = subprocess.Popen(
            [HOOK_PATH],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=json.dumps(input_json))
        return process.returncode, stdout, stderr

    def test_allow_safe_commands(self):
        safe_cases = [
            {"tool_name": "Bash", "tool_input": {"command": "ls -la"}},
            {"tool_name": "Bash", "tool_input": {"command": "git push origin main"}},
            {"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users WHERE id = 5"}},
            {"tool_name": "Bash", "tool_input": {"command": "echo 'hello world'"}},
            {"tool_name": "Bash", "tool_input": {"command": "rm -f file.txt"}}
        ]
        for case in safe_cases:
            code, stdout, stderr = self.run_hook(case)
            self.assertEqual(code, 0, f"Failed for safe case: {case}")
            self.assertEqual(json.loads(stdout), case)
            self.assertEqual(stderr, "")

    def test_block_rm_rf(self):
        input_data = {"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/my-app"}}
        code, stdout, stderr = self.run_hook(input_data)
        self.assertEqual(code, 2)
        self.assertIn("rm -rf pattern detected", stderr)
        self.assertTrue(os.path.exists(LOG_PATH))
        with open(LOG_PATH, "r") as f:
            log_content = f.read()
            self.assertIn("rm -rf pattern detected", log_content)
            self.assertIn("rm -rf /tmp/my-app", log_content)

    def test_block_drop_table(self):
        input_data = {"tool_name": "Bash", "tool_input": {"command": "DROP TABLE users;"}}
        code, stdout, stderr = self.run_hook(input_data)
        self.assertEqual(code, 2)
        self.assertIn("DROP TABLE pattern detected", stderr)

    def test_block_git_force_push(self):
        input_data = {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}}
        code, stdout, stderr = self.run_hook(input_data)
        self.assertEqual(code, 2)
        self.assertIn("git push --force pattern detected", stderr)
        
        input_data_short = {"tool_name": "Bash", "tool_input": {"command": "git push -f origin main"}}
        code, stdout, stderr = self.run_hook(input_data_short)
        self.assertEqual(code, 2)

    def test_block_truncate(self):
        input_data = {"tool_name": "Bash", "tool_input": {"command": "TRUNCATE TABLE logs;"}}
        code, stdout, stderr = self.run_hook(input_data)
        self.assertEqual(code, 2)
        self.assertIn("TRUNCATE pattern detected", stderr)

    def test_block_delete_without_where(self):
        input_data = {"tool_name": "Bash", "tool_input": {"command": "DELETE FROM users;"}}
        code, stdout, stderr = self.run_hook(input_data)
        self.assertEqual(code, 2)
        self.assertIn("DELETE FROM without WHERE clause detected", stderr)

if __name__ == "__main__":
    unittest.main()
