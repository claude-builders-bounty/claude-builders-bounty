# 🛡️ Safety Hook - Pre-tool-use Protection

A Claude Code hook that blocks destructive bash commands before execution.

## Quick Install (2 Commands)

```bash
# 1. Create hooks directory and download
mkdir -p ~/.claude/hooks/pre-tool-use && \
curl -o ~/.claude/hooks/pre-tool-use/safety-hook.py \
  https://raw.githubusercontent.com/lisaxiao299-maker/claude-builders-bounty/main/hooks/pre-tool-use/safety-hook.py

# 2. Make executable
chmod +x ~/.claude/hooks/pre-tool-use/safety-hook.py
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /folder` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | Database destruction |
| `TRUNCATE` | `TRUNCATE table;` | Delete all rows |
| `DELETE FROM` (no WHERE) | `DELETE FROM users;` | Delete all rows |
| `git push --force` | `git push --force origin main` | Overwrite remote history |
| `git reset --hard` | `git reset --hard HEAD~5` | Lose local changes |
| `dd to device` | `dd if=... of=/dev/sda` | Disk destruction |
| Fork bomb | `:(){ :|:& };:` | System crash |
| `curl | bash` | `curl ... | bash` | Potential malware |

## How It Works

1. Claude tries to run a bash command
2. Hook intercepts before execution
3. Checks against dangerous patterns
4. If dangerous: blocks, logs, shows error
5. If safe: allows execution

## Logs

Blocked commands are logged to:
```
~/.claude/hooks/blocked.log
```

Example log entry:
```
[2026-03-27T17:20:00] BLOCKED: rm -rf (recursive force delete)
  Command: rm -rf /important-folder
  Project: /home/user/my-project
```

## Bypassing

If you're sure a command is safe, run it directly in your terminal (not through Claude).

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use/safety-hook.py
```

## Requirements

- Python 3.6+
- Claude Code with hooks support

## License

MIT