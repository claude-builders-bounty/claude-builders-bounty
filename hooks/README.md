# Destructive Command Guard 🛡️

A `pre-tool-use` hook for Claude Code that intercepts and blocks destructive bash commands before they execute.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /` | Irreversible recursive file deletion |
| `DROP TABLE/DATABASE` | `psql -c 'DROP TABLE users'` | SQL schema destruction |
| `TRUNCATE TABLE` | `mysql -e 'TRUNCATE TABLE orders'` | SQL mass data deletion |
| `DELETE FROM` (no WHERE) | `psql -c 'DELETE FROM users'` | SQL mass deletion without filter |
| `git push --force` / `-f` | `git push -f origin main` | Remote history rewrite |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Filesystem formatting |
| `dd of=/dev/*` | `dd if=/dev/zero of=/dev/sda` | Direct disk overwrite |
| `chmod 777` | `chmod 777 /etc/passwd` | Overly permissive file permissions |
| Fork bomb | `:(){ :|:& };:` | System resource exhaustion |
| Device overwrite | `> /dev/sda` | Direct device redirection |

## What it allows

Safe commands pass through without interference:
- `rm file.txt` (single file, no `-rf`)
- `git push origin main` (normal push)
- `git push --force-with-lease` (safe force push)
- `DELETE FROM users WHERE id = 5` (has WHERE clause)
- All non-destructive commands: `ls`, `cat`, `npm`, `pip`, etc.

## Install (2 commands)

```bash
# 1. Copy the hook script
cp hooks/guard.sh ~/.claude/hooks/guard.sh && chmod +x ~/.claude/hooks/guard.sh

# 2. Add to your Claude Code settings (~/.claude/settings.json)
# Merge this into your existing settings:
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tool_name": "Bash" },
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/guard.sh"
          }
        ]
      }
    ]
  }
}
```

That's it! The hook will now intercept every `Bash` tool call and block destructive commands.

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-28T02:15:00Z] BLOCKED | project=/home/user/myapp | command=rm -rf / | reason=Destructive file deletion: 'rm -rf' can irreversibly delete files and directories
```

## Testing

```bash
bash hooks/test/test.sh
```

Output:

```
🛡️ Destructive Command Guard — Test Suite

🔴 Should BLOCK:
  ✓ BLOCKED: rm -rf /
  ✓ BLOCKED: rm -rf /home
  ✓ BLOCKED: rm -fr .
  ✓ BLOCKED: sudo rm -rf
  ✓ BLOCKED: DROP TABLE
  ✓ BLOCKED: DROP DATABASE
  ✓ BLOCKED: TRUNCATE TABLE
  ✓ BLOCKED: DELETE without WHERE
  ✓ BLOCKED: git push --force
  ✓ BLOCKED: git push -f
  ✓ BLOCKED: mkfs
  ✓ BLOCKED: dd of=/dev
  ✓ BLOCKED: chmod 777
  ✓ BLOCKED: fork bomb

🟢 Should ALLOW:
  ✓ ALLOWED: rm single file
  ✓ ALLOWED: rm -r (no -f)
  ✓ ALLOWED: git push
  ✓ ALLOWED: git push --force-with-lease
  ✓ ALLOWED: npm install
  ✓ ALLOWED: pip install
  ✓ ALLOWED: ls -la
  ✓ ALLOWED: cat file
  ✓ ALLOWED: DELETE with WHERE
  ✓ ALLOWED: SELECT
  ✓ ALLOWED: echo
  ✓ ALLOWED: mkdir
  ✓ ALLOWED: chmod 644
  ✓ ALLOWED: git commit

📝 Log output:
  ✓ blocked.log has 14 entries

────────────────────────────────────────
Results: 29 passed, 0 failed
```

## How it works

1. Claude Code calls the `Bash` tool → hook receives JSON on stdin
2. Hook extracts the `command` field from `tool_input`
3. Command is checked against 12 destructive patterns via regex
4. If matched: logs the attempt and outputs `{ "permissionDecision": "deny" }` JSON
5. If safe: exits silently (command proceeds normally)

## Requirements

- Bash 4+
- Python 3 (for JSON parsing from stdin)
- Claude Code with hooks support

## License

MIT
