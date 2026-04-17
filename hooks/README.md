# Claude Code Safety Hook — Block Dangerous Bash Commands

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks destructive bash commands before they execute.

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` | `rm -rf /important/dir` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push origin main --force` |
| `TRUNCATE` | `TRUNCATE orders;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions` |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, and the project path.

## Install

```bash
curl -o ~/.claude/hooks/block_dangerous.py https://raw.githubusercontent.com/ArOhBeK/claude-builders-bounty/main/hooks/block_dangerous.py
```

```bash
cat >> ~/.claude/settings.json << 'EOF'
,
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/block_dangerous.py"}]
      }
    ]
  }
EOF
```

> **Tip:** If `~/.claude/settings.json` doesn't exist yet, run `claude` once to generate it, then add the hooks section.

## How it works

Claude Code calls the hook with a JSON payload on stdin before every `Bash` tool use:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf node_modules"}}
```

The hook checks the command against the dangerous patterns. If matched:
- Exits with code `2` (Claude Code interprets this as a block)
- Prints a clear explanation for Claude
- Appends a log entry to `~/.claude/hooks/blocked.log`

Safe commands pass through with exit code `0` and zero overhead.

## Log format

```
[2026-04-17T22:40:00] BLOCKED(rm -rf (recursive force delete)) path='/home/user/project' cmd='rm -rf dist/'
```
