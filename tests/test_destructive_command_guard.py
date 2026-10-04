from __future__ import annotations

import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from hooks.destructive_command_guard import _redact_command_for_log, detect_danger, main
from hooks.install import hook_command, install


class GuardDetectionTests(unittest.TestCase):
    def test_blocks_short_rm_rf_in_shell_chain(self) -> None:
        self.assertIn("rm -rf", detect_danger("printf 'review'; rm -rf ./build"))

    def test_blocks_long_rm_flags_in_any_order(self) -> None:
        self.assertIsNotNone(detect_danger("rm --force --recursive ./tmp"))

    def test_blocks_uppercase_recursive_rm_with_force(self) -> None:
        for command in (
            "rm -Rf ./fixture",
            "rm -fR ./fixture",
            "rm -R -f ./fixture",
            "rm -f -R ./fixture",
            "rm -R --force ./fixture",
            "rm --force -R ./fixture",
            "rm -rRf ./fixture",
            "sudo rm -Rf ./fixture",
            "bash -lc 'rm -Rf ./fixture'",
            "busybox rm -Rf ./fixture",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))

    def test_uppercase_recursive_rm_preserves_safe_boundaries(self) -> None:
        for command in (
            "rm -R ./fixture",
            "rm -f ./fixture",
            "rm -- -Rf",
            "rm -R -- -f",
            "rm -f -- -R",
            "echo 'rm -Rf ./fixture'",
            "printf '%s' 'rm -R --force ./fixture'",
        ):
            with self.subTest(command=command):
                self.assertIsNone(detect_danger(command))

    def test_blocks_force_push(self) -> None:
        self.assertIsNotNone(detect_danger("git -C repo push origin main --force"))
        self.assertIsNotNone(detect_danger("git push --force-with-lease origin main"))
        self.assertIsNotNone(detect_danger("git push --force-with-lease=main origin main"))
        self.assertIsNotNone(detect_danger("git push origin +HEAD:main"))
        self.assertIsNotNone(detect_danger("git -C repo push origin +HEAD:main"))
        self.assertIsNotNone(detect_danger("git push --mirror origin"))
        self.assertIsNotNone(detect_danger("git -c remote.origin.push=+HEAD:main push origin"))
        self.assertIsNotNone(detect_danger("git -cremote.origin.push=+HEAD:main push origin"))
        self.assertIsNotNone(detect_danger("git -c remote.origin.mirror=true push origin"))
        self.assertIsNotNone(
            detect_danger("git --config-env=remote.origin.push=GIT_PUSH_REFSPEC push origin")
        )
        self.assertIsNone(detect_danger("git push origin HEAD:main"))
        self.assertIsNone(detect_danger("git -c remote.origin.push=HEAD:main push origin"))
        self.assertIsNone(detect_danger("git -c remote.origin.mirror=false push origin"))

    def test_blocks_dangerous_commands_inside_shell_wrappers(self) -> None:
        self.assertIsNotNone(detect_danger("bash -lc 'rm -rf ./build'"))
        self.assertIsNotNone(detect_danger("bash -ec 'rm -rf ./build'"))
        self.assertIsNotNone(detect_danger("sh -uc 'git push --force origin main'"))
        self.assertIsNotNone(detect_danger("sh -c 'git push --force origin main'"))
        self.assertIsNotNone(detect_danger("zsh -c 'DELETE FROM accounts'"))

    def test_blocks_commands_after_common_command_wrappers(self) -> None:
        for command in (
            "command rm -rf ./build",
            "command -- rm -rf ./build",
            "sudo -u root rm -rf /tmp/build",
            "sudo --user=root -- git push --force origin main",
            "env DEBUG=1 sudo -u root git push --force origin main",
            "env -S 'rm -rf ./build'",
            "env --split-string='git push --force origin main'",
            "nohup rm -rf ./build",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))
        self.assertIsNone(detect_danger("command echo 'DROP TABLE accounts'"))

    def test_blocks_commands_executed_through_time_eval_find_and_xargs(self) -> None:
        for command in (
            "time rm -rf ./build",
            "nice -n 10 git push --force origin main",
            "timeout --signal=TERM 5s rm -rf ./build",
            "stdbuf -oL git push --force origin main",
            "eval 'rm -rf ./build'",
            "find ./build -exec rm -rf {} +",
            r"find ./build -exec rm -rf {} \;",
            r"find . -exec echo safe \; -exec rm -rf ./build \;",
            r"find . -exec echo safe \; ; rm -rf ./build",
            "find . -exec echo safe + -exec rm -rf ./build +",
            "find ./build -exec sh -c 'rm -rf \"$1\"' sh {} +",
            "xargs -0 -I{} rm -rf < targets.txt",
            "xargs --arg-file targets.txt --no-run-if-empty git push --force origin main",
            "xargs -a targets.txt sh -c 'git push --force origin main' sh",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))

        for command in (
            "time echo 'rm -rf ./build'",
            "eval 'echo safe'",
            "find . -exec echo 'rm -rf ./build' {} +",
            "xargs -I{} echo 'rm -rf ./build' < targets.txt",
        ):
            with self.subTest(command=command):
                self.assertIsNone(detect_danger(command))

    def test_blocks_destructive_commands_through_busybox_applets(self) -> None:
        self.assertIsNotNone(detect_danger("busybox rm -rf ./build"))

    def test_blocks_dangerous_commands_inside_shell_substitutions(self) -> None:
        for command in (
            'echo "$(rm -rf ./build)"',
            "target=$(git push --force origin main)",
            "echo `rm -rf ./build`",
            "cat <(psql -c 'DELETE FROM accounts')",
            "cat >(sqlite3 db.sqlite 'DROP TABLE users')",
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))

    def test_allows_quoted_or_escaped_substitution_examples(self) -> None:
        for command in (
            "echo '$(rm -rf ./build)'",
            'echo "\\$(rm -rf ./build)"',
            "echo '`git push --force origin main`'",
            'echo "literal rm -rf ./build"',
        ):
            with self.subTest(command=command):
                self.assertIsNone(detect_danger(command))

    def test_excessive_shell_nesting_is_blocked_without_recursing_unboundedly(self) -> None:
        command = "echo " + "$(" * 40 + "rm -rf ./build" + ")" * 40
        self.assertIn("inspection limit", detect_danger(command))

    def test_blocks_destructive_sql(self) -> None:
        self.assertIsNotNone(detect_danger("DROP TABLE accounts"))
        self.assertIsNotNone(detect_danger("TRUNCATE TABLE accounts"))
        self.assertIsNotNone(detect_danger("DELETE FROM accounts"))
        self.assertIsNotNone(detect_danger("psql -c 'DROP TABLE accounts'"))

    def test_allows_scoped_delete(self) -> None:
        self.assertIsNone(detect_danger("DELETE FROM accounts WHERE id = 7"))

    def test_blocks_unscoped_delete_before_a_later_where_clause(self) -> None:
        command = "psql -c 'DELETE FROM accounts; SELECT * FROM audit WHERE id = 7'"
        self.assertIsNotNone(detect_danger(command))

    def test_sql_comments_cannot_supply_a_fake_where_clause(self) -> None:
        for command in (
            'mysql -e "DELETE FROM users /* WHERE id = 1 */"',
            'sqlite3 app.db "DELETE FROM users -- WHERE id = 1"',
            'mysql --database=app -e "DELETE FROM users # WHERE id = 1"',
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))
        self.assertIsNone(detect_danger('mysql -e "DELETE FROM users WHERE id = 1"'))

    def test_sql_block_comments_between_delete_and_from_do_not_bypass_guard(self) -> None:
        self.assertIsNotNone(detect_danger('sqlite3 app.db "DELETE /* comment */ FROM users"'))

    def test_sql_strings_and_subqueries_cannot_supply_a_fake_where_clause(self) -> None:
        for command in (
            'psql -c "DELETE FROM accounts RETURNING \'WHERE\'"',
            'psql -c "DELETE FROM accounts USING (SELECT id FROM archive WHERE expired) a"',
            'psql -c "DELETE FROM accounts RETURNING (SELECT id FROM archive WHERE expired)"',
        ):
            with self.subTest(command=command):
                self.assertIsNotNone(detect_danger(command))
        self.assertIsNone(
            detect_danger(
                'psql -c "DELETE FROM accounts WHERE id IN (SELECT id FROM archive)"'
            )
        )

    def test_allows_normal_commands_and_literal_output(self) -> None:
        for command in (
            "git status",
            "rm -r ./build",
            "DEBUG=1",
            "echo 'DROP TABLE accounts'",
            "python -c \"print('DROP TABLE accounts')\"",
            "bash -lc \"echo 'rm -rf ./build'\"",
            "bash -e 'echo safe'",
            "sh -c 'echo DELETE FROM accounts'",
            "npm test",
        ):
            with self.subTest(command=command):
                self.assertIsNone(detect_danger(command))


