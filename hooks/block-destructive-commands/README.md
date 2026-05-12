# 🛡️ Block Destructive Commands — Claude Code Hook

A Claude Code **pre-tool-use** hook that intercepts and blocks dangerous bash commands before they are executed. Protects against accidental data loss from commands like `rm -rf`, `DROP TABLE`, `git push --force`, and more.

> Bounty submission for [Issue #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

## ⚡ Installation (2 commands)

```bash
git clone https://github.com/<your-fork>/claude-builders-bounty.git
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

That's it! The hook is now active for all Claude Code sessions.

## 🔒 What Gets Blocked

| Pattern | Severity | Example |
|---------|----------|---------|
| `rm -rf` | CRITICAL | `rm -rf /`, `sudo rm -rf /home` |
| `DROP TABLE/DATABASE` | CRITICAL | `DROP TABLE users`, `DROP DATABASE prod` |
| `git push --force` | HIGH | `git push --force origin main`, `git push -f` |
| `TRUNCATE` | CRITICAL | `TRUNCATE TABLE orders` |
| `DELETE FROM` (no WHERE) | CRITICAL | `DELETE FROM users;` |
| `mkfs` | CRITICAL | `mkfs.ext4 /dev/sda1` |
| `dd` to device | CRITICAL | `dd if=/dev/zero of=/dev/sda` |
| `chmod -R 777 /` | HIGH | `chmod -R 777 /` |

## ✅ What's NOT Blocked

Safe commands pass through without interference:

- `rm single_file.txt` — single file delete (no `-rf`)
- `git push origin main` — regular push (no `--force`)
- `DELETE FROM users WHERE id = 42;` — targeted delete with WHERE
- `ls -la`, `cat`, `echo`, etc. — all normal commands
- Non-Bash tools (FileWrite, FileRead, etc.) — only Bash is inspected

## 📝 Logging

All blocked attempts are logged in JSON Lines format to:

```
~/.claude/hooks/blocked.log
```

Each log entry contains:

```json
{
  "timestamp": "2026-05-13T00:45:00.000000Z",
  "severity": "CRITICAL",
  "attempted_command": "rm -rf /",
  "reason": "rm -rf (recursive force delete)",
  "project_path": "/Users/you/project"
}
```

## 🧪 Running Tests

```bash
python3 hooks/block-destructive-commands/test_hook.py
```

## 🏗️ How It Works

1. Claude Code calls the hook with JSON on stdin before executing any tool
2. The hook checks if the tool is a Bash command
3. If the command matches a destructive pattern, it returns `{"decision": "block", "reason": "..."}` 
4. If the command is safe, it outputs nothing (implicit allow)
5. Blocked attempts are logged to `~/.claude/hooks/blocked.log`

### Hook Input Format

```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /" }
}
```

### Block Response

```json
{
  "decision": "block",
  "reason": "🚫 BLOCKED [CRITICAL]: rm -rf (recursive force delete)..."
}
```

## 📋 Requirements

- Python 3.8+
- No external dependencies (stdlib only)

## 📄 License

MIT
