# Destructive Command Blocker

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## What It Blocks

- Recursive forced deletion through `rm -rf`, `rm -fr`, `rm --recursive --force`, and wrapper commands such as `sudo rm -rf`, `bash -lc "rm -rf ..."`, or `find ... -exec rm -rf`.
- Forced Git pushes through `git push --force`, `git push -f`, `git push --force-with-lease`, and forced refspecs such as `git push origin +main`.
- Direct destructive SQL statements, plus destructive SQL sent to common database clients such as `psql`, `mysql`, `mariadb`, `sqlite3`, `duckdb`, and `sqlcmd`:
  - `DROP TABLE`, `DROP DATABASE`, and `DROP SCHEMA`
  - `TRUNCATE`
  - `DELETE FROM` statements without a `WHERE` clause
  - SQL loaded from explicit local input files such as `psql -f migration.sql`, `sqlcmd -i migration.sql`, `mysql < migration.sql`, and `cat migration.sql | psql`

The detector tokenizes the shell command before matching, so documentation/search commands such as `echo "rm -rf build"`, `grep -R "DROP TABLE" docs`, and `printf "DELETE FROM users" >> examples.sql` are not blocked. SQL file inspection is limited to local files explicitly passed to a recognized database client, and files larger than 1 MiB are skipped to avoid slowing normal Bash usage.

Blocked attempts are appended as JSON lines to `~/.claude/hooks/blocked.log` with the UTC timestamp, severity, rule, reason, evidence, attempted command, and project path.

## Install

```bash
python hooks/destructive-command-blocker/install.py
python hooks/destructive-command-blocker/test_destructive_command_blocker.py
```

The installer copies `destructive-command-blocker.py` into `~/.claude/hooks/` and adds an equivalent Claude Code hook configuration to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/destructive-command-blocker.py"
          }
        ]
      }
    ]
  }
}
```

On Windows, the installer writes a command that invokes the current Python executable explicitly. On macOS/Linux, it writes the copied hook path and marks it executable. Re-running the installer updates the existing hook entry instead of duplicating it.

## Manual Check

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf node_modules","cwd":"/tmp/project"}}' | ~/.claude/hooks/destructive-command-blocker.py
```

Expected output contains `permissionDecision: "deny"` and a clear reason for Claude. Safe Bash commands exit without output so they do not interfere with normal work.

The included tests cover the required acceptance criteria plus wrapper commands, nested shell commands, Git forced refspecs, direct SQL statements, SQL clients, SQL input files and redirections, piped SQL input, false-positive strings, non-Bash tool payloads, invalid input, logging, and installer idempotency.