class HookInvocationTests(unittest.TestCase):
    def test_real_hook_process_handles_uppercase_recursive_rm(self) -> None:
        hook = Path(__file__).resolve().parents[1] / "hooks" / "destructive_command_guard.py"
        for command, denied in (
            ("rm -Rf ./fixture", True),
            ("rm -fR ./fixture", True),
            ("rm -R --force ./fixture", True),
            ("rm -R ./fixture", False),
            ("rm -R -- -f", False),
            ("echo 'rm -Rf ./fixture'", False),
        ):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as directory:
                environment = os.environ.copy()
                log_path = Path(directory) / "blocked.log"
                environment["CLAUDE_HOOK_LOG"] = str(log_path)
                payload = {
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                    "cwd": directory,
                }
                # The shell command is JSON data only, never executed.
                result = subprocess.run(
                    [sys.executable, str(hook)],
                    input=json.dumps(payload),
                    capture_output=True,
                    check=False,
                    env=environment,
                    text=True,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                if denied:
                    self.assertNotEqual(result.stdout, "", "dangerous command was allowed")
                    decision = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(decision["hookEventName"], "PreToolUse")
                    self.assertEqual(decision["permissionDecision"], "deny")
                    self.assertIn("recursive and force", decision["permissionDecisionReason"])
                    records = log_path.read_text(encoding="utf-8").splitlines()
                    self.assertEqual(len(records), 1)
                    record = json.loads(records[0])
                    self.assertEqual(record["attempted_command"], command)
                    self.assertEqual(record["project_path"], directory)
                else:
                    self.assertEqual(result.stdout, "")
                    self.assertFalse(log_path.exists())

    def test_denies_and_logs_blocked_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git push --force origin main"},
                "cwd": "/workspace/example",
            }
            with mock.patch.dict(
                "os.environ",
                {"CLAUDE_HOOKS_DIR": directory},
                clear=False,
            ):
                exit_code = main(io.StringIO(json.dumps(payload)), output)
            self.assertEqual(exit_code, 0)
            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("forced git push", decision["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertIn("Safe alternative", decision["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertIn("new branch", decision["hookSpecificOutput"]["permissionDecisionReason"])
            record = json.loads((Path(directory) / "blocked.log").read_text(encoding="utf-8").strip())
            self.assertEqual(record["attempted_command"], "git push --force origin main")
            self.assertEqual(record["project_path"], "/workspace/example")
            self.assertIn("timestamp", record)

    def test_invalid_json_is_denied_without_echoing_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with mock.patch.dict("os.environ", {"CLAUDE_HOOKS_DIR": directory}, clear=False):
                self.assertEqual(main(io.StringIO('{"command":"secret'), output), 0)
            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("could not be inspected", decision["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertNotIn("secret", output.getvalue())
            record = json.loads((Path(directory) / "blocked.log").read_text(encoding="utf-8").strip())
            self.assertEqual(record["attempted_command"], "[unavailable: invalid hook input]")

    def test_malformed_bash_payload_is_denied(self) -> None:
        for payload in (
            {"tool_name": "Bash"},
            {"tool_name": "Bash", "tool_input": []},
            {"tool_name": "Bash", "tool_input": {"command": 42}},
            {"tool_name": 7, "tool_input": {"command": "rm -rf ./build"}},
        ):
            with self.subTest(payload=payload):
                output = io.StringIO()
                self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
                decision = json.loads(output.getvalue())
                self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_pretooluse_denies_nested_substitution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": 'echo "$(rm -rf ./build)"'},
            }
            with mock.patch.dict("os.environ", {"CLAUDE_HOOKS_DIR": directory}, clear=False):
                self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_redacts_credentials_before_persisting_blocked_command(self) -> None:
        command = (
            "git push --force origin main --token cli-secret "
            '--api-key="key with spaces" PASSWORD=env-secret '
            'Authorization: "basic header-secret" '
            "-H 'X-Trace: Bearer bearer-secret' "
            "https://build-user:url-secret@example.test/repo "
            "github_pat_0123456789abcdefghijklmnop"
        )
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            payload = {"tool_name": "Bash", "tool_input": {"command": command}}
            with mock.patch.dict("os.environ", {"CLAUDE_HOOKS_DIR": directory}, clear=False):
                self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)

            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            log_text = (Path(directory) / "blocked.log").read_text(encoding="utf-8")
            for secret in (
                "cli-secret",
                "key with spaces",
                "env-secret",
                "basic header-secret",
                "bearer-secret",
                "build-user:url-secret",
                "github_pat_0123456789abcdefghijklmnop",
            ):
                with self.subTest(secret=secret):
                    self.assertNotIn(secret, log_text)
            record = json.loads(log_text.strip())
            self.assertIn("--token [REDACTED]", record["attempted_command"])
            self.assertIn('--api-key="[REDACTED]"', record["attempted_command"])
            self.assertIn("PASSWORD=[REDACTED]", record["attempted_command"])
            self.assertIn('X-Trace: Bearer [REDACTED]', record["attempted_command"])
            self.assertIn("https://[REDACTED]@example.test", record["attempted_command"])

    def test_truncates_oversized_commands_in_the_audit_log(self) -> None:
        logged = _redact_command_for_log("rm -rf ./build " + "x" * 5000)
        self.assertLessEqual(len(logged), 4014)
        self.assertTrue(logged.endswith("…[TRUNCATED]"))

    def test_safe_command_is_silent(self) -> None:
        output = io.StringIO()
        payload = {"tool_name": "Bash", "tool_input": {"command": "git status"}}
        self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
        self.assertEqual(output.getvalue(), "")

    def test_cmd_alias_uses_the_same_pretooluse_wire_format(self) -> None:
        output = io.StringIO()
        payload = {"tool_name": "Bash", "tool_input": {"cmd": "rm -rf ./build"}}
        self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
        decision = json.loads(output.getvalue())
        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_logging_failure_still_denies_the_command(self) -> None:
        output = io.StringIO()
        payload = {"tool_name": "Bash", "tool_input": {"command": "DROP TABLE accounts"}}
        with mock.patch("hooks.destructive_command_guard._open_audit_log", side_effect=OSError("disk full")):
            self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
        decision = json.loads(output.getvalue())
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("DROP TABLE", decision["hookSpecificOutput"]["permissionDecisionReason"])

    def test_existing_audit_file_is_secured_or_logged_by_platform(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "blocked.log"
            log_path.write_text("", encoding="utf-8")
            os.chmod(log_path, 0o644)
            payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf ./build"}}
            output = io.StringIO()
            with mock.patch.dict("os.environ", {"CLAUDE_HOOK_LOG": str(log_path)}, clear=False):
                self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
            self.assertTrue(log_path.exists())
            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(log_path.stat().st_mode), 0o600)
            else:
                self.assertIn("attempted_command", log_path.read_text(encoding="utf-8"))

    def test_audit_log_does_not_follow_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "other.log"
            target.write_text("untouched", encoding="utf-8")
            log_path = Path(directory) / "blocked.log"
            log_path.symlink_to(target)
            payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf ./build"}}
            output = io.StringIO()
            with mock.patch.dict("os.environ", {"CLAUDE_HOOK_LOG": str(log_path)}, clear=False):
                if os.name == "nt":
                    # Force the final open to protect against a link swapped
                    # into place after the preliminary path check.
                    with mock.patch.object(Path, "is_symlink", return_value=False):
                        self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
                else:
                    self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
            decision = json.loads(output.getvalue())
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(target.read_text(encoding="utf-8"), "untouched")
            self.assertTrue(log_path.is_symlink())

    def test_non_bash_tool_is_ignored(self) -> None:
        output = io.StringIO()
        payload = {"tool_name": "Read", "tool_input": {"command": "rm -rf /"}}
        self.assertEqual(main(io.StringIO(json.dumps(payload)), output), 0)
        self.assertEqual(output.getvalue(), "")


class InstallerTests(unittest.TestCase):
    def test_installer_preserves_existing_hooks_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings_path = home / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True)
            command = hook_command(home)
            settings_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Read",
                                    "hooks": [{"type": "command", "command": command}],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            install(home)
            install(home)
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(len(settings["hooks"]["PreToolUse"]), 2)
            bash_matchers = [
                matcher
                for matcher in settings["hooks"]["PreToolUse"]
                if matcher.get("matcher") == "Bash"
            ]
            self.assertEqual(len(bash_matchers), 1)
            self.assertEqual(bash_matchers[0]["hooks"], [{"type": "command", "command": command}])
            self.assertTrue((home / ".claude" / "hooks" / "destructive_command_guard.py").exists())

    def test_installer_keeps_existing_settings_if_atomic_replace_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings_path = home / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True)
            original = b'{"custom":true}\n'
            settings_path.write_bytes(original)

            with mock.patch("hooks.install.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaisesRegex(OSError, "replace failed"):
                    install(home)

            self.assertEqual(settings_path.read_bytes(), original)
            self.assertEqual(list(settings_path.parent.glob(".settings.json.*.tmp")), [])

    def test_installer_preserves_existing_settings_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            settings_path = home / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text("{}\n", encoding="utf-8")
            settings_path.chmod(0o640)
            original_mode = stat.S_IMODE(settings_path.stat().st_mode)

            install(home)

            self.assertEqual(stat.S_IMODE(settings_path.stat().st_mode), original_mode)

    def test_installed_hook_processes_real_pretooluse_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installed = install(home)
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": 'echo "$(rm -rf ./build)"'},
                "cwd": str(home),
            }
            environment = os.environ.copy()
            environment["CLAUDE_HOOKS_DIR"] = str(installed.parent)
            result = subprocess.run(
                [sys.executable, str(installed)],
                input=json.dumps(payload),
                capture_output=True,
                check=False,
                env=environment,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertTrue((installed.parent / "blocked.log").is_file())

    def test_registered_bash_matcher_command_is_invocable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            install(home)
            settings = json.loads((home / ".claude" / "settings.json").read_text(encoding="utf-8"))
            matcher = next(
                entry
                for entry in settings["hooks"]["PreToolUse"]
                if entry.get("matcher") == "Bash"
            )
            command = matcher["hooks"][0]["command"]
            payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf ./build"}}
            environment = os.environ.copy()
            environment["CLAUDE_HOOKS_DIR"] = str(home / ".claude" / "hooks")
            result = subprocess.run(
                command,
                input=json.dumps(payload),
                capture_output=True,
                check=False,
                env=environment,
                shell=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_installed_hook_denies_invalid_input_as_pretooluse_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            installed = install(home)
            environment = os.environ.copy()
            environment["CLAUDE_HOOKS_DIR"] = str(installed.parent)
            result = subprocess.run(
                [sys.executable, str(installed)],
                input='{"tool_name":"Bash"}',
                capture_output=True,
                check=False,
                env=environment,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            record = json.loads((installed.parent / "blocked.log").read_text(encoding="utf-8").strip())
            self.assertEqual(record["attempted_command"], "[unavailable: invalid hook input]")


if __name__ == "__main__":
    unittest.main()
