# Pre-Tool-Use Hook — Dangerous Command Blocker

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they execute.

## Features

- Blocks 40+ dangerous command patterns across 7 categories
- Logs every blocked attempt with timestamp, command, and project path
- Clear error messages explaining WHY the command was blocked
- Zero false positives for normal bash commands
- Pure Python — no external dependencies

## Blocked Patterns

| Category | Examples |
|----------|----------|
| 🗑️ Destructive file ops | `rm -rf /`, `rm -rf /etc` |
| 🔥 Force git pushes | `git push --force`, `git reset --hard` |
| 🗄️ Database destruction | `DROP TABLE`, `TRUNCATE`, `DELETE FROM` (no WHERE) |
| ⚙️ System operations | `shutdown`, `reboot`, `dd if=`, `mkfs` |
| 📦 Package removal | `apt remove`, `pip uninstall`, `npm uninstall` |
| 🔒 Permission changes | `chmod 0`, `chown -R` |
| 🛡️ sudo escalation | `sudo rm -rf`, write to `/etc` |

## Installation

**2 commands:**

```bash
mkdir -p ~/.claude/hooks/
cp hooks/pre-tool-use/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py
```

> Claude Code automatically discovers hooks in `~/.claude/hooks/`.

## How It Works

1. Claude Code calls the hook before every `Bash` tool invocation
2. The hook receives the full command as JSON on stdin
3. It checks the command against 40+ blocklist regex patterns
4. If matched → returns `{"is_allowed": False}` with a clear explanation
5. If safe → returns `{"is_allowed": True}` and execution proceeds normally

## Override

If you genuinely need to run a blocked command:

```bash
# Add "#allow" at the start of the command:
#allow rm -rf temp/build/
```

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-25 19:30:00] REASON=Force push blocked | PROJECT=/home/user/my-project | CMD=git push --force origin main
```

## Testing

```bash
# Should block
echo '{"tool":{"name":"Bash","input":{"command":"rm -rf /"}}}' | python3 hooks/pre-tool-use/pre-tool-use.py

# Should allow
echo '{"tool":{"name":"Bash","input":{"command":"ls -la"}}}' | python3 hooks/pre-tool-use/pre-tool-use.py

# Should allow non-Bash tools
echo '{"tool":{"name":"Read","input":{"path":"file.txt"}}}' | python3 hooks/pre-tool-use/pre-tool-use.py
```
