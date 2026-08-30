# Destructive Bash Blocker — Claude Code Pre-Tool-Use Hook

A Python hook that intercepts destructive bash commands **before** Claude Code
executes them, blocks them, and logs every attempt.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_blocker.py ~/.claude/hooks/
```

```bash
# add to ~/.claude/settings.json (merging if it already exists):
```

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre_tool_use_blocker.py" }] }
    ]
  }
}
```

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` (recursive/force) | `rm -rf ./node_modules` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |
| `git push --force` / `-f` | `git push origin main --force` |

Normal bash commands (`ls`, `npm install`, `git add`, etc.) pass through untouched.

## Logging

Every blocked attempt is written to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-08-30T08:00:00Z", "command": "rm -rf ./x", "reason": "...", "project": "/home/user/myproj"}
```

Fields: **timestamp**, **attempted command**, **reason**, **project path**.

## How it works

- Reads the Claude Code `PreToolUse` JSON payload from stdin.
- Only gates `Bash` tool calls with a command string.
- Regex-matches known destructive patterns → `permissionDecision: block` with a
  clear human explanation so Claude corrects its approach.
- Never crashes the tool if logging fails.
- Blocks without a `WHERE` clause on `DELETE FROM` only (scoped deletes are fine).

*Automated hook — real protection, readable logs.*
