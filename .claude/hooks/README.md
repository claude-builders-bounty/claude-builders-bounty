# 🛡️ Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands **before** they execute. Written in Python with regex pattern matching, configurable rules, and structured JSON logging.

## 🔒 Blocked Patterns

| Category | Patterns | Examples |
|----------|----------|----------|
| **Filesystem** | `rm -rf`, `rm -r /`, `chmod 777`, `mkfs.*`, `dd of=/dev/*`, redirect to block device, fork bombs | `rm -rf /`, `chmod -R 777 /var/www` |
| **Git** | `git push --force`, `git push --force-with-lease`, `git push +ref` | `git push --force origin main` |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` | `DROP TABLE users;`, `DELETE FROM orders;` |

## 📦 Installation (2 commands)

```bash
# 1. Copy the hook and config into your project
cp -r .claude/ /path/to/your-project/

# 2. Make the hook executable
chmod +x /path/to/your-project/.claude/hooks/block-destructive.py
```

That's it. The next time Claude Code runs a Bash command in that project, the hook will intercept it.

### Global installation (all projects)

```bash
cp .claude/settings.json ~/.claude/settings.json
mkdir -p ~/.claude/hooks
cp .claude/hooks/block-destructive.py ~/.claude/hooks/
cp .claude/hooks/rules.json ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.py
```

## ⚙️ Configuration

Edit `.claude/hooks/rules.json` to customize:

```jsonc
{
  // Add/remove patterns
  "patterns": [
    {
      "name": "my-rule",
      "pattern": "sudo rm -rf /",
      "description": "Absolutely never do this"
    }
  ],

  // Whitelist specific commands (regex)
  "allowed_commands": [
    "git push --force origin feature/.*"
  ],

  // Set to true to ask for confirmation instead of outright denying
  "require_confirmation": false
}
```

### Adding custom patterns

Each pattern has three fields:
- **`name`** — unique identifier (logged and displayed when matched)
- **`pattern`** — Python regex (case-insensitive, unanchored)
- **`description`** — human-readable explanation shown to Claude

### Whitelisting safe commands

Add regex patterns to `allowed_commands` to bypass checks. Useful for:
- Force-pushing to feature branches
- Known-safe `rm` commands
- CI/CD automation commands

### Confirmation mode

Set `require_confirmation: true` to prompt the user instead of outright blocking. The user sees the warning and can choose to proceed.

## 📋 Logging

Every blocked attempt is logged to `.claude/hooks/blocked.log` in JSON-lines format:

```json
{
  "timestamp": "2026-07-05T19:45:00.123456+00:00",
  "level": "BLOCKED",
  "message": "Destructive command intercepted",
  "session_id": "abc123",
  "command": "rm -rf /tmp/build",
  "cwd": "/home/user/my-project",
  "matched_rules": ["rm-recursive-force"],
  "decision": "deny"
}
```

## 🧪 Testing the hook

```bash
# Simulate a Claude Code hook call
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp","session_id":"test"}' \
  | python3 .claude/hooks/block-destructive.py

# Expected output: JSON with permissionDecision "deny"
# Expected log entry in .claude/hooks/blocked.log

# Safe commands pass through
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp","session_id":"test"}' \
  | python3 .claude/hooks/block-destructive.py

# Expected: exit 0, no output
```

## 🏗️ How It Works

```
Claude Code → PreToolUse hook fires
                   ↓
        block-destructive.py reads
        tool_input.command from stdin
                   ↓
        Regex patterns loaded from rules.json
                   ↓
        Command matched? ──No──→ exit 0 (allow)
                   ↓ Yes
        Check allowed_commands whitelist
                   ↓ Not whitelisted
        Log to blocked.log
                   ↓
        Return {permissionDecision: "deny"}
        with reason shown to Claude
```

## 📁 File Structure

```
.claude/
├── settings.json              # Hook registration (Claude Code picks this up)
└── hooks/
    ├── block-destructive.py   # The hook script
    ├── rules.json             # Configurable patterns
    └── blocked.log            # Created at runtime; blocked attempt records
```

## 🔧 Requirements

- Python 3.8+
- No external dependencies (stdlib only)
- Claude Code (any version supporting hooks)

## 📄 License

MIT — same as the parent project.
