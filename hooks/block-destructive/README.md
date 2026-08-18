# 🛡️ Block Destructive Bash Commands — Claude Code Hook

A `PreToolUse` hook for Claude Code that intercepts dangerous bash commands before they execute, keeping your system safe from accidental destruction.

## Install (2 commands)

```bash
git clone https://github.com/rifkir23/claude-builders-bounty.git && cd claude-builders-bounty/hooks/block-destructive
bash install.sh
```

That's it. The hook is active immediately for all Claude Code sessions.

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /`, `rm -rf *` | Recursive force delete |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `DROP TABLE` | `DROP TABLE users;` | Destroys database tables |
| `DROP DATABASE` | `DROP DATABASE prod;` | Destroys entire databases |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Wipes all table data |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Deletes all rows |
| `dd if=/dev/zero` | `dd if=/dev/zero of=/dev/sda` | Disk wipe |
| `mkfs` | `mkfs.ext4 /dev/sda1` | Format filesystem |
| `chmod -R 777` | `chmod -R 777 /var/www` | Insecure permissions |
| Fork bomb | `:(){ :\|:& };:` | System crash |

## How it works

```
Claude wants to run: rm -rf node_modules/
                         │
                         ▼
              ┌─────────────────────┐
              │  PreToolUse Hook    │
              │  (block_destructive)│
              └─────────┬───────────┘
                        │
              ┌─────────▼───────────┐
              │  Match against      │
              │  blocked patterns   │
              └─────────┬───────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
     ┌──────▼──────┐       ┌───────▼───────┐
     │   Safe ✅    │       │  Dangerous 🚫 │
     │  (exit 0)   │       │  (deny + log) │
     └─────────────┘       └───────────────┘
```

1. Claude Code calls the `Bash` tool with a command
2. The hook receives the command via stdin (JSON)
3. It checks against all blocked patterns
4. If dangerous: denies execution + logs to `~/.claude/hooks/blocked.log`
5. If safe: exits 0, command proceeds normally

## Log file

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-08-18T12:30:45Z] BLOCKED | reason: rm -rf (recursive force delete) | command: rm -rf / | cwd: /home/user/project
[2026-08-18T12:31:02Z] BLOCKED | reason: git push --force (force push to remote) | command: git push --force origin main | cwd: /home/user/project
```

## Manual installation

If you prefer not to use the install script:

1. Copy `block_destructive.py` to `~/.claude/hooks/`
2. Make it executable: `chmod +x ~/.claude/hooks/block_destructive.py`
3. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Uninstall

```bash
rm ~/.claude/hooks/block_destructive.py
# Then remove the hook entry from ~/.claude/settings.json
```

## Requirements

- Python 3.6+
- Claude Code with hooks support

## License

MIT
