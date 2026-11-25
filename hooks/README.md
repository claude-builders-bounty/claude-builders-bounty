# Pre-tool-use Destructive Command Hook

Claude Code pre-tool-use hook that intercepts destructive Bash commands before they execute.

## Acceptance criteria (claude-builders-bounty/claude-builders-bounty#3)

- [x] Claude Code hooks format (`~/.claude/hooks/`)
- [x] Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- [x] Logs every blocked attempt to `~/.claude/hooks/blocked.log` (timestamp, attempted command, project path)
- [x] Displays a clear message explaining why the command was blocked
- [x] Does not interfere with normal (non-destructive) Bash commands
- [x] README with installation in 2 commands or fewer

## Installation (2 commands)

1. Copy the hook into place:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/pre_tool_use_block_destructive.py
```

2. Register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python ~/.claude/hooks/pre_tool_use_block_destructive.py"
      }
    ]
  }
}
```

## How it works

- Reads the Claude Code `PreToolUse` hook JSON from stdin.
- Extracts the Bash `command` and project `cwd`.
- Matches destructive patterns (case-insensitive): `rm -rf`/recursive delete, `DROP TABLE`, `git push --force`/`-f`/`--force-with-lease`, `TRUNCATE`, `DELETE FROM ...` without `WHERE`.
- On match: appends `{timestamp} | BLOCKED | {reason} | cmd={command} | cwd={path}` to `~/.claude/hooks/blocked.log`, prints a clear rejection message to stderr, exits with code 2 (Claude Code blocks the command and surfaces the message).
- Non-destructive commands return exit 0 and run normally.

## Compliance

- Local only; no network, no secrets, no data exfiltration.
- Does not modify the user's project files.
- Best-effort logging; never blocks on a logging failure.
