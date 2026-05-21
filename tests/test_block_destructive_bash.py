import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = REPO_ROOT / "hooks" / "block_destructive_bash.py"
INSTALLER_SCRIPT = REPO_ROOT / "hooks" / "install_block_destructive_hook.py"


class DestructiveBashHookTests(unittest.TestCase):
    def run_hook(self, command, *, tool_name="Bash", cwd="/tmp/project"):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home, ignore_errors=True)
        payload = {
            "hook_event_name": "PreToolUse",
            "cwd": cwd,
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        env["CLAUDE_HOOKS_DIR"] = str(home / ".claude" / "hooks")

        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        return result, home

    def test_blocks_required_destructive_patterns(self):
        blocked_commands = [
            "rm -rf build",
            "git push --force origin main",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'TRUNCATE audit_log'",
            "mysql -e 'DELETE FROM users'",
        ]

        for command in blocked_commands:
            with self.subTest(command=command):
                result, home = self.run_hook(command, cwd="/workspace/app")

                self.assertEqual(result.returncode, 2)
                self.assertIn("Blocked destructive Bash command", result.stderr)

                log_path = home / ".claude" / "hooks" / "blocked.log"
                self.assertTrue(log_path.exists())
                log_text = log_path.read_text(encoding="utf-8")
                self.assertIn(command, log_text)
                self.assertIn("/workspace/app", log_text)
                self.assertRegex(log_text, re.compile(r"\d{4}-\d{2}-\d{2}T"))

    def test_allows_normal_bash_commands(self):
        allowed_commands = [
            "npm test",
            "git push origin main",
            "psql -c 'DELETE FROM sessions WHERE id = 1'",
        ]

        for command in allowed_commands:
            with self.subTest(command=command):
                result, home = self.run_hook(command)

                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, "")
                self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_ignores_non_bash_tools(self):
        result, home = self.run_hook("rm -rf build", tool_name="Read")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())


class InstallerTests(unittest.TestCase):
    def test_installer_adds_bash_pre_tool_use_hook_once(self):
        temp_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp_root, ignore_errors=True)
        claude_dir = temp_root / ".claude"
        env = os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = str(claude_dir)

        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(INSTALLER_SCRIPT)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

        self.assertTrue((claude_dir / "hooks" / "block_destructive_bash.py").exists())
        settings = json.loads((claude_dir / "settings.json").read_text(encoding="utf-8"))
        pre_tool_use = settings["hooks"]["PreToolUse"]
        bash_matcher = next(item for item in pre_tool_use if item["matcher"] == "Bash")
        matching_hooks = [
            hook
            for hook in bash_matcher["hooks"]
            if hook["type"] == "command"
            and "block_destructive_bash.py" in hook["command"]
        ]
        self.assertEqual(len(matching_hooks), 1)


if __name__ == "__main__":
    unittest.main()
