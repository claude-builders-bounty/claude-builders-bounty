import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("guard", HERE / "destructive_guard.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)


class CommandTests(unittest.TestCase):
    def test_destructive_commands(self):
        cases = [
            "rm -rf /tmp/example", "rm -fr /tmp/example", "rm -r -f /tmp/example",
            "rm --recursive --force /tmp/example", "/bin/rm -Rf /tmp/example",
            "rm /tmp/example -rf", "sudo -u root rm -rf /tmp/example",
            "env MODE=test command rm -rf /tmp/example", "true && rm -rf /tmp/example",
            "false || rm -rf /tmp/example", "pwd; rm -rf /tmp/example",
            "pwd\nrm -rf /tmp/example", "(rm -rf /tmp/example)",
            "if true; then rm -rf /tmp/example; fi", "r'm' -rf /tmp/example",
            "rm -r\\\nf /tmp/example", "bash -lc 'rm -rf /tmp/example'",
            "sh -c 'git push --force'", 'eval "rm -rf /tmp/example"',
            'echo "$(rm -rf /tmp/example)"', "echo `rm -rf /tmp/example`",
            'echo "\'$(rm -rf /tmp/example)"', "X=$(git push --force)",
            "git push --force origin main", "git push -f origin main",
            "git -C /tmp/repo push --force", "git -c core.foo=true push -vf",
            "git push --force-with-lease origin main", "git push --force-with-lease=main:abc",
            "git push origin +HEAD:main", "DROP TABLE users", "drop table users",
            'psql -c "DROP TABLE users"', 'mysql -e "TRUNCATE TABLE users"',
            'sqlite3 db.sqlite "DELETE FROM users"',
            'psql -c "DELETE FROM users; SELECT * FROM users WHERE id=1"',
            'psql -c "DELETE FROM users WHERE id=1; DELETE FROM sessions"',
            'psql -c "DELETE FROM users /* WHERE id=1 */"',
            'psql -c "DELETE FROM users -- WHERE id=1"',
            'psql -c "DELETE FROM users RETURNING \'WHERE\'"',
            'psql -c "DELETE FROM users RETURNING (SELECT id FROM x WHERE id=1)"',
            'psql -c "DROP/* comment */TABLE users"',
            'echo "DELETE FROM users" | psql',
            'printf "%s\\n" "TRUNCATE users" | mysql',
            "psql <<'SQL'\nDELETE FROM users;\nSQL\n",
            "psql <<SQL\nDROP TABLE users;\nSQL\n",
            "cat <<EOF\n$(rm -rf /tmp/example)\nEOF\n",
            "echo '<<EOF'\nrm -rf /tmp/example",
            "echo tag#suffix; rm -rf /tmp/example",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command))

    def test_ordinary_commands(self):
        cases = [
            "ls -la", "pwd", "npm test", "python3 -m unittest discover",
            "git status", "git push origin main", "git fetch --force",
            "rm file.txt", "rm -r directory", "rm -f file.txt", "rmdir empty",
            "rm -- -rf", "echo 'rm -rf /tmp/example'", "printf '%s' 'git push --force'",
            "grep 'rm -rf' README.md", "echo 'DROP TABLE users'",
            "echo '$(rm -rf /tmp/example)'", "echo '\\`rm -rf example\\`'",
            "# rm -rf /tmp/example\npwd", "false || echo ok", "ls | head -n 1",
            "bash -lc 'git status'", "echo $(pwd)", "echo $((2 + 3))",
            'psql -c "SELECT * FROM users"', 'psql -c "DELETE FROM users WHERE id=1"',
            'psql -c "SELECT \'DROP TABLE users; TRUNCATE t; DELETE FROM t\'"',
            'psql -c "SELECT \'it\'\'s WHERE; DROP TABLE\'"',
            'psql -c "SELECT 1 /* DROP TABLE users */"',
            'psql -c "DELETE FROM users WHERE name=\'TRUNCATE\'"',
            "cat <<'EOF'\nrm -rf example\n$(git push --force)\nEOF\n",
            "psql <<'SQL'\nDELETE FROM users\nWHERE id=1;\nSQL\n",
            "# example $(rm -rf /tmp/example)\npwd",
            "echo '# $(pwd)'", "echo '<<EOF'\npwd",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command))

    def test_sql_boundaries(self):
        self.assertIsNone(guard.sql_reason("SELECT $$DROP TABLE users$$"))
        self.assertIsNone(guard.sql_reason("SELECT $tag$TRUNCATE t$tag$"))
        self.assertIsNotNone(guard.sql_reason('DELETE FROM "WHERE"'))
        self.assertIsNotNone(guard.sql_reason("DELETE FROM t RETURNING $$WHERE$$"))
        self.assertIsNotNone(guard.sql_reason("DELETE FROM t RETURNING 'WHERE;';"))


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory(prefix="guard test ")
        self.addCleanup(self.home.cleanup)
        self.env = {**os.environ, "HOME": self.home.name}
        self.log = Path(self.home.name) / ".claude/hooks/blocked.log"

    def run_hook(self, payload):
        return subprocess.run([sys.executable, str(HERE / "destructive_guard.py")],
                              input=json.dumps(payload), text=True, capture_output=True, env=self.env)

    def event(self, command):
        return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": command}, "cwd": "/project/with space"}

    def test_block_protocol_and_append_log(self):
        for command in ["rm -rf example", "git push --force\necho done"]:
            result = self.run_hook(self.event(command))
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertIn("Blocked:", output["permissionDecisionReason"])
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[1]["command"], "git push --force\necho done")
        self.assertEqual(records[0]["project_path"], "/project/with space")
        self.assertRegex(records[0]["timestamp"], r"^\d{4}-\d{2}-\d{2}T.*\+00:00$")
        self.assertEqual(self.log.stat().st_mode & 0o777, 0o600)

    def test_allow_and_ignore_other_tools(self):
        for event in [self.event("git status"), {**self.event("rm -rf example"), "tool_name": "Read"}]:
            result = self.run_hook(event)
            self.assertEqual((result.returncode, result.stdout), (0, ""))
        self.assertFalse(self.log.exists())

    def test_invalid_input_denies(self):
        for payload in [[], {"tool_name": "Bash"}, self.event(None)]:
            self.assertEqual(json.loads(self.run_hook(payload).stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_log_failure_still_denies(self):
        self.log.parent.mkdir(parents=True)
        self.log.mkdir()
        result = self.run_hook(self.event("rm -rf example"))
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("could not be written", output["permissionDecisionReason"])

    def test_installer_merges_and_is_idempotent(self):
        config = Path(self.home.name) / ".claude"
        config.mkdir()
        settings = config / "settings.json"
        previous = {"model": "example", "hooks": {"PostToolUse": [], "PreToolUse": [
            {"matcher": "Read", "hooks": [{"type": "command", "command": "echo existing"}]}]}}
        original = json.dumps(previous).encode()
        settings.write_bytes(original)
        for _ in range(2):
            result = subprocess.run([sys.executable, str(HERE / "install.py")], env=self.env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(settings.read_text())
        self.assertEqual(data["model"], "example")
        self.assertEqual(data["hooks"]["PostToolUse"], [])
        self.assertEqual(data["hooks"]["PreToolUse"][0], previous["hooks"]["PreToolUse"][0])
        self.assertEqual(len(data["hooks"]["PreToolUse"]), 2)
        backups = list(config.glob("settings.json.before-destructive-guard-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), original)
        command = data["hooks"]["PreToolUse"][-1]["hooks"][0]["command"]
        result = subprocess.run(command, shell=True, env=self.env, input=json.dumps(self.event("git push --force")), capture_output=True, text=True)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_invalid_settings_preserved(self):
        config = Path(self.home.name) / ".claude"
        config.mkdir()
        settings = config / "settings.json"
        settings.write_text("{invalid")
        result = subprocess.run([sys.executable, str(HERE / "install.py")], env=self.env, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(settings.read_text(), "{invalid")
        self.assertFalse((config / "hooks").exists())


if __name__ == "__main__":
    unittest.main()
