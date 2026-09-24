# Claude Code Pre-Tool-Use Security Guard Hook

> Bounty Solution for Opire / GitHub Issue #3: `HOOK: Pre-tool-use hook that blocks destructive bash commands` ($100)

A lightweight, zero-dependency Python hook for Claude Code that intercepts and blocks dangerous bash commands before execution and writes audit entries to `~/.claude/hooks/blocked.log`.

## Installation (2 Commands or Fewer)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py
```

## Security Rules Enforced

| Threat Category | Blocked Patterns | Action |
| :--- | :--- | :--- |
| **Recursive File Deletion** | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` | Aborts execution before filesystem changes |
| **Database Destruction** | `DROP TABLE`, `DROP VIEW`, `DROP DATABASE`, `DROP SCHEMA` | Prevents permanent table drop |
| **Git Force Overwrite** | `git push --force`, `git push -f`, `git push ... --force-with-lease` | Prevents overwriting remote history |
| **Table Truncation** | `TRUNCATE TABLE`, `TRUNCATE` | Protects database records |
| **Unbounded SQL Delete** | `DELETE FROM <table>` (without a `WHERE` clause) | Prevents wiping entire tables |

## Audit Logging

Every blocked attempt is recorded in `~/.claude/hooks/blocked.log` with timestamp, matched rule, working directory, and the command string:
```text
[2026-09-24 14:00:00] BLOCKED: rule='Recursive Force Removal (rm -rf)' | path='/home/phil/project' | command='rm -rf ./build'
```

## Pass-Through Verification
Normal commands (`ls`, `git status`, `git push origin main`, `pytest`, `npm test`, `cat`, etc.) pass through with zero latency.
