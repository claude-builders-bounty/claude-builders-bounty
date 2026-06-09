# Safe Bash Hook for Claude Code

A `pre-tool-use` hook that intercepts and blocks destructive bash commands before they execute.

## Installation (2 commands)

```bash
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/install.sh | bash
```

That's it. The hook is now active.

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive forced deletion |
| `DROP TABLE` | Destructive SQL |
| `DROP DATABASE` | Destructive SQL |
| `TRUNCATE` | Destructive SQL |
| `DELETE FROM` (no WHERE) | Deletes all rows |
| `git push --force` | Overwrites history |
| `git push -f` | Overwrites history |
| `mkfs` | Formats filesystem |
| `dd of=/dev/` | Overwrites disks |
| `curl \| sh` | Remote code execution |
| `wget \| sh` | Remote code execution |
| `chmod -R 777` | Insecure permissions |
| Fork bomb | Crashes system |

## How it works

1. Claude Code calls the hook before executing any bash command
2. The hook checks the command against blocked patterns
3. If dangerous: command is blocked, logged, and Claude sees a clear message
4. If safe: command proceeds normally

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-06-09 01:30:00 UTC] BLOCKED
  Command: rm -rf /important/dir
  Reason:  rm -rf: Recursive forced deletion
  Project: /home/user/my-project
────────────────────────────────────────────────────────────
```

## Configuration

Create `~/.claude/hooks/config.json` (optional):

```json
{
  "extra_patterns": ["my_dangerous_command"],
  "allow_patterns": ["rm -rf /tmp/safe_dir"],
  "log_file": "~/.claude/hooks/blocked.log"
}
```

- `extra_patterns`: Additional regex patterns to block
- `allow_patterns`: Exceptions (if pattern is in command, it's allowed)
- `log_file`: Custom log file path

## Uninstall

```bash
rm ~/.claude/hooks/pre_tool_use_hook.py
```
