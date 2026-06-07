# Destructive Command Blocker

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands before
they execute.

## Blocked Patterns

| Category | Examples Blocked |
|---|---|
| Filesystem | `rm -rf /path`, `dd of=/dev/sda` |
| Database | `DROP TABLE`, `TRUNCATE`, `DELETE FROM x` (no WHERE) |
| Git | `push --force`, `reset --hard`, `checkout -- .`, `clean -fd` |
| Permissions | `chmod 777`, recursive `chown` on `/` |
| Systemd | Disabling `sshd`, `network`, `systemd` services |
| Web | `curl \| bash`, `wget \| sh` (pipe to shell) |
| Fork bomb | `:(){ :\|:& };:` |

## Setup

```bash
# 1. Copy the hook and make executable
cp destructive-command-blocker/block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.py
```

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## How It Works

1. Claude Code sends the Bash command as JSON on stdin
2. The hook checks it against 18+ dangerous patterns
3. If matched: blocks execution, logs the attempt, shows a reason
4. If safe: passes through with no delay

## Blocked Log

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-06-07T12:00:00+00:00", "command": "rm -rf /tmp/*", "reason": "Recursive force remove", "project": "/home/user/project"}
```
