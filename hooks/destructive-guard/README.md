# Claude Code — Destructive Bash Guard

A `pre-tool-use` hook for Claude Code that blocks dangerous bash commands before they execute.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /important/folder` |
| `git push --force` / `-f` | `git push --force origin main` |
| `DROP TABLE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions;` |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Install (2 commands)

```bash
git clone https://github.com/LozzKappa/claude-destructive-guard && cd claude-destructive-guard
bash install.sh
```

Then restart Claude Code.

## How it works

The hook reads the tool invocation from stdin as JSON, checks the `command` field against dangerous patterns, and exits with code `2` to block execution if a match is found. Legitimate bash commands pass through unaffected.

## Log format

```
[2026-05-16T10:23:45] BLOCKED: rm -rf
  command: 'rm -rf /tmp/myproject'
  project: /home/user/myproject
```

## Uninstall

Remove the hook entry from `~/.claude/settings.json` under `hooks.PreToolUse` and delete `~/.claude/hooks/pre_tool_use.py`.
