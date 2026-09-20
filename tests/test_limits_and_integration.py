"""Resource, concurrent audit, and installed-entrypoint checks; all offline."""

import concurrent.futures
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_commands.py"


class LimitsAndIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="offline hook integration ")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.environment = dict(os.environ, HOME=str(self.home))
        self.log = self.home / ".claude" / "hooks" / "blocked.log"

    def invoke(self, payload, argv=None):
        # Only the hook is executed. No shell ever receives tool_input.command.
        return subprocess.run(argv or [sys.executable, str(HOOK)], input=payload,
                              capture_output=True, text=True, env=self.environment,
                              cwd=self.home, timeout=10)

    def event(self, command, **extra):
        payload = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                   "tool_input": {"command": command}, "cwd": str(self.home)}
        payload.update(extra)
        return json.dumps(payload)

    def test_oversized_input_is_refused_and_audited_without_retaining_blob(self):
        result = self.invoke("x" * (1024 * 1024 + 1))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("1 MiB", result.stderr)
        self.assertLess(self.log.stat().st_size, 2048)

    def test_nesting_limit_is_refused_without_python_traceback(self):
        command = "printf safe"
        # Double quotes keep this fixture linear in size (no execution occurs).
        command = "$(" * 20 + command + ")" * 20
        result = self.invoke(self.event(command))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("nesting", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_other_events_are_ignored(self):
        result = self.invoke(self.event("rm -rf fixture", hook_event_name="PostToolUse"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.log.exists())

    def test_concurrent_denials_produce_one_intact_record_each(self):
        commands = ["rm -rf /tmp/text-fixture-{}".format(i) for i in range(12)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(lambda c: self.invoke(self.event(c)), commands))
        self.assertTrue(all(r.returncode == 2 for r in results))
        self.assertTrue(all("logging failed" not in r.stderr for r in results))
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(records), len(commands))
        self.assertEqual({r["command"] for r in records}, set(commands))

    def test_installed_settings_launch_the_real_hook(self):
        install = subprocess.run([sys.executable, str(ROOT / "install.py")],
                                 capture_output=True, text=True, env=self.environment,
                                 timeout=10)
        self.assertEqual(install.returncode, 0, install.stderr)
        settings = json.loads((self.home / ".claude" / "settings.json").read_text())
        entry = settings["hooks"]["PreToolUse"][0]
        argv = shlex.split(entry["hooks"][0]["command"])
        self.assertEqual(entry["matcher"], "Bash")
        self.assertEqual(Path(argv[1]).read_bytes(), HOOK.read_bytes())
        allowed = self.invoke(self.event("printf safe"), argv)
        denied = self.invoke(self.event("rm -rf /tmp/text-fixture"), argv)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(denied.returncode, 2, denied.stderr)
        self.assertEqual(json.loads(self.log.read_text())["project_path"], str(self.home))

    def test_split_echo_arguments_are_inspected_as_one_sql_statement(self):
        result = self.invoke(self.event("echo DELETE FROM accounts | sqlite3 local.db"))
        self.assertEqual(result.returncode, 2, result.stderr)


if __name__ == "__main__":
    unittest.main()
