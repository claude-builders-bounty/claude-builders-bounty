# Claude Code Security Hook

**Blocks destructive bash commands before Claude Code executes them.**

## Installation

```bash
# 1. Copy the hook to Claude's hooks directory
mkdir -p ~/.claude/hooks
cp pre-tool-use-security.py ~/.claude/hooks/pre-tool-use.py
chmod +x ~/.claude/hooks/pre-tool-use.py

# 2. Done! Hook is active immediately.
```

## What It Blocks

- `rm -rf` (recursive force delete)
- `git push --force` / `-f` / `--force-with-lease` (overwrites remote history)
- `DROP TABLE` / `DROP DATABASE` (permanent SQL deletion)
- `TRUNCATE TABLE` (deletes all rows)
- `DELETE FROM` without `WHERE` clause (deletes all rows)

## How It Works

1. **Intercepts** - Runs before every Bash command Claude tries to execute
2. **Checks** - Scans command against dangerous patterns
3. **Blocks** - Prevents dangerous commands and shows clear message to Claude
4. **Logs** - Records every blocked attempt to `~/.claude/hooks/blocked.log`

## Example

When Claude tries to run a dangerous command:

```
Claude: I'll clean up those files
$ rm -rf /important-data

⚠️ BLOCKED: rm -rf (recursive force delete)

Command: rm -rf /important-data

This command has been blocked for safety.
If you need to run it, use the ! prefix to bypass this hook.

Logged to: ~/.claude/hooks/blocked.log
```

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-23T13:45:22] BLOCKED: rm -rf (recursive force delete)
  Command: rm -rf /tmp/test
  Project: /Users/you/project

[2026-04-23T13:47:10] BLOCKED: git push --force (overwrites remote history)
  Command: git push origin main --force
  Project: /Users/you/project
```

## Override

If you need to run a blocked command, use the `!` prefix in Claude Code:

```
! rm -rf /tmp/safe-to-delete
```

This bypasses hooks entirely.

## Testing

Test the hook with safe examples:

```bash
# Safe commands - will pass
echo "rm -rf test" | python3 pre-tool-use-security.py < <(echo '{"tool":{"name":"Bash","input":{"command":"echo test"}}}')

# Dangerous command - will block
echo '{"tool":{"name":"Bash","input":{"command":"rm -rf /tmp/data"}}}' | python3 pre-tool-use-security.py
```

## Requirements

- Python 3.6+
- Claude Code 2.0+

## License

MIT
