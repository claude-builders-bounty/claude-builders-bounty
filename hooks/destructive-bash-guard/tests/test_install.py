import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "install.py"
spec = importlib.util.spec_from_file_location("install", MODULE_PATH)
installer = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_merge_settings_adds_bash_pre_tool_use_hook(self):
        merged = installer.merge_settings({"permissions": {"allow": ["Read"]}})

        self.assertEqual(merged["permissions"], {"allow": ["Read"]})
        pre_tool_use = merged["hooks"]["PreToolUse"]
        self.assertEqual(len(pre_tool_use), 1)
        self.assertEqual(pre_tool_use[0]["matcher"], "Bash")
        self.assertEqual(
            pre_tool_use[0]["hooks"][0]["command"],
            "python3 ~/.claude/hooks/destructive_bash_guard.py",
        )

    def test_merge_settings_does_not_duplicate_existing_hook(self):
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": installer.HOOK_COMMAND,
                            }
                        ],
                    }
                ]
            }
        }

        merged = installer.merge_settings(settings)

        self.assertEqual(len(merged["hooks"]["PreToolUse"]), 1)

    def test_install_copies_hook_and_writes_settings(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            settings_path = home / ".claude" / "settings.json"
            installed = installer.install(settings_path, home=home)

            self.assertEqual(installed, settings_path)
            self.assertTrue((home / ".claude" / "hooks" / "destructive_bash_guard.py").exists())
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertTrue(installer.has_guard_entry(settings["hooks"]["PreToolUse"]))


if __name__ == "__main__":
    unittest.main()
