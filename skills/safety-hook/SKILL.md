---
name: pre-tool-use
description: Blocks destructive bash commands before execution
---

# Safety Hook — Pre-Tool-Use Security Guard

A Claude Code `pre-tool-use` hook that automatically blocks dangerous bash
commands before they can execute. Works silently in the background without
interfering with normal development workflows.

## Installation

**Step 1:** Copy the hook into Claude Code's hooks directory:

```bash
cp hooks/pre-tool-use.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

**Step 2:** Verify it's working by running a blocked command in Claude Code.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Recursive root deletion |
| `rm -rf /*` | Root wildcard deletion |
| `dd if=` | Disk destruction |
| `mkfs.*` | Filesystem formatting |
| `DROP TABLE` | SQL table deletion |
| `TRUNCATE TABLE` | SQL table truncation |
| `DELETE FROM` without WHERE | Mass SQL deletion |
| `git push --force` | Force push |
| `curl ... | bash` | Pipe from internet to shell |
| `chmod -R 777 /` | Permission bombing |
| `:(){ :|:& };:` | Fork bomb |
| `shutdown/reboot/halt` | System shutdown in CI |

## How It Works

The hook receives every tool call as JSON on stdin before execution. It
extracts the bash command and checks it against a list of dangerous patterns.

- **Safe commands** → passes through immediately (0 exit)
- **Dangerous commands** → blocked with clear explanation (1 exit)
- **All blocked attempts** → logged to `~/.claude/hooks/blocked.log`

## Log File

All blocked attempts are recorded in a timestamped log:

```
[2026-01-15T10:30:00Z] [BLOCKED] Recursive root deletion | project=/app | cmd=rm -rf /
[2026-01-15T10:30:05Z] [BLOCKED] Force push to git | project=/app | cmd=git push --force origin main
```

## Temporary Disable

If you need to run a blocked command temporarily:

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
# ... run your command ...
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

## Requirements

- **Bash version**: bash 4+, grep with -P support (Linux/macOS)
- **Python version**: python 3.6+ (cross-platform, including Windows)

## Files

```
├── hooks/
│   ├── pre-tool-use.sh          # Bash implementation
│   └── pre_tool_use.py          # Python implementation (cross-platform)
├── skills/
│   └── safety-hook/
│       └── SKILL.md             # Claude Code skill
└── INSTALL.md                   # 2-command install guide
```
