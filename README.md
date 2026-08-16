# claude-code-safety-hook

A `PreToolUse` hook for Claude Code that **blocks destructive bash commands** before they run.

## Setup (2 commands)

```bash
cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
cat >> ~/.claude/settings.json <<'EOF'
{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python ~/.claude/hooks/pre_tool_use.py"}]}]}}
EOF
```

Restart Claude Code — done.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -r` / `rm -rf` | `rm -rf /tmp/build` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE logs;` |
| `DELETE FROM` **without** `WHERE` | `DELETE FROM users;` |
| `git push --force` / `-f` | `git push --force origin main` |
| `mysql ... -e "DROP ..."` | `mysql -e "DROP DATABASE app"` |
| `dd` to raw device | `dd if=x of=/dev/sda` |

Safe commands (e.g. `DELETE FROM users WHERE id=1`) pass through untouched.

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, the attempted command, and the project path. Claude receives a clear explanation of why the command was blocked.

## Test

```bash
python test_hook.py   # 8/8 cases pass
```
