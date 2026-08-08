from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block-destructive.py"
CHANGELOG = ROOT / "scripts" / "changelog.py"


class HookTests(unittest.TestCase):
    def run_hook(self, command: str, log: Path) -> tuple[int, dict | None]:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(ROOT)}
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**os.environ, "CLAUDE_HOOK_LOG": str(log)},
            check=True,
        )
        return result.returncode, json.loads(result.stdout) if result.stdout.strip() else None

    def test_blocks_required_patterns_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "blocked.log"
            for command in (
                "rm -rf build",
                "DROP TABLE users",
                "TRUNCATE TABLE sessions",
                "git push --force origin main",
                "DELETE FROM users",
            ):
                _, output = self.run_hook(command, log)
                self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 5)
            self.assertTrue(all(record["project_path"] == str(ROOT) for record in records))

    def test_allows_safe_commands_and_delete_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / "blocked.log"
            for command in ("rm -r build", "git push origin main", "DELETE FROM users WHERE id = 1"):
                _, output = self.run_hook(command, log)
                self.assertIsNone(output)
            self.assertFalse(log.exists())


class ChangelogTests(unittest.TestCase):
    def test_generates_categories_from_real_repository_history(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHANGELOG), "--repo", str(ROOT), "--stdout"],
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn("# Changelog", result.stdout)
        for heading in ("Added", "Fixed", "Changed", "Removed"):
            self.assertIn(f"### {heading}", result.stdout)

    def test_reads_commits_since_latest_tag_and_categorizes_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            for subject in ("feat: initial", "fix: stale parser", "remove: old mode"):
                (repo / "sample.txt").write_text(subject, encoding="utf-8")
                subprocess.run(["git", "add", "sample.txt"], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-q", "-m", subject], cwd=repo, check=True)
                if subject == "feat: initial":
                    subprocess.run(["git", "tag", "v1.0.0"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(CHANGELOG), "--repo", str(repo), "--stdout"],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("fix: stale parser", result.stdout)
            self.assertIn("remove: old mode", result.stdout)
            self.assertNotIn("feat: initial", result.stdout)


if __name__ == "__main__":
    unittest.main()
