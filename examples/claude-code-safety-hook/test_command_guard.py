from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import command_guard


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "command_guard.py"
INSTALLER = ROOT / "install.py"


class ClassifierTests(unittest.TestCase):
    def test_issue_patterns_are_blocked_as_strings_only(self) -> None:
        examples = [
            "rm -rf /tmp/demo",
            "/bin/rm -f -R /tmp/demo",
            "rm --recursive --force x",
            "true && rm -fr x",
            "git push --force origin main",
            "git -C /tmp/repo push origin main -f",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE TABLE users'",
            "sqlite3 x.db 'DELETE FROM users'",
            "MODE=test rm -rf /tmp/demo",
            "git push -vf origin main",
            "git push origin +HEAD:main",
            "eval rm -rf /tmp/demo",
            "sqlite3 -cmd 'DROP TABLE users' sample.db",
            "printf '%s' 'DELETE FROM users' | psql",
            "psql <<'SQL'\nDELETE FROM users;\nSQL",
            "psql -c 'WITH removed AS (DELETE FROM users RETURNING *) SELECT * FROM removed'",
            "psql -c 'WITH removed AS (DELETE FROM users RETURNING *), filtered AS (SELECT * FROM users WHERE id=1) SELECT * FROM removed'",
            "printf 'DROP %s users' TABLE | psql",
            "printf '\\x44ROP TABLE users' | psql",
            "printf '%s' 'SELECT 1;' 'DROP TABLE users' | psql",
            "echo 'DROP TABLE users' | psql | cat",
            "bash <<'EOF'\nrm -rf /tmp/example\nEOF",
            "cat <<'EOF' | bash\nrm -rf /tmp/example\nEOF",
            "echo '<<EOF'\nrm -rf /tmp/example\nEOF",
            "cat file.sql | psql",
            "psql < file.sql",
        ]
        for command in examples:
            with self.subTest(command=command):
                self.assertIsNotNone(command_guard.inspect_command(command))

    def test_wrapped_and_substitution_commands_are_blocked(self) -> None:
        examples = [
            "echo \"$(rm -rf x)\"",
            "bash -c 'rm -rf x'",
            "sudo git push --force origin main",
            "env MODE=test rm -rf x",
            "git --no-pager -C /tmp/r push --force-with-lease origin main",
        ]
        for command in examples:
            with self.subTest(command=command):
                self.assertIsNotNone(command_guard.inspect_command(command))

    def test_normal_commands_and_literal_text_are_allowed(self) -> None:
        examples = [
            "ls",
            "git status",
            "npm test",
            "rm single.txt",
            "git push origin main",
            "echo 'rm -rf x; DROP TABLE users'",
            "printf '%s' 'git push --force'",
            "# rm -rf x\nls",
            "psql -c 'SELECT 1'",
            "DELETE FROM users WHERE id=1",
            "DELETE FROM users WHERE id IN (SELECT id FROM old WHERE stale=1)",
            "psql -c \"DELETE FROM users WHERE id IN (SELECT id FROM old)\"",
            "DELETE FROM users WHERE note='WHERE is this text'",
            "# $(rm -rf x)\nls",
            "printf x # `rm -rf x`",
            "psql -c 'SELECT $$ DROP TABLE users $$'",
            "psql <<'SQL'\nSELECT 1;\nSQL",
            "cat <<'EOF'\nrm -rf /tmp/example\nEOF",
            "cat <<'EOF'\n$(rm -rf x)\nEOF",
            "bash -c 'cat' <<'EOF'\nrm -rf /tmp/example\nEOF",
            "psql <<'SQL'\nSELECT 1;\nSQL\ncat <<'TEXT'\nDROP TABLE users;\nTEXT",
            "echo 'SELECT 1' | psql",
            "printf '%s' 'SELECT 1' | psql",
        ]
        for command in examples:
            with self.subTest(command=command):
                self.assertIsNone(command_guard.inspect_command(command))

    def test_sql_comments_strings_and_nested_where_do_not_hide_unbounded_delete(self) -> None:
        examples = [
            "psql -c \"DELETE FROM users /* WHERE */\"",
            "psql -c \"DELETE FROM users -- WHERE hidden\\n\"",
            "psql -c \"DELETE FROM users; DELETE FROM secrets WHERE id=1\"",
            "mysql -e 'DELETE FROM users # WHERE id=1'",
            "psql -c 'DELETE FROM users RETURNING $$ WHERE $$'",
            "psql <<'SQL' > /tmp/fixture-output\nDELETE FROM users;\nSQL",
            "echo \"$SQL\" | psql",
            "psql <<SQL\nSELECT $SQL;\nSQL",
        ]
        for command in examples:
            with self.subTest(command=command):
                self.assertIsNotNone(command_guard.inspect_command(command))


