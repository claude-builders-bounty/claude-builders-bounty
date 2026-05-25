from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


INSTALLER = Path(__file__).resolve().parents[1] / "install.py"


class InstallerTest(unittest.TestCase):
    def test_installs_hook_and_settings_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp

            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(INSTALLER)],
                    text=True,
                    capture_output=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            hook_path = Path(tmp) / ".claude" / "hooks" / "destructive-command-guard.py"
            settings_path = Path(tmp) / ".claude" / "settings.json"

            self.assertTrue(hook_path.exists())
            self.assertTrue(hook_path.stat().st_mode & stat.S_IXUSR)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            entries = settings["hooks"]["PreToolUse"]
            matching_entries = [
                hook
                for group in entries
                for hook in group["hooks"]
                if hook["command"] == str(hook_path)
            ]
            self.assertEqual(len(matching_entries), 1)


if __name__ == "__main__":
    unittest.main()
