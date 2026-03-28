# Claude Code Anti-Destructive Hook

A `PreToolUse` hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code) that **intercepts dangerous commands before they execute** — giving you a safety net against irreversible operations.

## What it blocks

| Pattern | Why it's dangerous |
|---|---|
| `rm -rf` | Recursive forced deletion — can wipe your entire filesystem |
| `DROP TABLE` | Permanently destroys a database table and all its data |
| `DROP DATABASE` | Permanently destroys an entire database and all its contents |
| `DROP SCHEMA` | Permanently destroys a database schema and everything it contains |
| `git push --force` / `-f` | Rewrites remote history, destroying commits for all collaborators |
| `TRUNCATE` | Removes all rows from a table instantly, usually non-rollbackable |
| `DELETE FROM` without `WHERE` | Deletes every row in a table |
| Fork bomb `:(){ :|:& };:` | Recursively spawns processes until the system crashes |
| `mkfs.*` | Formats a block device — destroys all data on it |
| `dd ... of=/dev/...` | Writes directly to a block device — can destroy disks |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp, the command, and the project path.

## Installation

```bash
git clone https://github.com/pino12033/claude-builders-bounty.git && cd claude-builders-bounty
bash bounties/issue-3-hook/install.sh
```

That's it. The hook is immediately active for all Claude Code sessions.

> **Requirements:** Python 3 (pre-installed on macOS/Linux) and `jq` is not required (pure Python).

## How it works

```
Claude wants to run → PreToolUse hook fires → hook.py reads JSON from stdin
                                                      │
                              ┌───────────────────────┴────────────────────────┐
                              │  Checks against dangerous patterns (regex)      │
                              └───────────────────────┬────────────────────────┘
                                                      │
                               safe? → exit 0 (allow) │ dangerous? → deny JSON + log
```

Claude Code passes a JSON object to the hook via stdin:
```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "rm -rf /important/data" },
  "project_path": "/my/project"
}
```

The hook returns a deny decision that Claude Code enforces:
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "⛔ Command blocked: rm -rf detected..."
  }
}
```

Claude receives the reason and stops — it cannot bypass this.

## Uninstall

```bash
bash bounties/issue-3-hook/uninstall.sh
```

## Log format

```
[2025-01-15T14:32:01] BLOCKED | project=/Users/sam/myproject | reason=rm -rf detected | cmd='rm -rf ./dist'
[2025-01-15T14:35:22] BLOCKED | project=/Users/sam/api      | reason=DROP TABLE detected | cmd='mysql -e "DROP TABLE users"'
```

## Files

```
bounties/issue-3-hook/
├── hook.py        # The hook (Python 3, no external deps)
├── install.sh     # Installer — copies hook + registers in settings.json
├── uninstall.sh   # Removes hook and cleans settings.json
└── README.md      # This file
```

## Hook settings entry (for reference)

The installer adds this to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/anti-destructive.py"
          }
        ]
      }
    ]
  }
}
```

---

Submitted for [Opire bounty #3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) — $100 HOOK pre-tool-use anti-destructive.
