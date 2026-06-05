# Destructive Command Blocker Hook

Claude Code PreToolUse hook that blocks risky Bash commands before they run.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/hooks/destructive-command-blocker && ./install.sh
```

## What It Blocks

- `rm -rf`, including option variants such as `rm -fr`
- SQL `DROP TABLE`
- SQL `TRUNCATE` and `TRUNCATE TABLE`
- SQL `DELETE FROM` statements without a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

When a command is blocked, the hook exits with code `2` so Claude Code blocks the Bash tool call. It logs the attempt to `~/.claude/hooks/blocked.log` as JSON lines with:

- timestamp
- attempted command
- project path
- block reason

## Example Hook Settings

`settings.example.json` contains the Claude Code hook configuration:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python -m unittest discover -s hooks/destructive-command-blocker/tests
```

## Examples

Blocked:

```bash
rm -rf build/
psql "$DATABASE_URL" -c "DROP TABLE users"
sqlite3 app.db "DELETE FROM sessions"
git push --force origin main
```

Allowed:

```bash
rm -r build/
psql "$DATABASE_URL" -c "DELETE FROM sessions WHERE expires_at < now()"
git push origin main
python -m pytest
```
