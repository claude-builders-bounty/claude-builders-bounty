# 🛡️ Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) pre-tool-use hook that intercepts dangerous bash commands **before** they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm --recursive --force` | Recursive force delete — can wipe entire directories |
| `DROP TABLE` | SQL table destruction |
| `git push --force` / `git push -f` | Rewrites remote history — dangerous in shared repos |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |

## How it works

1. Intercepts every `Bash` tool call via Claude Code's `PreToolUse` hook
2. Checks the command against destructive patterns
3. **Blocks** the command and shows Claude why it was denied
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with:
   - UTC timestamp
   - Reason for block
   - The attempted command
   - The working directory
5. **Allows** safe commands to pass through unchanged

## Install (2 commands)

```bash
# 1. Copy the hook files into your project
cp -r .claude /path/to/your/project/

# 2. That's it! Claude Code picks up .claude/settings.json automatically
```

Or if you're in your project directory already:

```bash
# Clone and copy
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/bounty && \
cp -r /tmp/bounty/hooks/block-destructive-commands/.claude . && rm -rf /tmp/bounty
```

## Requirements

- **jq** — for JSON parsing (`brew install jq` / `apt install jq`)

## Blocked log

View blocked attempts:

```bash
cat ~/.claude/hooks/blocked.log
```

Example entry:

```
[2026-03-27T01:00:00Z] BLOCKED | Recursive force delete (rm -rf) blocked | Command: rm -rf /tmp/build | PWD: /home/user/project
```

## How to unblock for legitimate use

If you genuinely need a blocked command, run it directly in your terminal outside Claude Code. The hook only intercepts commands **Claude Code** tries to execute — not your own shell.

## Configuration

The hook is configured via `.claude/settings.json` in your project root:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": ".claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## License

MIT
