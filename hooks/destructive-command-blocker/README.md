# Destructive Command Blocker Hook

Claude Code `PreToolUse` hook for Bash commands that blocks common destructive patterns before they run.

## Install

```bash
bash hooks/destructive-command-blocker/install_settings.sh
```

## What It Blocks

- `rm -rf` and equivalent `rm -fr` flag combinations, including common executable paths and escaped command names
- `DROP TABLE`
- `TRUNCATE`
- `git push --force` and `git push --force-with-lease`, including Git global options before `push`
- `DELETE FROM` statements that do not include a `WHERE` clause
- `git reset --hard`
- block-device destruction commands such as `dd of=/dev/*`, `mkfs`, and `wipefs`
- remote script execution through `curl | bash` or `wget | sh`

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with:

- timestamp
- attempted command
- project path
- block reason

The hook uses Node's JSON parser (available with Claude Code) so escaped quotes, backslashes, and command newlines cannot bypass JSON payload parsing. Empty, whitespace-only, malformed, or unparseable payloads fail closed with a structured deny response and an audit-log entry. Normal Bash commands and non-Bash tool calls exit successfully without logging.
The SQL checks are scoped to SQL execution contexts or bare SQL statements so harmless commands such as `grep "DROP TABLE" docs` and Unix `truncate -s 0 file` are allowed. SQL comments in a command containing `DELETE FROM` or `DROP TABLE` fail closed for manual review; this intentionally favors safety over allowing commented destructive statements.
On POSIX hosts, the hook and installer request owner-only file modes for blocked-command logs, settings, backups, and the installed hook; settings and backup files are written through unique private temporary files before replacement. Windows access continues to follow inherited filesystem ACLs. The matcher is a conservative pattern guard, not a full Bash parser or sandbox; it does not inspect the contents of arbitrary local scripts passed to an interpreter.

## Claude Code Hook Format

The installer writes this hook into `~/.claude/settings.json`:

If that file already exists, the installer first refreshes `~/.claude/settings.json.bak` from the pre-install settings, then preserves its settings and other hooks while adding this hook idempotently. The backup is replaced atomically, and a symlink or non-file at the backup path is rejected before installation. The installer refuses to overwrite a different hook already installed at the target path (and refuses symlinks), leaving the existing hook and settings unchanged on that conflict.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/block_destructive_bash.sh"
          }
        ]
      }
    ]
  }
}
```

The hook reads Claude Code's JSON payload from stdin. If a dangerous Bash command is detected, it logs the attempt and returns Claude Code's structured deny payload:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: rm -rf recursive deletion. Review the command and rerun only if this destructive action is intentional and safe."
  }
}
```

## Test

```bash
bash hooks/destructive-command-blocker/test_block_destructive_bash.sh
```

The regression script covers required blocked patterns, expanded shell safety patterns, logging fields, the structured `hookSpecificOutput` deny schema, normal Bash passthrough, non-Bash tool passthrough, and SQL-text false-positive guards.
