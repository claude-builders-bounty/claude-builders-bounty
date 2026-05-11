from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.py"


def load_installer():
    spec = importlib.util.spec_from_file_location("install_hook", INSTALLER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class InstallTest(unittest.TestCase):
    def test_install_registers_hook_and_is_idempotent(self) -> None:
        installer = load_installer()
        claude_home = Path(tempfile.mkdtemp()) / ".claude"

        target, settings_path, changed = installer.install(claude_home, sys.executable)
        _, _, changed_again = installer.install(claude_home, sys.executable)

        self.assertTrue(changed)
        self.assertFalse(changed_again)
        self.assertEqual(target, claude_home / "hooks" / "block_destructive_bash.py")
        self.assertTrue(target.exists())

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = settings["hooks"]["PreToolUse"]
        bash_matcher = next(item for item in hooks if item["matcher"] == "Bash")
        commands = [hook["command"] for hook in bash_matcher["hooks"]]
        self.assertEqual(len(commands), 1)
        self.assertIn("block_destructive_bash.py", commands[0])


if __name__ == "__main__":
    unittest.main()
