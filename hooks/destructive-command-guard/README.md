# Destructive Command Guard for Claude Code

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

It blocks:

- `rm -rf` style recursive force deletion
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Installation in 2 commands

Run these from this directory:

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
python3 install_hook.py
```

The installer updates `~/.claude/settings.json` and adds the hook under `PreToolUse` for the `Bash` matcher. Existing settings are preserved.

## Manual settings snippet

If you prefer manual installation, add this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_command_guard.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code sends hook input as JSON. The hook reads the attempted Bash command from common hook payload shapes, including `tool_input.command`, then checks it against destructive patterns. If a command is dangerous, the hook:

1. writes a JSON log entry to `~/.claude/hooks/blocked.log`
2. prints a clear explanation to stderr
3. exits with status `2`, which tells Claude Code to block the tool call

Normal commands exit with status `0` and continue without interference.

## Examples

Blocked:

```bash
rm -rf node_modules
DROP TABLE users;
git push origin main --force
TRUNCATE audit_logs;
DELETE FROM sessions;
```

Allowed:

```bash
rm -r build
rm -f tmp.txt
git push origin feature-branch
SELECT * FROM users;
DELETE FROM sessions WHERE expires_at < datetime('now');
npm test
```

## Local test

```bash
python3 test_destructive_command_guard.py
```
