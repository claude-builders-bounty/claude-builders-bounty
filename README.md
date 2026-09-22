# Claude Code Pre-Tool-Use Security Hook

An automatic security hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before execution.

## Blocked Patterns
- `rm -rf` (Recursive forced deletion)
- `DROP TABLE` (Database table drops)
- `git push --force`, `-f`, `--force-with-lease` (Destructive git history rewrites)
- `TRUNCATE [TABLE]` (Full table wipes)
- `DELETE FROM` without a `WHERE` clause (Unbounded deletions)

Blocked attempts are automatically logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path. Safe commands execute normally.

---

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive_commands.py
```

---

## Configuration in Claude Code

Add the hook to your `~/.claude/settings.json` under `hooks`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/block_destructive_commands.py"
      }
    ]
  }
}
```

## Running Tests
Run the test suite to verify all rules:
```bash
python3 test_hook.py
```
