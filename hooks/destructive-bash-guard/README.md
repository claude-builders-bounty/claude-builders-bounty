# Destructive Bash Guard

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run. It recognizes the official Claude hook JSON schema, avoids viewer-command false positives such as `echo 'DROP TABLE users'`, and appends one JSON line to `~/.claude/hooks/blocked.log` for every blocked attempt.

## Install

```bash
bash hooks/destructive-bash-guard/install.sh
```

The installer:

1. Copies the executable hook to `~/.claude/hooks/destructive-bash-guard.py`.
2. Adds a Bash-only `PreToolUse` matcher to `~/.claude/settings.json`.
3. Leaves other hook configuration unchanged and does not duplicate the hook if installed again.

Restart Claude Code after installation so it loads the updated settings.

## Blocked Commands

- `rm` when both recursive and force flags are present, including `sudo rm -rf`, `rm -fr`, and `rm -r --force`.
- `git push --force` and `git push -f`.
- `DROP TABLE` and `TRUNCATE` in a SQL client context.
- `DELETE FROM` without a `WHERE` clause in a SQL client context.

The guard only inspects Claude's `Bash` tool. Commands such as `echo 'DROP TABLE users'`, `grep 'DELETE FROM users'`, and `git push --force-with-lease` remain allowed because they do not perform the destructive operation.

It also inspects the command string passed to `bash -c`, `sh -c`, and `zsh -c`.

## Hook Output

Denied requests use Claude Code's structured decision schema:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked because..."
  }
}
```

The log contains the UTC timestamp, attempted command, and project path:

```json
{"timestamp":"2026-10-27T00:00:00.000000+00:00","attempted_command":"rm -rf /tmp/example","project_path":"/project"}
```

## Tests

```bash
python3 hooks/destructive-bash-guard/test-pre-tool-use.py
```
