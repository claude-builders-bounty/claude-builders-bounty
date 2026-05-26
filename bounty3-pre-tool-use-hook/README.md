# Pre-Tool-Use Safety Hook for Claude Code

> **Bounty #3** — $100 | [claude-builders-bounty#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)

A Python-based `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute in Claude Code.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -r -f` | Recursive deletion of directories |
| `git push --force` / `git push -f` | Overwriting remote history |
| `DROP TABLE` | SQL table destruction |
| `TRUNCATE TABLE` | SQL table data wipe |
| `DELETE FROM ...` (no WHERE) | Accidental full-table delete |
| `dd ... of=/dev/...` | Irreversible disk overwrite |
| `mkfs` | Filesystem creation (destroys existing data) |
| `chmod -R 777` | Removes all security permissions |
| `shutdown` / `reboot` | System shutdown/reboot |

## How It Works

1. **Hook Protocol**: Integrates with Claude Code's [`PreToolUse`](https://docs.anthropic.com/claude-code/hooks) hook system
2. **Pattern Matching**: Uses regex to detect dangerous command patterns in bash tool invocations
3. **Fail-Safe**: If input can't be parsed or an error occurs, the hook **allows** execution (fail-open)
4. **Smart Allow-list**: Skips blocking for comments, echo statements, and quoted strings containing blocked patterns
5. **Audit Log**: Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, command, and working directory

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/jiangyj545/claude-builders-bounty/main/bounty3-pre-tool-use-hook/pre-tool-use-hook.py -o ~/.claude/hooks/pre-tool-use-hook.py
```

Then add to your `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "bash",
        "hooks": [
          { "command": "python3 ~/.claude/hooks/pre-tool-use-hook.py" }
        ]
      }
    ]
  }
}
```

## Test

```bash
# Test that it blocks
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 ~/.claude/hooks/pre-tool-use-hook.py
# Expected: {"decision":"block","error_message":"🛑 COMMAND BLOCKED..."}

# Test that normal commands pass through
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre-tool-use-hook.py
# Expected: {"decision":"allow"}

# Check blocked log
cat ~/.claude/hooks/blocked.log
```

## Design Decisions

- **Fail-open**: Hook errors don't block legitimate commands — safety without disruption
- **Regex over AST**: Simpler, faster, covers the most common dangerous patterns without requiring a shell parser
- **Allow-list for context**: Patterns inside comments, echo, or quotes are allowed (reduces false positives)
- **Structured JSON output**: Follows Claude Code's hook protocol exactly — returns `{decision: "allow"|"block"}`
