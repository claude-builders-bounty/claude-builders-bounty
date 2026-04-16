# Block Destructive Commands — Claude Code Hook

A pre-tool-use hook for Claude Code that intercepts and blocks dangerous bash commands before execution.

## Install (2 commands)

```bash
cp block-destructive-commands.sh ~/.claude/hooks/pre-tool-use.sh
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What It Blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /var/data` | Irreversible recursive force delete |
| `DROP TABLE` | `DROP TABLE users` | Permanently deletes database tables |
| `git push --force` | `git push --force origin main` | Overwrites remote history |
| `git push --force-with-lease` | `git push --force-with-lease origin main` | Rewrites remote history even if it feels safer than `--force` |
| `TRUNCATE` | `TRUNCATE TABLE logs` | Empties entire table |
| `DELETE FROM` (no WHERE) | `DELETE FROM users` | Deletes ALL rows without filtering |

## How It Works

1. Claude Code sends tool-use events to the hook via stdin (JSON format)
2. The hook parses the command from `Bash` tool calls
3. If the command matches a dangerous pattern, it's **blocked** with exit code 2
4. The block reason is displayed to Claude
5. The attempt is logged to `~/.claude/hooks/blocked.log`
6. Normal commands pass through unaffected (exit code 0)

## Blocked Command Log

Every blocked attempt is recorded in `~/.claude/hooks/blocked.log`:

```
[2026-04-15 12:34:56] BLOCKED | cmd: rm -rf /var/data | reason: recursive force delete | path: /home/user/project
```

## Allowed Commands

The hook only blocks the specific dangerous patterns above. These are fine:

```bash
rm file.txt              # Single file delete (no -rf)
git push origin main     # Normal push (no --force)
DELETE FROM users WHERE id = 1  # DELETE with WHERE clause
DROP TABLE IF EXISTS temp      # Wait — this IS blocked (intentional safety)
```

## Quick Validation

Run these after installing the hook:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo","workdir":"/repo"}}' | ~/.claude/hooks/pre-tool-use.sh
printf '{"tool_name":"Bash","tool_input":{"command":"git push origin main","workdir":"/repo"}}' | ~/.claude/hooks/pre-tool-use.sh
```

The first command should exit with status `2` and append to `blocked.log`. The second should exit `0`.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use.sh
```

## Override

If you need to run a blocked command, run it directly in your terminal (outside Claude Code). The hook only intercepts Claude's tool-use events.

## Technical Details

- **Format**: Claude Code hooks spec (`~/.claude/hooks/`)
- **Input**: JSON on stdin with `tool_name` and `tool_input.command`
- **Exit codes**: 0 = allow, 2 = block
- **Dependencies**: bash, python3
- **Platform**: macOS / Linux (no GNU `grep -P` required)
