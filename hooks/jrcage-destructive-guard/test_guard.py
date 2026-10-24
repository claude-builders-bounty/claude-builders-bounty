import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


guard = load("guard")
installer = load("install")


class LiteralCommandTests(unittest.TestCase):
    def test_denied_commands(self):
        commands = [
            "rm -rf /tmp/fixture", "rm -fr /tmp/fixture", "rm -r -f /tmp/fixture",
            "rm --recursive --force /tmp/fixture", "/bin/rm -Rf /tmp/fixture",
            "sudo -u nobody rm -rf /tmp/fixture", "env X=1 rm -rf /tmp/fixture",
            "command -- rm -rf /tmp/fixture", "true && rm -rf /tmp/fixture",
            "true\nrm -rf /tmp/fixture", "(rm -rf /tmp/fixture)",
            "rm -r\\\n -f /tmp/fixture", "bash -lc 'rm -rf /tmp/fixture'",
            'bash -c "sh -c \'rm -rf /tmp/fixture\'"',
            "git push --force origin main", "git -C /tmp push -f origin main",
            "git -c core.pager=cat push --force-with-lease", "git push origin +main:main",
            "git push -vf origin main", "DROP TABLE things", "TRUNCATE TABLE things",
            'sqlite3 :memory: "DROP TABLE things;"',
            'psql -c "DELETE FROM things;"',
            'mysql -e "DELETE FROM things; SELECT 1 WHERE true;"',
            'psql -c "DELETE FROM things /* WHERE id=1 */;"',
            'psql -c "DELETE FROM things RETURNING \'WHERE\';"',
            'psql -c "DELETE FROM things RETURNING (SELECT 1 WHERE true);"',
            'psql -c "DROP /* note */ TABLE things;"',
            'sqlite3 :memory: "DELETE FROM things WHERE id=1; DELETE FROM other;"',
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.command_reason(command))

    def test_normal_commands_have_no_objection(self):
        commands = [
            "git status --short", "git push origin main", "git --version",
            "git push --force-if-includes", "rm file.txt", "rm -r folder",
            "rm -f file.txt", "rm -- -rf", "printf '%s' 'rm -rf folder'",
            "echo 'DROP TABLE example'", "echo 'git push --force'",
            "python3 -m unittest", "ls -la | head -10", "# rm -rf /tmp/fixture\ntrue",
            'sqlite3 :memory: "SELECT \'DROP TABLE things\';"',
            'psql -c "DELETE FROM things WHERE id=1;"',
            'psql -c "DELETE FROM things WHERE id IN (SELECT id FROM old);"',
            'mysql -e "SELECT 1; -- TRUNCATE things\nSELECT 2;"',
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.command_reason(command))

    def test_unclosed_quoting_denied(self):
        self.assertIsNotNone(guard.command_reason("echo 'oops"))


class ProtocolTests(unittest.TestCase):
    def invoke(self, raw, home):
        # Run only our hook in a disposable home. Commands are never executed.
        return subprocess.run([sys.executable, str(ROOT / "guard.py")],
                              input=raw, capture_output=True, timeout=5,
                              env={"HOME": str(home), "PATH": os.defpath})

    def event(self, command, **kwargs):
        return json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Bash",
                           "tool_input": {"command": command}, "cwd": "/synthetic/project", **kwargs}).encode()

    def test_denial_and_jsonl_log(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            command = 'rm -rf /synthetic/only\necho "not run"'
            result = self.invoke(self.event(command), home)
            self.assertEqual(result.returncode, 0)
            response = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(response["hookEventName"], "PreToolUse")
            self.assertEqual(response["permissionDecision"], "deny")
            self.assertIn("removal", response["permissionDecisionReason"])
            log = home / ".claude/hooks/blocked.log"
            record = json.loads(log.read_text())
            self.assertEqual(record["command"], command)
            self.assertEqual(record["project_path"], "/synthetic/project")
            self.assertIn("+00:00", record["timestamp"])
            self.assertEqual(len(log.read_text().splitlines()), 1)
            self.assertEqual(log.stat().st_mode & 0o777, 0o600)
            self.invoke(self.event("git push --force"), home)
            self.assertEqual(len(log.read_text().splitlines()), 2)

    def test_allowed_does_not_log_or_auto_approve(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            result = self.invoke(self.event("git status"), home)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b"")
            self.assertFalse((home / ".claude").exists())

    def test_other_tools_unaffected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.invoke(self.event("rm -rf x", tool_name="Read"), Path(directory))
            self.assertEqual(result.stdout, b"")

    def test_invalid_input_denied(self):
        for raw in [b"{", b"[]", b"null", b'{"tool_name":"Bash","tool_input":{}}', b"x" * (guard.MAX_INPUT + 1)]:
            with self.subTest(raw=raw[:50]), tempfile.TemporaryDirectory() as directory:
                result = self.invoke(raw, Path(directory))
                self.assertEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_log_failure_still_denies(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / ".claude").write_text("not a directory")
            result = self.invoke(self.event("rm -rf x"), home)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn(b"could not be written", result.stdout)


class InstallerTests(unittest.TestCase):
    def test_merge_backup_and_repeat_install(self):
        with tempfile.TemporaryDirectory(prefix="guard home ") as directory:
            root = Path(directory) / ".claude"
            root.mkdir()
            prior = {"model": "existing", "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}], "Stop": []}}
            settings = root / "settings.json"
            settings.write_text(json.dumps(prior))
            installer.install(root)
            installer.install(root)
            result = json.loads(settings.read_text())
            self.assertEqual(result["model"], "existing")
            self.assertEqual(result["hooks"]["Stop"], [])
            self.assertEqual(len(result["hooks"]["PreToolUse"]), 2)
            self.assertEqual(json.loads((root / "settings.before-jrcage-guard.json").read_text()), prior)
            self.assertEqual((root / "hooks/jrcage-destructive-guard.py").read_bytes(), (ROOT / "guard.py").read_bytes())
            self.assertEqual(settings.stat().st_mode & 0o777, 0o600)

    def test_bad_settings_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "settings.json"
            settings.write_text("{broken")
            with self.assertRaises(ValueError):
                installer.install(root)
            self.assertEqual(settings.read_text(), "{broken")
            self.assertFalse((root / "hooks").exists())


if __name__ == "__main__":
    unittest.main()
