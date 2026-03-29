# Claude Code Pre-Tool-Use Safety Hook

Blocks dangerous bash commands before Claude Code executes them. Logs every blocked attempt.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Database destruction |
| `TRUNCATE` | Mass row deletion |
| `DELETE FROM` without WHERE | Full table wipe |
| `git push --force` / `-f` | History rewriting |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/YOUR_FORK/hook.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-26T18:00:00] BLOCKED | project=/home/user/myapp | reason=Recursive force delete | command=rm -rf /tmp/test
```

## How It Works

1. Claude Code calls `PreToolUse` hook before every `Bash` tool execution
2. Hook receives JSON on stdin with `tool_name` and `tool_input.command`
3. If command matches a blocked pattern → exits with code `2` (block + message to Claude)
4. Claude sees a clear explanation of why it was blocked and how to fix it
5. Safe commands pass through instantly (exit code `0`)

## Testing

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp"},"cwd":"/home/user"}' | python3 hook.py
echo $?  # should be 2

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/home/user"}' | python3 hook.py  
echo $?  # should be 0
```
