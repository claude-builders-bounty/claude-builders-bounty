# 🛡️ Block Destructive Bash Commands — Claude Code Hook

A **PreToolUse hook** for [Claude Code](https://claude.ai/code) that intercepts and blocks destructive bash commands before they execute. Configurable allowlist, detailed logging, and clear explanations for every blocked command.

## Installation

### 1. Copy the hook script

```bash
mkdir -p ~/.claude/hooks && cp block-destructive-commands.py ~/.claude/hooks/
```

### 2. Add the hook configuration

Add this to `~/.claude/settings.json` (global) or `.claude/settings.json` (per-project):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive-commands.py"
          }
        ]
      }
    ]
  }
}
```

**Done!** Claude Code will now automatically check every bash command before it runs.

---

## What It Blocks

| Category | Patterns |
|----------|----------|
| 🗑️ **Filesystem destruction** | `rm -rf`, `rm -rf /`, recursive force deletes |
| 💾 **Disk/block device ops** | `dd`, `mkfs`, `mkfs.ext*`, `format`, `fdisk`, `parted`, `wipefs`, `shred` |
| 🔓 **Permission abuse** | `chmod -R 777`, `chown -R` |
| 💥 **Fork bomb** | `:(){ ... }` |
| 🏠 **Root moves** | `mv /`, moving dirs to `/dev/null` |
| 🖥️ **System commands** | `reboot`, `shutdown`, `halt`, `poweroff`, `init 0/6` |
| 🗄️ **Database destruction** | `DROP DATABASE`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| 🔄 **Git force push** | `git push --force`, `git push -f` |
| 📦 **Piped internet scripts** | `curl ... | bash`, `wget ... | sh` |
| ⚠️ **Dangerous flags** | `rm -rf --no-preserve-root`, `sudo rm`, `sudo dd` |

## What's Allowed by Default

The following safe destructive operations are **always allowed**:
- `rm -rf node_modules/`, `rm -rf .next/`, `rm -rf build/`, `rm -rf dist/`
- `rm -rf .venv/`, `rm -rf __pycache__/`
- `rm -rf /tmp/`, `rm -rf /var/tmp/`
- `dd` writing an ISO to a USB device (basic pattern)

## Customizing the Allowlist

Create `~/.claude/hooks/allowlist.txt` with one regex pattern per line:

```
# Allow rm -rf on my custom build directory
rm -rf custom-out/
# Allow specific git force pushes
git push --force origin main
```

Lines starting with `#` are ignored. Empty lines are ignored.

## Logging

Every blocked command is logged to `~/.claude/hooks/blocked.log` in JSON format:

```json
{"timestamp": "2026-07-03T20:30:00.123456", "command": "rm -rf /", "reason": "rm -rf / — would delete the entire filesystem!", "project_path": "/Users/me/my-project"}
```

## Uninstall

1. Remove the hook config from your settings.json
2. Delete: `rm ~/.claude/hooks/block-destructive-commands.py`

## How It Works

This hook uses Claude Code's [PreToolUse event](https://docs.anthropic.com/en/docs/claude-code/hooks). Before every Bash tool call:

1. Claude Code sends the command as JSON on stdin
2. This script checks the command against 40+ destructive patterns
3. If matched, it checks the allowlist (default + custom)
4. If not allowed, it:
   - Logs the attempt to `blocked.log`
   - Returns a `"deny"` permission decision to Claude Code
   - Shows a clear message explaining why it was blocked

## Requirements

- Python 3.6+
- Claude Code (any version with hook support)

## License

MIT — free to use, modify, and share.
