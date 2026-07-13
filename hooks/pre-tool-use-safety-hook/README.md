# 🛡️ Claude Code Pre-Tool-Use Safety Hook

> A configurable `PreToolUse` hook that blocks dangerous bash commands before Claude Code executes them.

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](#testing)

Closes **#3** — `[BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands`

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🚫 **Pattern Blocking** | Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` (no WHERE), and more |
| 📋 **Structured Logging** | JSON logs with timestamp, command, matched rule, severity, and project path |
| ⚙️ **Configurable Rules** | Add/remove/modify rules via `hook_config.json` — no code changes needed |
| ✅ **Whitelist Support** | Exempt specific paths or command prefixes from blocking |
| 🎨 **Colour Output** | Clear red/yellow terminal warnings when a command is blocked |
| 🧪 **Dry-Run Mode** | Log dangerous commands without actually blocking them |
| 📦 **Zero Dependencies** | Pure Python 3 stdlib — no `pip install` required |
| 🔄 **Log Rotation** | Automatic rotation when log exceeds configurable size |

---

## 🚀 Quick Install (2 commands)

```bash
git clone https://github.com/sayanget/claude-builders-bounty.git && \
bash claude-builders-bounty/hooks/pre-tool-use-safety-hook/install.sh
```

Or manually:

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks
cp pre_tool_use_hook.py ~/.claude/hooks/
cp hook_config.json ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre_tool_use_hook.py

# 2. Add to Claude Code settings (~/.claude/settings.json)
```

Add this to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_hook.py"
          }
        ]
      }
    ]
  }
}
```

Restart Claude Code and you're protected! 🎉

---

## 🔒 Blocked Patterns

| ID | Pattern | Severity | Example |
|----|---------|----------|---------|
| `rm-rf` | `rm -rf` (recursive force delete) | 🔴 Critical | `rm -rf /`, `rm -rf .` |
| `drop-table` | SQL `DROP TABLE` | 🔴 Critical | `DROP TABLE users` |
| `git-push-force` | `git push --force` / `-f` | 🟠 High | `git push --force origin main` |
| `truncate` | SQL `TRUNCATE` | 🔴 Critical | `TRUNCATE TABLE sessions` |
| `delete-no-where` | `DELETE FROM` without `WHERE` | 🔴 Critical | `DELETE FROM users;` |
| `chmod-777` | World-writable permissions | 🟠 High | `chmod 777 /var/www` |
| `mkfs` | Format filesystem | 🔴 Critical | `mkfs.ext4 /dev/sda1` |
| `dd-of-dev` | Raw disk write | 🔴 Critical | `dd if=/dev/zero of=/dev/sda` |

**Safe commands pass through normally** — `ls`, `git push`, `rm file.txt`, `DELETE FROM users WHERE id=5` are all allowed.

---

## ⚙️ Configuration

Edit `~/.claude/hooks/hook_config.json` to customise behaviour:

### Add a custom rule

```json
{
  "rules": [
    {
      "id": "no-sudo-rm",
      "description": "Block sudo rm",
      "pattern": "\\bsudo\\s+rm\\b",
      "severity": "high",
      "enabled": true
    }
  ]
}
```

### Whitelist a path

```json
{
  "whitelist": {
    "paths": ["/tmp/safe-sandbox"],
    "commands": ["rm -rf /tmp/build-cache"]
  }
}
```

### Enable dry-run mode

```json
{
  "dry_run": true
}
```

In dry-run mode, dangerous commands are **logged but not blocked** — useful for auditing before enforcement.

### Environment variable config path

```bash
export HOOK_CONFIG_PATH=/path/to/custom/hook_config.json
```

---

## 📋 Logging

All blocked commands are logged to `~/.claude/hooks/blocked.log` in structured JSON format:

```json
{
  "timestamp": "2026-07-13T18:30:00.000000+00:00",
  "command": "rm -rf /home/user",
  "rule_id": "rm-rf",
  "rule_description": "Recursive force delete",
  "severity": "critical",
  "project_path": "/home/user/project",
  "dry_run": false
}
```

- **Log rotation**: Automatic rotation when file exceeds `max_size_mb` (default: 10 MB)
- **Disable logging**: Set `"logging": {"enabled": false}` in config

---

## 🧪 Testing

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest test_hook.py -v

# Run with coverage
pip install pytest-cov
pytest test_hook.py -v --cov=pre_tool_use_hook --cov-report=term-missing
```

### Test categories

- ✅ **Dangerous commands** — verifies all required patterns are caught
- ✅ **Safe commands** — verifies normal commands are NOT blocked
- ✅ **Non-Bash tools** — verifies Read/Write/Edit tools pass through
- ✅ **Whitelist** — verifies path and command exemptions work
- ✅ **Dry-run** — verifies dangerous commands are logged but allowed
- ✅ **Logging** — verifies log file creation, format, and rotation
- ✅ **Config loading** — verifies merging defaults with custom config
- ✅ **Edge cases** — multiline, pipes, env vars, disabled rules
- ✅ **Response format** — verifies Claude Code deny JSON structure

---

## 🏗️ Architecture

```
stdin (JSON) → Parse tool_input.command
                    ↓
              Is it a Bash tool?  ── No ──→ exit 0 (allow)
                    ↓ Yes
              Is it whitelisted?  ── Yes ──→ exit 0 (allow)
                    ↓ No
              Match against rules
                    ↓
              Rule matched?  ── No ──→ exit 0 (allow)
                    ↓ Yes
              Log to blocked.log
              Print terminal warning
                    ↓
              Dry-run mode?  ── Yes ──→ exit 0 (allow)
                    ↓ No
              Output deny JSON → exit 2 (blocked)
```

### Files

| File | Purpose |
|------|---------|
| `pre_tool_use_hook.py` | Main hook script — reads stdin, checks rules, outputs decision |
| `hook_config.json` | Configurable rules, whitelist, and logging settings |
| `test_hook.py` | Comprehensive pytest test suite (50+ test cases) |
| `install.sh` | One-command installer with verification |
| `README.md` | This documentation |

---

## 🔗 How It Works with Claude Code

This hook implements the [Claude Code hooks protocol](https://docs.anthropic.com/en/docs/claude-code/hooks):

1. **Event**: Registered for `PreToolUse` with matcher `"Bash"`
2. **Input**: Receives JSON on stdin with `tool_name`, `tool_input.command`, and `project_path`
3. **Decision**: Returns `permissionDecision: "deny"` with a reason to block, or exits silently to allow
4. **Logging**: Every blocked attempt is recorded with full context

The hook **only** inspects `Bash` tool calls — all other tools (Read, Write, Edit, etc.) pass through immediately with zero overhead.

---

## License

MIT — see [LICENSE](../../LICENSE)
