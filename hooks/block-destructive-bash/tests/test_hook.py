"""Stdlib-only tests for hooks/block-destructive-bash/hook.py.

Run from the bounty folder:
    python -m unittest hooks.block-destructive-bash.tests.test_hook
or:
    python hooks/block-destructive-bash/tests/test_hook.py
"""
from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path

THIS = Path(__file__).resolve()
HOOK_DIR = THIS.parent.parent
sys.path.insert(0, str(HOOK_DIR))

import hook as hook_module  # noqa: E402  (path-modifying import)


class EvaluateBlocked(unittest.TestCase):
    """Commands that MUST be blocked."""

    cases = [
        # Recursive force delete — bundled flag forms
        "rm -rf /",
        "rm -rf .",
        "rm -fr ./node_modules",
        "rm -Rf foo",
        "rm -fR foo",
        "rm -rfv tmp/",
        # Recursive force delete — separated flags
        "rm -r -f foo",
        "rm -f -r foo",
        # Recursive force delete — long flags
        "rm --recursive --force foo",
        "rm --force --recursive foo",
        # Compound commands still block
        "cd /tmp && rm -rf .",
        "ls; rm -rf /var/log",
        # SQL DDL / unsafe DML
        "psql -c 'DROP TABLE users'",
        "mysql -e \"drop database prod\"",
        "DROP TABLE users;",
        "TRUNCATE TABLE logs",
        "TRUNCATE logs",
        "DELETE FROM users",
        "DELETE FROM users;",
        # git force push
        "git push --force origin main",
        "git push -f origin main",
        # Disk / filesystem destruction
        "dd if=/dev/zero of=/dev/sda bs=1M",
        "mkfs.ext4 /dev/sdb1",
        "echo bad > /dev/sda",
        # Fork bomb
        ":(){ :|: & };:",
    ]

    def test_all_blocked(self) -> None:
        for cmd in self.cases:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(
                    hook_module.evaluate(cmd),
                    f"Expected to BLOCK: {cmd!r}",
                )


class EvaluateAllowed(unittest.TestCase):
    """Commands that MUST NOT be blocked (no false positives)."""

    cases = [
        # Normal shell work
        "ls -la",
        "cd src && npm test",
        "git status",
        "python script.py",
        # Partial rm: missing one of the two required flags
        "rm file.txt",
        "rm -r dir",  # recursive but not forced
        "rm -f file",  # forced but not recursive
        # Quoted dangerous strings (echoes / docs / greps)
        'echo "rm -rf"',
        "grep 'DROP TABLE' schema.sql",
        'cat README.md | grep "git push --force"',
        # Comments
        "# rm -rf is dangerous",
        "ls # rm -rf comment",
        # Safe SQL
        "SELECT * FROM users",
        "DELETE FROM users WHERE id = 1",
        "DELETE FROM users WHERE id = 1;",
        "UPDATE users SET active = 0 WHERE id = 1",
        # Safer git variants
        "git push origin main",
        "git push --force-with-lease origin main",
        "git push --force-with-lease=main:abc origin main",
        # Other false-positive temptations
        "echo 'TRUNCATE TABLE logs'",
        "rg 'mkfs' docs/",
    ]

    def test_all_allowed(self) -> None:
        for cmd in self.cases:
            with self.subTest(cmd=cmd):
                self.assertIsNone(
                    hook_module.evaluate(cmd),
                    f"Expected to ALLOW: {cmd!r} (got: {hook_module.evaluate(cmd)!r})",
                )


class StripComments(unittest.TestCase):
    def test_strips_outside_quotes(self) -> None:
        self.assertEqual(hook_module.strip_line_comments("ls # bye"), "ls ")

    def test_keeps_inside_double_quotes(self) -> None:
        self.assertEqual(
            hook_module.strip_line_comments('echo "hi # not a comment"'),
            'echo "hi # not a comment"',
        )

    def test_keeps_inside_single_quotes(self) -> None:
        self.assertEqual(
            hook_module.strip_line_comments("echo 'a # b'"), "echo 'a # b'"
        )

    def test_handles_multiline(self) -> None:
        self.assertEqual(
            hook_module.strip_line_comments("ls # one\npwd # two"),
            "ls \npwd ",
        )


class HookEntryPoint(unittest.TestCase):
    """Verify run_hook() reads stdin, blocks, and emits the right schema."""

    def _run(self, payload: dict) -> tuple[int, str]:
        sys.stdin = io.StringIO(json.dumps(payload))
        out = io.StringIO()
        sys.stdout = out
        try:
            rc = hook_module.run_hook()
        finally:
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__
        return rc, out.getvalue()

    def test_blocks_rm_rf(self) -> None:
        rc, body = self._run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/whatever"},
                "cwd": "/some/project",
            }
        )
        self.assertEqual(rc, 0)
        self.assertTrue(body, "expected JSON output for blocked command")
        decision = json.loads(body)
        self.assertEqual(
            decision["hookSpecificOutput"]["permissionDecision"], "deny"
        )
        self.assertIn(
            "rm", decision["hookSpecificOutput"]["permissionDecisionReason"]
        )

    def test_allows_safe_command(self) -> None:
        rc, body = self._run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
                "cwd": "/some/project",
            }
        )
        self.assertEqual(rc, 0)
        self.assertEqual(body, "")  # silent allow

    def test_ignores_non_bash_tool(self) -> None:
        rc, body = self._run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Read",
                "tool_input": {"file_path": "/etc/passwd"},
            }
        )
        self.assertEqual(rc, 0)
        self.assertEqual(body, "")

    def test_ignores_non_pretooluse_event(self) -> None:
        rc, body = self._run(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /"},
            }
        )
        self.assertEqual(rc, 0)
        self.assertEqual(body, "")

    def test_malformed_input_fails_open(self) -> None:
        sys.stdin = io.StringIO("not json")
        try:
            rc = hook_module.run_hook()
        finally:
            sys.stdin = sys.__stdin__
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
