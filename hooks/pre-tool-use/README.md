# pre-tool-use-destroy

> Claude Code pre-tool-use hook that intercepts and blocks destructive bash commands.

## What it does

This hook monitors every `Bash` tool invocation in Claude Code and blocks commands that could cause permanent data loss or disrupt shared resources.

**Blocked patterns:**

| Category | Patterns |
|----------|----------|
| **Recursive delete** | `rm -rf /`, `rm -rf /*` |
| **Database destruction** | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA` |
| **Git history rewrite** | `git push --force`, `git push -f` |
| **Data deletion** | `DELETE FROM` without `WHERE`, `TRUNCATE` |
| **System destruction** | `mkfs`, `dd of=/dev/*`, fork bombs |
| **System shutdown** | `shutdown -h`, `halt`, `poweroff`, `reboot -f` |

**Allowed (safe):**
- `rm -rf ./tmp` — relative path is not a system directory
- `rm -rf "$dir"` — variable expansion is not root
- `DELETE FROM table WHERE id = 1` — has a WHERE clause
- `git push` (without `--force`) — normal push is allowed
- `git push origin --delete branch-name` — branch deletion is separate from force push

## Installation

**2 commands:**

```bash
# 1. Copy the hook to Claude Code's hooks directory
cp -r pre-tool-use ~/.claude/hooks/

# 2. Make scripts executable
chmod +x ~/.claude/hooks/pre-tool-use/pre-tool-use-destroy.sh
chmod +x ~/.claude/hooks/pre-tool-use/destructive-hook.py
```

Or for a specific project only (local hook):

```bash
cp -r pre-tool-use ./.claude/hooks/
chmod +x ./.claude/hooks/pre-tool-use/*.sh ./.claude/hooks/pre-tool-use/*.py
```

## Usage

Once installed, the hook runs automatically on every Claude Code session. No manual activation required.

**When a blocked command is detected:**

```
🚫 COMMAND BLOCKED — DESTRUCTIVE OPERATION DETECTED

The following command was blocked by the pre-tool-use hook:

  git push --force origin main

Located in: /home/user/my-project

Reason(s):
  • Force push — rewrites remote history, can destroy others' work

This command cannot be executed because it poses an unacceptable risk
of permanent data loss or damage to shared resources.
```

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
============================================================
Timestamp: 2026-03-29T12:00:00+00:00
Project:   /home/user/my-project
Blocked Command:
git push --force origin main
Reason(s):
  - Force push — rewrites remote history, can destroy others' work
============================================================
```

## Disabling the Hook

If you need to run a legitimately dangerous command:

```bash
# Move the hook out of the hooks directory temporarily
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled

# Run your command in Claude Code

# Re-enable when done
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

## Files

```
pre-tool-use/
├── README.md                   # This file
├── pre-tool-use-destroy.sh    # Shell wrapper (entry point for Claude Code)
└── destructive-hook.py        # Python implementation (pattern matching + logging)
```

## Requirements

- `bash` 4.0+
- `python3` (or `python`) — for the pattern-matching engine
  - Falls back to allow (fails open) if Python is not available

## How it works

Claude Code hooks are scripts in `~/.claude/hooks/` that run before tool invocations. The naming convention is:

```
{tool-name}-{hook-type}.{sh,py,js}
```

This hook is named `pre-tool-use-destroy.sh`, so it runs before every tool use. It:

1. Reads the tool input JSON from stdin
2. Extracts the bash command
3. Checks against destructive patterns (regex-based)
4. If dangerous: logs to `blocked.log`, prints error, exits 1 (blocks)
5. If safe: exits 0 (allows)

## Contributing

Improvements to patterns or false positive handling welcome — open an issue or PR.
