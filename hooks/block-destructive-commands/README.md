# block-destructive-commands — Claude Code PreToolUse hook

A `PreToolUse` hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks)
that intercepts **dangerous bash commands before they run** and blocks them,
logging every attempt.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` (and `-r -f`, `-fr`, `--recursive --force`) | irreversible recursive delete |
| `git push --force` / `-f` | overwrites remote history (`--force-with-lease` is **allowed**) |
| `DROP TABLE` | permanently drops a DB table |
| `TRUNCATE` | wipes all rows |
| `DELETE FROM ...` **without** a `WHERE` clause | deletes every row |

Safe commands (`rm file`, `git push`, `DELETE ... WHERE ...`, `echo "rm -rf"`,
etc.) pass through untouched.

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as
`timestamp <tab> rule <tab> project-path <tab> command`, and Claude receives a
clear explanation of why the command was blocked.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands/block_destructive_commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_commands.py
```

```bash
cat hooks/block-destructive-commands/settings.snippet.json  # add this "hooks" block to ~/.claude/settings.json
```

That's it. The snippet registers the hook for the `Bash` tool:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/block_destructive_commands.py" }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code passes the tool call as JSON on stdin. The hook reads
`tool_input.command`, checks it against the destructive-pattern rules, and:

- **exit 0** → command is allowed (nothing printed to the model);
- **exit 2** → command is blocked, and the reason on stderr is returned to
  Claude so it can choose a safer alternative.

Logging failures never block the hook, and unparseable / non-Bash payloads are
allowed through so the hook can't wedge normal work.

## Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 hooks/block-destructive-commands/block_destructive_commands.py; echo "exit=$?"   # exit=2 (blocked)
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'   | python3 hooks/block-destructive-commands/block_destructive_commands.py; echo "exit=$?"   # exit=0 (allowed)
```
