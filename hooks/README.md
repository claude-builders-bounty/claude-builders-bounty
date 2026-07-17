# 🛡️ Claude Code PreToolUse Guard Hook

**Bounty #3 — claude-builders-bounty ($100)**

A Python-based `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they execute. Part of the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) program.

## 🚀 Quick Install (2 commands)

```bash
curl -o ~/.claude/hooks/guard-hook.py https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/submissions/003-hook/guard-hook.py
chmod +x ~/.claude/hooks/guard-hook.py
```

Then add this to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/guard-hook.py"
      }
    ]
  }
}
```

Or run the interactive setup:

```bash
./install.sh
```

## 🛡️ Blocked Commands

| Category | Patterns Blocked | Severity |
|----------|-----------------|----------|
| **File Deletion** | `rm -rf`, `rm -r`, `rm -fr`, `find ... -delete` | CRITICAL |
| **SQL Destruction** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE TABLE`, `DELETE FROM` without `WHERE` | CRITICAL |
| **Git Force Push** | `git push --force`, `git push -f`, `git push --force-with-lease`, `git push --delete` | HIGH |
| **Pipe-to-Shell** | `curl ... \| bash`, `wget ... \| sh`, `curl ... \| python` | CRITICAL |
| **Permission Escalation** | `chmod 777`, `chmod -R 777`, `chown -R ... /` | HIGH |
| **Disk Destruction** | `dd ... of=/dev/...`, `mkfs.*` | CRITICAL |
| **System Shutdown** | `shutdown`, `reboot`, `halt`, `poweroff` | HIGH |
| **Fork Bombs** | `:(){ :\|:& };:`, `perl -e ... fork` | CRITICAL |

## 📋 Requirements

- Python 3.8+
- Claude Code (any recent version)
- macOS, Linux, or WSL

## 🧪 Testing

```bash
python3 test_hook.py
```

All 50 tests should pass:

```
Ran 50 tests in ~1.0s
OK
```

## 📊 Logging

Blocked attempts are logged to `~/.claude/hooks/blocked.log` in JSON Lines format:

```json
{
  "timestamp": "2026-07-18T12:34:56.789Z",
  "command": "rm -rf /important/data",
  "project_path": "/Users/dev/my-project",
  "matched_rules": ["rm -rf — recursive forced removal"],
  "severity": "CRITICAL"
}
```

## 🔧 How It Works

1. Claude Code is about to execute a Bash command
2. The `PreToolUse` hook fires and passes JSON to `guard-hook.py` via stdin
3. The script checks the command against 16+ dangerous regex patterns
4. **Safe** → exits 0, command proceeds
5. **Dangerous** → exits 2, command is blocked, Claude sees the explanation

```
┌──────────────┐     JSON stdin      ┌──────────────┐
│  Claude Code  │ ──────────────────> │ guard-hook.py │
│  (PreToolUse) │                     │               │
│               │ <────────────────── │  exit 0: allow │
│               │     exit 2: block   │  exit 2: block │
└──────────────┘                     └──────┬────────┘
                                            │
                                     ┌──────▼────────┐
                                     │  blocked.log   │
                                     └───────────────┘
```

## 📁 Files

```
claude-hook/
├── guard-hook.py    # The hook script
├── install.sh       # Interactive installer
├── test_hook.py     # 50-test suite
└── README.md        # This file
```

## 🔒 Security

- Only intercepts `Bash` tool calls (Write, Read, Edit pass through)
- Uses regex patterns — no `eval()` or code execution
- Logs are written to user's home directory only
- No network access, no external dependencies

## 📝 License

MIT — see the [claude-builders-bounty](https://github.com/claude-builders-bounty/claude-builders-bounty) repo for details.
