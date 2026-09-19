import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("guard", HERE / "guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def test_blocked_commands(self):
        commands = ["rm -rf build", "rm -fr build", "rm -r -f build", "rm --recursive --force build",
                    "sudo rm -Rf build", "/bin/rm -rf build", "echo ok && rm -rf build",
                    "sudo -u root rm -rf build", "env -u TEMP rm -rf build",
                    "echo ok\nrm -rf build", "bash -c 'rm -rf build'", "eval 'rm -rf build'",
                    "git push --force origin main", "git -C app push origin main -f",
                    "git push --force-with-lease", "git push origin +main",
                    "DROP TABLE users", "TRUNCATE TABLE users", "DELETE FROM users",
                    'sqlite3 db.sqlite "DROP TABLE users;"',
                    'psql -c "DELETE FROM users RETURNING \'WHERE\';"',
                    'psql -c "DELETE FROM users /* WHERE id=1 */;"',
                    'psql -c "DELETE FROM users RETURNING (SELECT id FROM x WHERE id=1);"',
                    'psql -c "DELETE FROM users WHERE id=1; DELETE FROM secrets;"',
                    'echo "TRUNCATE users" | psql', 'psql <<SQL\nDROP TABLE users;\nSQL']
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.reason(command))

    def test_normal_commands(self):
        commands = ["npm test", "git status", "git push origin main", "rm file.txt", "rm -r build",
                    "rm -- -rf", "echo 'rm -rf build'", "printf '%s' 'git push --force'",
                    'psql -c "DELETE FROM users WHERE id=42;"',
                    'psql -c "SELECT \'DROP TABLE users\';"', "grep 'DELETE FROM' schema.sql"]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.reason(command))

    def run_hook(self, home, payload):
        env = dict(os.environ, HOME=home, USERPROFILE=home)
        result = subprocess.run([sys.executable, str(HERE / "guard.py")],
                                input=json.dumps(payload), capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def test_protocol_and_log(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf example"}, "cwd": "/work/project"}
            result = self.run_hook(home, payload)
            decision = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            log = Path(home) / ".claude/hooks/blocked.log"
            record = json.loads(log.read_text())
            self.assertEqual(record["command"], payload["tool_input"]["command"])
            self.assertEqual(record["project_path"], payload["cwd"])
            self.assertIn("+00:00", record["timestamp"])
            self.run_hook(home, payload)
            self.assertEqual(len(log.read_text().splitlines()), 2)

    def test_normal_and_other_tool_silent(self):
        with tempfile.TemporaryDirectory() as home:
            for payload in [{"tool_name": "Read"}, {"tool_name": "Bash", "tool_input": {"command": "git status"}}]:
                self.assertEqual(self.run_hook(home, payload).stdout, "")
            self.assertFalse((Path(home) / ".claude/hooks/blocked.log").exists())

    def test_bad_input_denied(self):
        with tempfile.TemporaryDirectory() as home:
            for payload in [[], {"tool_name": "Bash", "tool_input": None}]:
                result = self.run_hook(home, payload)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_log_failure_still_denies(self):
        with tempfile.TemporaryDirectory() as home:
            (Path(home) / ".claude").write_text("not a directory")
            result = self.run_hook(home, {"tool_name": "Bash", "tool_input": {"command": "rm -rf build"}})
            decision = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("could not be written", decision["permissionDecisionReason"])

    def test_install_preserves_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as home:
            root = Path(home) / ".claude"
            root.mkdir()
            settings = root / "settings.json"
            previous = {"permissions": {"deny": ["Bash(curl *)"]}, "hooks": {"Stop": [{"hooks": []}]}}
            settings.write_text(json.dumps(previous))
            env = dict(os.environ, HOME=home, USERPROFILE=home)
            for _ in range(2):
                subprocess.run([sys.executable, str(HERE / "install.py")], env=env, check=True, capture_output=True)
            data = json.loads(settings.read_text())
            self.assertEqual(data["permissions"], previous["permissions"])
            self.assertEqual(data["hooks"]["Stop"], previous["hooks"]["Stop"])
            self.assertEqual(len(data["hooks"]["PreToolUse"]), 1)
            self.assertEqual(len(list(root.glob("settings.json.backup-*"))), 1)
            self.assertTrue((root / "hooks/destructive-guard.py").exists())

    def test_install_rejects_invalid_json_without_overwrite(self):
        with tempfile.TemporaryDirectory() as home:
            root = Path(home) / ".claude"
            root.mkdir()
            settings = root / "settings.json"
            settings.write_text("invalid json")
            result = subprocess.run([sys.executable, str(HERE / "install.py")],
                                    env=dict(os.environ, HOME=home, USERPROFILE=home), capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(settings.read_text(), "invalid json")


if __name__ == "__main__":
    unittest.main()
