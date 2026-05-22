import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["block_destructive_bash"] = module
spec.loader.exec_module(module)


class BlockDestructiveBashTest(unittest.TestCase):
    def test_allows_normal_bash_command(self):
        self.assertIsNone(module.blocked_reason("git status --short"))
        self.assertIsNone(module.blocked_reason("rm old-build.log"))
        self.assertIsNone(module.blocked_reason("DELETE FROM sessions WHERE id = 1"))

    def test_blocks_rm_rf_variants(self):
        self.assertEqual(module.blocked_reason("rm -rf dist").rule, "rm -rf")
        self.assertEqual(module.blocked_reason("rm -fr dist").rule, "rm -rf")
        self.assertEqual(module.blocked_reason("sudo rm -Rf /tmp/example").rule, "rm -rf")

    def test_blocks_force_push_variants(self):
        self.assertEqual(module.blocked_reason("git push --force origin main").rule, "git push --force")
        self.assertEqual(module.blocked_reason("git push -f").rule, "git push --force")
        self.assertEqual(module.blocked_reason("git push --force-with-lease").rule, "git push --force")

    def test_blocks_destructive_sql(self):
        self.assertEqual(module.blocked_reason("DROP TABLE users").rule, "DROP TABLE")
        self.assertEqual(module.blocked_reason("truncate table events").rule, "TRUNCATE")
        self.assertEqual(
            module.blocked_reason("DELETE FROM audit_log").rule,
            "DELETE FROM without WHERE",
        )

    def test_cli_blocks_with_exit_code_two_and_logs(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "cwd": "/workspace/project",
            }
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked destructive Bash command", result.stderr)
            log_file = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertIn("rm -rf build", log_file.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
