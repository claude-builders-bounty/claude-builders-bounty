import subprocess
import sys
import unittest
from pathlib import Path

CURRENT_DIR = Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from guard import check_command

class TestSecurityGuard(unittest.TestCase):

    def test_rm_rf_variants_blocked(self):
        blocked_commands = [
            "rm -rf /",
            "rm -fr /var/log",
            "rm -r -f ./node_modules",
            "rm -R -f ./build",
            "rm -rfv dist/",
            "rm --recursive --force /tmp/test",
            "sudo rm -rf /etc"
        ]
        for cmd in blocked_commands:
            with self.subTest(cmd=cmd):
                res = check_command(cmd)
                self.assertIsNotNone(res, f"Expected '{cmd}' to be blocked")
                self.assertEqual(res["name"], "Recursive Force Removal")

    def test_safe_rm_allowed(self):
        allowed_commands = [
            "rm file.txt",
            "rm -f single_file.log",
            "rm -i old.txt",
            "rm --interactive=always temp.dat"
        ]
        for cmd in allowed_commands:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Expected '{cmd}' to be allowed")

    def test_git_force_push_blocked(self):
        blocked = [
            "git push --force",
            "git push origin main --force",
            "git push -f",
            "git push origin master -f",
            "git push origin main --force-with-lease"
        ]
        for cmd in blocked:
            with self.subTest(cmd=cmd):
                res = check_command(cmd)
                self.assertIsNotNone(res, f"Expected '{cmd}' to be blocked")
                self.assertEqual(res["name"], "Forced Git Push")

    def test_safe_git_push_allowed(self):
        allowed = [
            "git push",
            "git push origin main",
            "git push -u origin feat/branch",
            "git status",
            "git log -n 5"
        ]
        for cmd in allowed:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Expected '{cmd}' to be allowed")

    def test_sql_drop_table_blocked(self):
        blocked = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "sqlite3 db.sqlite 'DROP TABLE sessions;'",
            "psql -c 'DROP TABLE audit_logs'"
        ]
        for cmd in blocked:
            with self.subTest(cmd=cmd):
                res = check_command(cmd)
                self.assertIsNotNone(res, f"Expected '{cmd}' to be blocked")
                self.assertEqual(res["name"], "SQL Drop Table")

    def test_sql_truncate_blocked(self):
        blocked = [
            "TRUNCATE TABLE users;",
            "truncate users;",
            "psql -d test -c 'TRUNCATE TABLE orders;'"
        ]
        for cmd in blocked:
            with self.subTest(cmd=cmd):
                res = check_command(cmd)
                self.assertIsNotNone(res, f"Expected '{cmd}' to be blocked")
                self.assertEqual(res["name"], "SQL Truncate")

    def test_sql_delete_without_where_blocked(self):
        blocked = [
            "DELETE FROM users;",
            "delete from accounts",
            "DELETE FROM \"orders\";",
            "sqlite3 db.sqlite 'DELETE FROM logs;'"
        ]
        for cmd in blocked:
            with self.subTest(cmd=cmd):
                res = check_command(cmd)
                self.assertIsNotNone(res, f"Expected '{cmd}' to be blocked")
                self.assertEqual(res["name"], "Unbounded SQL Delete")

    def test_sql_delete_with_where_allowed(self):
        allowed = [
            "DELETE FROM users WHERE id = 42;",
            "delete from accounts where status = 'inactive'",
            "DELETE FROM logs WHERE created_at < NOW() - INTERVAL '30 days';"
        ]
        for cmd in allowed:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Expected '{cmd}' to be allowed")

    def test_innocuous_bash_commands_allowed(self):
        allowed = [
            "npm run test",
            "pytest tests/",
            "docker compose up -d",
            "cat README.md",
            "grep -rn 'TODO' src/",
            "echo 'rm -rf will not run'",
            "find . -name '*.py'"
        ]
        for cmd in allowed:
            with self.subTest(cmd=cmd):
                self.assertIsNone(check_command(cmd), f"Expected '{cmd}' to be allowed")

    def test_cli_execution_exit_codes(self):
        guard_path = Path(__file__).parent / "guard.py"
        
        # Test blocking command (exit code 2)
        proc_block = subprocess.run(
            [sys.executable, str(guard_path), "rm -rf /test"],
            capture_output=True,
            text=True
        )
        self.assertEqual(proc_block.returncode, 2)
        self.assertIn("[SECURITY BLOCK]", proc_block.stderr)
        self.assertIn("Recursive Force Removal", proc_block.stderr)

        # Test safe command (exit code 0)
        proc_allow = subprocess.run(
            [sys.executable, str(guard_path), "ls -la"],
            capture_output=True,
            text=True
        )
        self.assertEqual(proc_allow.returncode, 0)
        self.assertEqual(proc_allow.stderr, "")

    def test_claude_code_stdin_payload(self):
        import json
        guard_path = Path(__file__).parent / "guard.py"

        # 1. Test blocked command through stdin JSON
        payload_block = json.dumps({
            "tool": "Bash",
            "input": {"command": "rm -rf dist/"},
            "cwd": "/workspace/demo"
        })
        p1 = subprocess.run(
            [sys.executable, str(guard_path)],
            input=payload_block,
            capture_output=True,
            text=True
        )
        self.assertEqual(p1.returncode, 2)
        self.assertIn("Recursive Force Removal", p1.stderr)

        # 2. Test safe command through stdin JSON
        payload_safe = json.dumps({
            "tool": "Bash",
            "input": {"command": "git push origin main"},
            "cwd": "/workspace/demo"
        })
        p2 = subprocess.run(
            [sys.executable, str(guard_path)],
            input=payload_safe,
            capture_output=True,
            text=True
        )
        self.assertEqual(p2.returncode, 0)
        self.assertEqual(p2.stderr, "")

    def test_audit_log_content(self):
        from guard import LOG_FILE
        self.assertTrue(LOG_FILE.exists(), "Expected log file to exist")
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("BLOCKED (Recursive Force Removal)", content)
        self.assertIn("cwd:", content)


if __name__ == "__main__":
    unittest.main()