class HookProcessTests(unittest.TestCase):
    def run_hook(self, command: str, home: str, cwd: str = "/work/demo") -> subprocess.CompletedProcess[bytes]:
        payload = json.dumps(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "cwd": cwd,
            }
        ).encode()
        return subprocess.run(
            [sys.executable, str(HOOK)], input=payload, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env={**os.environ, "HOME": home}, check=False,
        )

    def test_process_protocol_logs_redacted_block_and_silent_allow(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            blocked = self.run_hook("rm -rf /tmp/demo --token super-secret", str(home))
            self.assertEqual(blocked.returncode, 2)
            self.assertEqual(blocked.stdout, b"")
            self.assertIn(b"Blocked recursive forced removal", blocked.stderr)
            log = home / ".claude" / "hooks" / "blocked.log"
            record = json.loads(log.read_text(encoding="utf-8"))
            self.assertEqual(record["project_path"], "/work/demo")
            self.assertEqual(record["command"], "rm -rf /tmp/demo --token [REDACTED]")
            self.assertTrue(record["timestamp"].endswith("Z"))
            self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)

            allowed = self.run_hook("git status", str(home))
            self.assertEqual((allowed.returncode, allowed.stdout, allowed.stderr), (0, b"", b""))
            self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)

    def test_symlink_log_is_not_followed_but_command_stays_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            hooks = home / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            outside = home / "outside.log"
            outside.write_text("keep\n", encoding="utf-8")
            (hooks / "blocked.log").symlink_to(outside)
            result = self.run_hook("rm -rf /tmp/demo", str(home))
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"could not be written", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "keep\n")

    def test_bash_dollar_quote_and_opaque_stdin_fail_closed(self) -> None:
        # Each example is hook input text only; fixture commands are never executed.
        blocked_inputs = (
            "bash -c $'rm -rf /tmp/fixture'",
            "$'rm' -rf /tmp/fixture",
            "bash -c $'git push --force origin main'",
            "psql -c $'DROP TABLE users'",
            "bash <<< 'rm -rf /tmp/fixture'",
            'cat /fake/script.sh | bash',
            "echo 'git push --force origin main' | bash",
            "printf '%s' 'rm -rf /tmp/fixture' | bash",
            'bash < /fake/script.sh',
        )
        with tempfile.TemporaryDirectory() as temp:
            for command in blocked_inputs:
                with self.subTest(command=command):
                    result = self.run_hook(command, temp)
                    self.assertEqual(result.returncode, 2, result.stderr.decode())
                    self.assertEqual(result.stdout, b"")
            for command in (
                'echo "literal $\'text\'"',
                "bash -c 'printf safe'",
                "echo 'printf safe' | bash",
                "cat <<'EOF'\nrm -rf x\nEOF",
            ):
                with self.subTest(normal_command=command):
                    result = self.run_hook(command, temp)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_safe_shell_heredoc_and_stdin_controls(self) -> None:
        # Data sent to the hook only, never executed as shell commands.
        allowed = (
            "bash <<'EOF'\nprintf safe\nEOF",
            "cat <<'EOF' | bash\nprintf safe\nEOF",
            "bash -s <<'EOF'\nprintf safe\nEOF",
            "echo 'printf safe' | bash",
            "printf '%s' 'printf safe' | sh",
            "bash -c 'printf safe' < /fake/input",
        )
        with tempfile.TemporaryDirectory() as temp:
            for command in allowed:
                with self.subTest(command=command):
                    result = self.run_hook(command, temp)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_stdin_option_boundaries_and_overrides_fail_closed(self) -> None:
        blocked = (
            "echo 'rm -rf /tmp/fixture' | bash -s -- -c",
            "bash -s -- -c <<< 'rm -rf /tmp/fixture'",
            "bash <<'EOF' <<< 'rm -rf /tmp/fixture'\nprintf safe\nEOF",
            "echo -ne '\\x72m -rf /tmp/fixture' | bash",
            "echo -ne 'rm -rf /tmp/fixture' | bash",
            "echo -nE 'git push --force origin main' | bash",
        )
        with tempfile.TemporaryDirectory() as temp:
            for command in blocked:
                with self.subTest(command=command):
                    result = self.run_hook(command, temp)
                    self.assertEqual(result.returncode, 2, result.stderr.decode())
                    self.assertEqual(result.stdout, b"")
            for command in ("echo 'printf safe' | bash -s -- -c", "echo -n 'printf safe' | bash", "echo -ne 'printf safe' | bash"):
                with self.subTest(normal_command=command):
                    result = self.run_hook(command, temp)
                    self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_non_bash_tool_is_ignored(self) -> None:
        payload = json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}}).encode()
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run([sys.executable, str(HOOK)], input=payload, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, env={**os.environ, "HOME": temp}, check=False)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))

    def test_malformed_and_oversize_input_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for payload in (b"{", b"x" * (command_guard.MAX_INPUT_BYTES + 1)):
                result = subprocess.run([sys.executable, str(HOOK)], input=payload, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, env={**os.environ, "HOME": temp}, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertIn(b"could not validate", result.stderr)

    def test_deep_json_missing_tool_and_nul_command_fail_closed_without_traceback(self) -> None:
        deep = b"{" + b'"x":' * 1200 + b'0' + b'}' * 1200
        huge_integer = b'{"tool_name":"Bash","tool_input":{"command":"ls"},"extra":' + b"1" * 5000 + b"}"
        payloads = (
            deep,
            huge_integer,
            b"{}",
            json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls\u0000"}}).encode(),
        )
        with tempfile.TemporaryDirectory() as temp:
            for payload in payloads:
                result = subprocess.run([sys.executable, str(HOOK)], input=payload, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, env={**os.environ, "HOME": temp}, check=False,
                                        timeout=5)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertNotIn(b"Traceback", result.stderr)

    def test_shell_parse_errors_fail_closed_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            for command in ('"', "eval " * 500 + "true"):
                result = self.run_hook(command, temp)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b"")
                self.assertNotIn(b"Traceback", result.stderr)

    def test_fifo_and_hardlink_logs_are_rejected_without_mutating_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            hooks = home / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            log = hooks / "blocked.log"
            os.mkfifo(log)
            result = self.run_hook("rm -rf x", str(home))
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"could not be written", result.stderr)
            log.unlink()

            outside = home / "other.log"
            outside.write_text("preserve", encoding="utf-8")
            os.link(outside, log)
            result = self.run_hook("rm -rf x", str(home))
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"could not be written", result.stderr)
            self.assertEqual(outside.read_text(encoding="utf-8"), "preserve")

    def test_secret_redaction_covers_quoted_and_common_values(self) -> None:
        command = "TOKEN='one two' --password=\"three four\" API_TOKEN=alpha PGPASSWORD=beta https://user:gamma@example.test"
        redacted = command_guard.redact_command(command)
        for secret in ("one two", "three four", "alpha", "beta", "gamma"):
            self.assertNotIn(secret, redacted)
        self.assertGreaterEqual(redacted.count("[REDACTED]"), 5)

    def test_log_is_bounded_and_keeps_the_latest_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            hooks = home / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            log = hooks / "blocked.log"
            log.write_text("x" * command_guard.MAX_LOG_BYTES, encoding="utf-8")
            result = self.run_hook("rm -rf x", str(home))
            self.assertEqual(result.returncode, 2)
            data = log.read_text(encoding="utf-8")
            self.assertLessEqual(len(data.encode()), command_guard.MAX_LOG_BYTES)
            record = json.loads(data)
            self.assertTrue(record["previous_log_truncated"])


