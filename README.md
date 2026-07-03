# Claude Code Pre-Tool-Use Hook — Destructive Command Blocker

Blocks dangerous bash commands before Claude Code executes them.

## How it works

Claude Code calls this hook via `pre-tool-use` on every `Bash` tool call.
The hook reads `stdin` (JSON from Claude), checks the command against a
blocklist of dangerous patterns, and:

- **exit 0** → command allowed
- **exit 2** → command blocked, stderr message sent back to Claude

Blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Blocked patterns

| Category | Patterns |
|----------|----------|
| Filesystem | `rm -rf`, `chmod -R 777`, `mv ... /dev/null`, `dd` to disk, `mkfs`, `truncate /etc/passwd` |
| Database | `DROP TABLE/DATABASE`, `TRUNCATE`, `DELETE FROM` (no WHERE) |
| Git | `git push --force`, `git reset --hard`, `git clean -fd`, `git branch -D` |
| System | Fork bombs, `sudo rm -rf`, `while true`, `curl | bash`, `netcat` |
| Low-level devices | Formatting tools (`mkfs`), raw writes to `/dev/sd*` |

## Installation (2 commands)

```bash
# 1. Copy the hook
cp hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
chmod +x ~/.claude/hooks/pre_tool_use.py

# 2. Merge the hooks section from settings.json into your
# ~/.claude/settings.json or project-level .claude/settings.json
```

## Log format

```
[2026-06-29T20:30:00Z] BLOCKED: Recursive forced deletion (rm -rf)
  command: rm -rf /home/user/project/node_modules
  project: /home/user/project
```

## Testing

```bash
# Should be BLOCKED (exit code 2):
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' | python3 hooks/pre_tool_use.py; echo "exit: $?"

# Should be ALLOWED (exit code 0):
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre_tool_use.py; echo "exit: $?"
```

Run the automated suite:

```bash
python3 test_hook.py
```

Expected: `23/23 passed`
