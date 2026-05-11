# Pre-tool-use Guard Hook

A Claude Code `pre-tool-use` hook that blocks destructive bash commands before they execute.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre_tool_use_guard.py \
  https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/submissions/issue3-pre-tool-use-hook/pre_tool_use_guard.py
```

Then add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` / `rm -fr` | Recursive force deletion |
| `DROP TABLE` | Destructive DB operation |
| `TRUNCATE` | Destructive DB operation |
| `DELETE FROM <table>` (no WHERE) | Unscoped deletion |
| `git push --force` / `-f` | Destructive force push |

Safe commands are **not** blocked:
- `rm -f specific_file.txt` — single file removal
- `DELETE FROM logs WHERE created_at < '2020-01-01'` — scoped deletion
- `git push origin feature-branch` — normal push
- `grep -r 'DROP TABLE' .` — searching for patterns

## Blocked Attempt Log

Every blocked command is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-11 23:30:00] BLOCKED: rm -rf: recursive force deletion
  project: /Users/you/my-project
  command: rm -rf ./dist

[2026-05-11 23:31:00] BLOCKED: git push --force: destructive force push
  project: /Users/you/my-project
  command: git push origin main --force
```

## How It Works

Claude Code calls the hook with a JSON payload on stdin before every `Bash` tool call:

```json
{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/foo"}}
```

If the command matches a destructive pattern, the hook outputs:
```json
{"decision": "block", "reason": "...explanation for Claude..."}
```

Claude sees the reason and stops execution — it will not retry the blocked command.

## Tests

```bash
python3 -m pytest tests/ -v
```

All 15 cases pass: 9 blocked, 6 allowed.
