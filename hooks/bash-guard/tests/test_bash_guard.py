"""Execute installed hook processes with inert command strings; never run them."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".test-tmp"


class InstalledHookTests(unittest.TestCase):
    def setUp(self):
        TEMP_ROOT.mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="guard ", dir=TEMP_ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = self.root / "config spaces ' $ UTF8-é"
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.config), "PYTHONDONTWRITEBYTECODE": "1"}
        self.install()

    def install(self, *arguments, expected=0):
        result = subprocess.run([sys.executable, "-B", str(ROOT / "install_hook.py"), *arguments],
                                env=self.env, capture_output=True, encoding="utf-8", timeout=10)
        self.assertEqual(result.returncode, expected, result.stderr)
        self.assertIsInstance(result.stdout, str)
        self.assertIsInstance(result.stderr, str)
        return result

    def invoke(self, command="git status", **changes):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": command}, "cwd": str(self.root / "project 雪")}
        event.update(changes)
        return self.raw(json.dumps(event, ensure_ascii=False).encode("utf-8"))

    def raw(self, body):
        settings = json.loads((self.config / "settings.json").read_text(encoding="utf-8"))
        hook = settings["hooks"]["PreToolUse"][-1]["hooks"][0]
        # Run the registered command string through a shell, as Claude Code does.
        # The command under inspection is ONLY stdin.
        return subprocess.run(hook["command"], shell=True, input=body,
                              capture_output=True, env=self.env, timeout=10)

    def blocked(self, command, reason):
        result = self.invoke(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(result.stdout, b"", "Expected a deny decision; hook returned no decision")
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(reason, output["permissionDecisionReason"])
        record = self.logs()[-1]
        self.assertEqual(record["command"], command)
        self.assertEqual(record["project_path"], str(self.root / "project 雪"))
        return output

    def allowed(self, command):
        before = self.logs()
        result = self.invoke(command)
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"", b""))
        self.assertEqual(self.logs(), before)

    def logs(self):
        path = self.config / "hooks" / "blocked.log"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []

    def test_rm_recursive_force_variants(self):
        for command in ["rm -rf /example", "rm -fr example", "rm -R -f example", "rm -fR example",
                        "rm --recursive --force example", "rm example -r -f", "rm\t-rf\t'folder space'",
                        "rm -r\\\n-f example", "/bin/rm -rf -- example", "sudo -u root rm -rf example",
                        "env LANG=C command -- rm -rf example", "X=1 rm -rf example",
                        "2>/dev/null rm -rf example", ">out.txt rm -rf example", "\\\nrm -rf example"]:
            with self.subTest(command=command):
                self.blocked(command, "recursive and force")

    def test_rm_nonrecursive_and_option_terminator(self):
        for command in ["rm file.txt", "rm -r example", "rm -f example", "rm -- -rf", "rm -r -- -f"]:
            with self.subTest(command=command):
                self.allowed(command)

    def test_literal_env_split_string_and_time_wrappers(self):
        for command in ["env -S 'rm -rf synthetic-example'",
                        "env --split-string='git push --force'",
                        "time -p rm -rf synthetic-example"]:
            with self.subTest(command=command):
                self.blocked(command, "Blocked:")

    def test_safe_env_split_string_and_time_wrappers(self):
        for command in ["env -S 'git status'", "env --split-string='git push origin main'",
                        "time -p git status", "env -S 'echo \"rm -rf example\"'",
                        "env --split-string 'printf \"%s\" \"git push --force\"'"]:
            with self.subTest(command=command):
                self.allowed(command)

    def test_force_push_variants(self):
        for command in ["git push --force", "git push origin main -f", "git -C 'folder space' push --force",
                        "git -c core.foo=bar push -vf origin main", "git push --force-with-lease=main:abc",
                        "git push --force-with-lease", "git push origin +main:main", "git\tpush\t--force"]:
            with self.subTest(command=command):
                self.blocked(command, "forced update")

    def test_normal_git(self):
        for command in ["git push origin main", "git push --dry-run", "git push --force-if-includes",
                        "git status", "git log --grep='git push --force'", "git add -- --force"]:
            with self.subTest(command=command):
                self.allowed(command)

    def test_drop_table_case_comments_and_space(self):
        for command in ['DROP TABLE users;', 'drop\ttable users', 'psql -c "DrOp /* reason */ TaBlE users"',
                        'mysql --execute="DROP TABLE IF EXISTS users"', "sqlite3 data.db 'DROP TABLE users;'",
                        'psql --command="DROP TABLE users"', 'mysql -e"DROP TABLE users"',
                        "sqlcmd -Q 'drop table users'", "duckdb -c 'DROP TABLE users'", "mariadb -e 'DROP TABLE users'"]:
            with self.subTest(command=command):
                self.blocked(command, "DROP TABLE")

    def test_truncate_sql_and_unix_utility(self):
        for command in ['TRUNCATE TABLE users', 'truncate users', 'psql -c "select 1; TrUnCaTe users;"']:
            with self.subTest(command=command):
                self.blocked(command, "TRUNCATE")
        self.allowed("truncate -s 0 ordinary-file.log")
        self.allowed('mysql -e "SELECT COALESCE(TRUNCATE(12.34, 1), 0)"')

    def test_delete_without_where(self):
        for command in ['DELETE FROM users;', 'delete\nfrom users', "psql -c 'DELETE /* gap */ FROM users;'",
                        'mysql -e "delete from users limit 1;"']:
            with self.subTest(command=command):
                self.blocked(command, "no WHERE")

    def test_delete_with_where_is_undecided(self):
        for command in ['DELETE FROM users WHERE id=7;', "psql -c 'delete from users where id = 1'",
                        'mysql -e "DELETE FROM users WHERE id IN (SELECT id FROM inactive)"',
                        'sqlite3 data.db "DELETE FROM users WHERE note=\'DROP TABLE\';"']:
            with self.subTest(command=command):
                self.allowed(command)

    def test_where_in_other_statement_does_not_count(self):
        for sql in ["SELECT * FROM users WHERE id=1; DELETE FROM users;",
                    "DELETE FROM users; SELECT * FROM users WHERE id=1;",
                    "DELETE FROM users WHERE id=1; DELETE FROM accounts;"]:
            with self.subTest(sql=sql):
                self.blocked("psql -c " + self.shell_quote(sql), "no WHERE")

    def test_where_in_comment_string_or_identifier_does_not_count(self):
        for sql in ["DELETE FROM users -- WHERE id=1", "DELETE FROM users /* WHERE */;",
                    "DELETE FROM users RETURNING 'WHERE'", 'DELETE FROM "WHERE";',
                    "DELETE FROM [WHERE];", "DELETE FROM `WHERE`;", "DELETE FROM users RETURNING $$WHERE$$"]:
            with self.subTest(sql=sql):
                self.blocked("psql -c " + self.shell_quote(sql), "no WHERE")

    def test_where_in_nested_query_does_not_count_for_outer_delete(self):
        self.blocked("psql -c 'DELETE FROM users RETURNING (SELECT id FROM a WHERE id=1)'", "no WHERE")
        self.blocked("psql -c 'WITH x AS (DELETE FROM users RETURNING *) SELECT * FROM x WHERE id=1'", "no WHERE")
        self.allowed("psql -c 'WITH x AS (SELECT id FROM a WHERE id=1) DELETE FROM users WHERE id IN (SELECT id FROM x)'")

    def test_sql_literals_comments_and_quoted_names(self):
        for sql in ["SELECT 'DROP TABLE users; DELETE FROM users; TRUNCATE users'",
                    'SELECT "TRUNCATE" FROM words', "SELECT $$DELETE FROM users$$", "SELECT $tag$DROP TABLE t$tag$",
                    "SELECT 1 /* DELETE FROM users */", "-- DROP TABLE users\nSELECT 1",
                    "SELECT 'it''s a DELETE FROM example'", "SELECT 1 /* outer /* DELETE FROM users */ inner */"]:
            with self.subTest(sql=sql):
                self.allowed("psql -c " + self.shell_quote(sql))

    def test_shell_quoted_mentions_are_not_executed(self):
        for command in ['echo "rm -rf /example"', "printf '%s' 'DROP TABLE users'", "grep 'DELETE FROM' README.md",
                        "echo '$(rm -rf example)'", "echo '`git push --force`'", "# rm -rf example\ngit status",
                        "printf '%s' 'TRUNCATE users'", "echo \"git push --force\"", "echo 'a; rm -rf b'",
                        "echo 'a\nDELETE FROM users'", "cat <<'TEXT'\nrm -rf example\nDROP TABLE users\nTEXT\n"]:
            with self.subTest(command=command):
                self.allowed(command)

    def test_compound_shell_commands(self):
        for command in ["git status; rm -rf example", "true && rm -rf example", "false || rm -rf example",
                        "(rm -rf example)", "if true; then rm -rf example; fi", "echo ok | git push --force"]:
            with self.subTest(command=command):
                self.blocked(command, "Blocked:")

    def test_nested_shell_and_substitutions(self):
        for command in ["bash -c 'rm -rf example'", "sh -lc 'git push --force'", "eval 'rm -rf example'",
                        'echo "$(rm -rf example)"', "echo `git push --force`", "echo $(echo $(rm -rf example))",
                        "bash <<'SCRIPT'\nrm -rf example\nSCRIPT\n", "bash <<< 'rm -rf example'"]:
            with self.subTest(command=command):
                self.blocked(command, "Blocked:")

    def test_sql_here_docs_and_here_strings(self):
        for command in ["psql <<'SQL'\nDELETE FROM users;\nSQL\n", "mysql <<-SQL\n\tDROP TABLE users;\n\tSQL\n",
                        "sqlite3 db <<< 'TRUNCATE users'", "printf '%s' 'DELETE FROM users;' | psql",
                        "echo 'DROP TABLE users;' | mysql"]:
            with self.subTest(command=command):
                self.blocked(command, "Blocked:")
        self.allowed("psql <<'SQL'\nDELETE FROM users WHERE id=1;\nSQL\n")

    def test_unquoted_here_document_expansion_rules(self):
        self.allowed("cat <<TEXT\nIt's ordinary text with an unmatched quote.\nTEXT\n")
        self.blocked("cat <<TEXT\n'$(rm -rf example)'\nTEXT\n", "recursive and force")

    def test_normal_build_commands(self):
        for command in ["ls -la", "python3 -m unittest discover", "npm test && git diff --check", "echo café 雪",
                        "find . -name '*.py'", "printf '%s\\n' done > output.txt", "echo $(date)", "", "# a comment"]:
            with self.subTest(command=command):
                self.allowed(command)

    def test_event_and_tool_filter(self):
        for changes in [{"tool_name": "Read"}, {"hook_event_name": "PostToolUse"}, {"tool_name": "PowerShell"}]:
            with self.subTest(changes=changes):
                result = self.invoke("rm -rf example", **changes)
                self.assertEqual((result.returncode, result.stdout), (0, b""))
        self.assertEqual(self.logs(), [])

    def test_malformed_protocol_is_denied(self):
        for body in [b"", b"not JSON", b"[]", b"null", b"{}", b"\xff", b"x" * (1024 * 1024 + 1)]:
            with self.subTest(body=body[:30]):
                result = self.raw(body)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(len(self.logs()), 7)

    def test_missing_command_and_project_are_denied(self):
        for changes in [{"tool_input": None}, {"tool_input": {}}, {"tool_input": {"command": 123}},
                        {"cwd": ""}, {"cwd": None}, {"cwd": "bad\x00path"}]:
            with self.subTest(changes=changes):
                result = self.invoke(**changes)
                self.assertIn("Cannot inspect", json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"])

    def test_parse_errors_are_denied(self):
        for command in ["echo 'unfinished", "echo $(date", "rm -rf \\", "psql <<SQL\nDELETE FROM users",
                        "psql -c 'SELECT 1 /*! DELETE FROM users */'", "psql -c \"DELETE FROM users /* unfinished\"",
                        "echo\x00unsafe"]:
            with self.subTest(command=command):
                self.blocked(command, "Cannot inspect")

    def test_original_utf8_command_and_project_are_logged_once_per_attempt(self):
        command = "  rm -rf 'résumé 雪'\n# original spacing retained\n"
        self.blocked(command, "recursive and force")
        self.blocked("git push --force", "forced update")
        rows = self.logs()
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows[0]), {"timestamp", "command", "project_path", "reason"})
        self.assertIsNotNone(datetime.fromisoformat(rows[0]["timestamp"]).utcoffset())
        self.assertEqual(rows[0]["command"], command)
        self.assertIn("雪".encode(), (self.config / "hooks" / "blocked.log").read_bytes())

    def test_concurrent_appends_produce_complete_records(self):
        commands = [f"rm -rf 'synthetic-{i}'" for i in range(12)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(self.invoke, commands))
        self.assertTrue(all(item.returncode == 0 for item in results))
        self.assertEqual(sorted(row["command"] for row in self.logs()), sorted(commands))

    def test_log_failure_does_not_allow_command(self):
        (self.config / "hooks" / "blocked.log").mkdir()
        result = self.invoke("rm -rf example")
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("Audit log could not be written", output["permissionDecisionReason"])

    @unittest.skipUnless(os.name == "posix", "POSIX file modes are checked on Linux")
    def test_private_modes_and_log_symlink_refusal(self):
        self.blocked("rm -rf example", "Blocked:")
        for relative, expected in [("settings.json", 0o600), ("hooks/bash_guard.py", 0o700), ("hooks/blocked.log", 0o600)]:
            self.assertEqual(stat.S_IMODE((self.config / relative).stat().st_mode), expected)
        target = self.root / "unrelated.txt"
        target.write_text("unchanged", encoding="utf-8")
        log = self.config / "hooks" / "blocked.log"
        log.unlink()
        log.symlink_to(target)
        result = self.invoke("rm -rf example")
        self.assertIn("Audit log could not be written", json.loads(result.stdout)["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")

    def test_payload_is_never_executed(self):
        sentinel = self.root / "still present.txt"
        sentinel.write_text("keep", encoding="utf-8")
        self.blocked("rm -rf " + self.shell_quote(str(sentinel)), "recursive and force")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
        output = self.root / "must not exist"
        self.allowed("printf changed > " + self.shell_quote(str(output)))
        self.assertFalse(output.exists())

    def test_installer_is_idempotent_and_retains_log(self):
        self.blocked("rm -rf example", "Blocked:")
        original = (self.config / "settings.json").read_bytes()
        log = (self.config / "hooks" / "blocked.log").read_bytes()
        self.install()
        self.assertEqual((self.config / "settings.json").read_bytes(), original)
        self.assertEqual((self.config / "hooks" / "blocked.log").read_bytes(), log)
        self.assertEqual((self.config / "hooks" / "bash_guard.py").read_bytes(), (ROOT / "bash_guard.py").read_bytes())

    def test_installer_preserves_unrelated_settings_and_neighbor_hooks(self):
        path = self.config / "settings.json"
        settings = json.loads(path.read_text(encoding="utf-8"))
        neighbor = {"type": "command", "command": "unrelated-checker", "timeout": 3}
        settings["hooks"]["PreToolUse"][0]["hooks"].append(neighbor)
        settings["hooks"]["PostToolUse"] = [{"matcher": "Write", "hooks": [neighbor]}]
        settings["permissions"] = {"deny": ["Read(.env)"]}
        settings["env"] = {"EXAMPLE": "café"}
        path.write_text(json.dumps(settings), encoding="utf-8")
        self.install()
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["permissions"], settings["permissions"])
        self.assertEqual(result["env"], settings["env"])
        self.assertEqual(result["hooks"]["PostToolUse"], settings["hooks"]["PostToolUse"])
        self.assertEqual(result["hooks"]["PreToolUse"][0]["hooks"], [neighbor])
        self.assertEqual(len(result["hooks"]["PreToolUse"]), 2)
        self.allowed("git status")

    def test_invalid_settings_are_not_replaced(self):
        path = self.config / "settings.json"
        for text in ["not JSON", "[]", '{"hooks":[]}', '{"hooks":{"PreToolUse":{}}}', '{"disableAllHooks":true}']:
            with self.subTest(text=text):
                path.write_text(text, encoding="utf-8")
                self.install(expected=1)
                self.assertEqual(path.read_text(encoding="utf-8"), text)

    def test_explicit_config_overrides_environment(self):
        alternate = self.root / "alternate config"
        self.install("--config-dir", str(alternate))
        self.assertTrue((alternate / "hooks" / "bash_guard.py").is_file())
        self.assertTrue((self.config / "hooks" / "bash_guard.py").is_file())

    def test_registration_uses_portable_single_command_string(self):
        settings = json.loads((self.config / "settings.json").read_text(encoding="utf-8"))
        entry = settings["hooks"]["PreToolUse"][0]
        self.assertEqual(entry["matcher"], "Bash")
        handler = entry["hooks"][0]
        self.assertEqual(set(handler), {"type", "command", "timeout"})
        self.assertEqual(handler["timeout"], 10)
        self.assertIsInstance(handler["command"], str)
        if os.name == "posix":
            self.assertEqual(shlex.split(handler["command"]),
                             [str(Path(sys.executable).resolve()), "-B", str(self.config / "hooks" / "bash_guard.py")])
        # Quoted paths (spaces, quote, dollar, non-ASCII) must survive the shell.
        self.blocked("rm -rf example", "recursive and force")

    def test_launchers_running_rm_rf_are_blocked(self):
        for command in ["find . -exec rm -rf {} +", "find . -name x -execdir rm -rf {} \\;",
                        "find . -type d -ok rm -rf {} ';'", "ls | xargs rm -rf", "echo x | xargs -n 1 rm -rf",
                        "echo x | xargs -I{} rm -rf {}", "echo x | xargs -I {} -- rm -rf {}",
                        "timeout 5 rm -rf x", "timeout -s KILL 5 rm -rf x", "nice rm -rf x", "nice -n 5 rm -rf x",
                        "doas rm -rf x", "doas -u root rm -rf x", "stdbuf -oL rm -rf x",
                        "stdbuf -o L rm -rf x", "nohup rm -rf x", "find . -exec git push --force \\;"]:
            with self.subTest(command=command):
                self.blocked(command, "Blocked:")

    def test_benign_launcher_commands_are_allowed(self):
        for command in ["find . -name x -print", "find . -exec ls {} +", "find . -exec echo rm -rf {} \\;",
                        "xargs echo", "ls | xargs rm", "ls | xargs -n 1 rm -f", "timeout 5 git status",
                        "nice -n 5 make", "doas ls", "stdbuf -oL cat file", "find . -name 'rm -rf'"]:
            with self.subTest(command=command):
                self.allowed(command)

    @staticmethod
    def shell_quote(value):
        return "'" + value.replace("'", "'\"'\"'") + "'"


if __name__ == "__main__":
    unittest.main(verbosity=2)