class InstallerTests(unittest.TestCase):
    def test_reinstall_restores_failure_policy_without_duplicating_hooks(self) -> None:
        for prior_policy in (None, "ignore"):
            with self.subTest(prior_policy=prior_policy), tempfile.TemporaryDirectory() as temp:
                env = {**os.environ, "HOME": temp}
                first = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True,
                                       env=env, check=False, timeout=5)
                self.assertEqual(first.returncode, 0, first.stderr.decode())
                settings = Path(temp) / ".claude" / "settings.json"
                parsed = json.loads(settings.read_text(encoding="utf-8"))
                handler = parsed["hooks"]["PreToolUse"][0]["hooks"][0]
                handler.pop("onFailure")
                if prior_policy is not None:
                    handler["onFailure"] = prior_policy
                handler["timeout"] = 17
                unrelated = {"matcher": "Read", "hooks": [{"type": "command", "command": "true"}]}
                parsed["hooks"]["PreToolUse"].append(unrelated)
                settings.write_text(json.dumps(parsed), encoding="utf-8")
                second = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True,
                                        env=env, check=False, timeout=5)
                self.assertEqual(second.returncode, 0, second.stderr.decode())
                groups = json.loads(settings.read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
                self.assertEqual(len(groups), 2)
                self.assertEqual(groups[1], unrelated)
                self.assertEqual(groups[0]["hooks"][0]["timeout"], 17)
                self.assertEqual(groups[0]["hooks"][0].get("onFailure"), "block")

    def test_fifo_hook_path_is_rejected_promptly_without_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            hooks = Path(temp) / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            target = hooks / "command_guard.py"
            os.mkfifo(target)
            try:
                result = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True,
                                        env={**os.environ, "HOME": temp}, check=False, timeout=3)
            except subprocess.TimeoutExpired:
                self.fail("installer blocked while opening a FIFO hook path")
            self.assertEqual(result.returncode, 1)
            self.assertIn(b"unsafe hook path", result.stderr)
            self.assertTrue(stat.S_ISFIFO(target.lstat().st_mode))
            self.assertFalse((hooks.parent / "settings.json").exists())

    def test_installer_preserves_settings_and_is_idempotent_in_fake_home(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            claude = home / ".claude"
            claude.mkdir()
            existing = {"theme": "dark", "hooks": {"PreToolUse": [{"matcher": "Read", "hooks": []}]}}
            settings = claude / "settings.json"
            settings.write_text(json.dumps(existing), encoding="utf-8")
            env = {**os.environ, "HOME": temp}
            first = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True, env=env, check=False)
            self.assertEqual(first.returncode, 0, first.stderr.decode())
            parsed = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(parsed["theme"], "dark")
            self.assertEqual(parsed["hooks"]["PreToolUse"][0]["matcher"], "Read")
            self.assertEqual(len(parsed["hooks"]["PreToolUse"]), 2)
            installed_hook = claude / "hooks" / "command_guard.py"
            self.assertTrue(installed_hook.exists())
            self.assertTrue(os.access(installed_hook, os.X_OK))

            first_contents = settings.read_text(encoding="utf-8")
            second = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True, env=env, check=False)
            self.assertEqual(second.returncode, 0, second.stderr.decode())
            self.assertEqual(settings.read_text(encoding="utf-8"), first_contents)
            hook_config = parsed["hooks"]["PreToolUse"][1]["hooks"][0]
            self.assertEqual(hook_config["onFailure"], "block")

    def test_invalid_settings_do_not_leave_partial_hook_installation(self) -> None:
        for settings_value in ("{", '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":null}]}}'):
            with self.subTest(settings_value=settings_value), tempfile.TemporaryDirectory() as temp:
                claude = Path(temp) / ".claude"
                claude.mkdir()
                settings = claude / "settings.json"
                settings.write_text(settings_value, encoding="utf-8")
                result = subprocess.run([sys.executable, str(INSTALLER)], capture_output=True,
                                        env={**os.environ, "HOME": temp}, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn(b"Traceback", result.stderr)
                self.assertEqual(settings.read_text(encoding="utf-8"), settings_value)
                self.assertFalse((claude / "hooks" / "command_guard.py").exists())


if __name__ == "__main__":
    unittest.main()
