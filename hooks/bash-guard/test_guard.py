import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


class GuardTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.home = Path(tmp.name)
        self.env = dict(os.environ, HOME=tmp.name, USERPROFILE=tmp.name)

    def event(self, command, name="Bash"):
        payload = {"tool_name": name, "tool_input": {"command": command}, "cwd": "/fixtures/project"}
        return subprocess.run([sys.executable, str(HERE / "guard.py")], env=self.env,
                              input=json.dumps(payload), text=True, capture_output=True, check=True).stdout

    def test_denials_and_json_lines(self):
        blocked = ["rm -rf fixture", "rm --recursive --force fixture", "git -C fixture push --force",
                   'sqlite3 scratch.db "drop table records"', 'psql -c "TRUNCATE records"',
                   'mysql -e "DELETE FROM records"', "DELETE FROM records",
                   'psql -c "DELETE\nFROM records"', "echo 'DELETE FROM records' | sqlite3 fixture.db"]
        for command in blocked:
            out = json.loads(self.event(command))["hookSpecificOutput"]
            self.assertEqual(out["permissionDecision"], "deny")
            self.assertTrue(out["permissionDecisionReason"])
        lines = (self.home / ".claude/hooks/blocked.log").read_text().splitlines()
        entries = [json.loads(x) for x in lines]
        self.assertEqual([x["command"] for x in entries], blocked)
        self.assertTrue(all(x["project_path"] == "/fixtures/project" and x["timestamp"] for x in entries))

    def test_normal_commands_are_unchanged(self):
        for command in ["git status", "git push origin main", "rm -- fixture", "ls",
                        "echo 'DROP TABLE example'", "printf 'rm -rf notes'",
                        "sqlite3 scratch.db \"DELETE FROM records WHERE id=3\"",
                        "echo first\nprintf second"]:
            self.assertEqual(self.event(command), "")
        self.assertEqual(self.event("rm -rf fixture", "Read"), "")
        self.assertFalse((self.home / ".claude/hooks/blocked.log").exists())

    def test_install_twice_preserves_settings(self):
        settings = self.home / ".claude/settings.json"
        settings.parent.mkdir()
        original = {"matcher": "Read", "hooks": []}
        settings.write_text(json.dumps({"theme": "dark", "hooks": {"PreToolUse": [original]}}))
        for _ in range(2):
            subprocess.run([sys.executable, str(HERE / "install.py")], env=self.env, check=True,
                           capture_output=True)
        result = json.loads(settings.read_text())
        self.assertEqual(result["theme"], "dark")
        self.assertEqual(result["hooks"]["PreToolUse"][0], original)
        self.assertEqual(len(result["hooks"]["PreToolUse"]), 2)
        self.assertTrue((self.home / ".claude/hooks/bash-guard.py").is_file())


if __name__ == "__main__":
    unittest.main()
