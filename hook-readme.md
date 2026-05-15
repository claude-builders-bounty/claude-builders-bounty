# Block Destructive Bash Commands — Claude Code Hook

A pre-tool-use hook that intercepts and blocks dangerous bash commands before Claude Code executes them.

## Blocked patterns

| Pattern | Why it's dangerous |
|---------|-------------------|
| `rm -rf` | Recursive force delete — irreversible data loss |
| `DROP TABLE/DATABASE` | Destructive SQL DDL — destroys schema and data |
| `TRUNCATE` | Wipes all table data without row-level control |
| `DELETE FROM` without `WHERE` | Deletes every row in the table |
| `DELETE FROM ... WHERE 1=1` | Tautological WHERE — same as no WHERE clause |
| `git push --force` | Rewrites shared git history, destroys others' work |

## Install (2 commands)

```bash
# 1. Copy the hook into your project
cp -r .claude/ /path/to/your/project/

# 2. That's it — Claude Code reads .claude/settings.json automatically
```

If you already have a `.claude/settings.json`, merge the `hooks` key into it:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## How it works

1. Claude Code fires `PreToolUse` before every tool call
2. This hook matches only `Bash` tool calls
3. It reads the command from the JSON input on stdin
4. Checks against the dangerous patterns listed above
5. If matched: returns a `deny` decision with a clear reason, and logs the attempt
6. If not matched: exits cleanly, allowing the command

## Blocked command log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-15T13:00:00Z] BLOCKED | project=/home/user/myapp | command=rm -rf /tmp/build | reason='rm -rf' or variant detected
[2026-05-15T13:05:00Z] BLOCKED | project=/home/user/myapp | command=git push --force origin main | reason='git push --force' detected
```

## Test it

```bash
# Run the hook with a simulated dangerous command
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | bash .claude/hooks/block-destructive.sh

# Expected: JSON deny output + entry in blocked.log

# Run with a safe command
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash .claude/hooks/block-destructive.sh

# Expected: no output (command allowed)
```

## Requirements

- Bash 4+
- jq (for JSON parsing)
