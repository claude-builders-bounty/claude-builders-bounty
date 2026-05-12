# Claude Code Safety Hook — Block Destructive Bash Commands

A pre-tool-use hook for Claude Code that intercepts dangerous bash commands
**before they are executed**, preventing accidental data loss.

## Why

Claude Code can execute arbitrary bash commands. This hook adds a safety net
that catches common destructive patterns before they reach the shell.

## What It Blocks

| Category | Patterns | Risk |
|----------|----------|------|
| Filesystem | `rm -rf`, `rm --no-preserve-root`, `dd if=... of=/dev/sd*`, redirect to `/dev/sda` | Irreversible deletion |
| Database | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` | Permanent data loss |
| Git | `git push --force`, `git push -f` | Overwritten remote history |
| Permissions | `chmod 777 /...`, `chown ... /...` | System compromise |
| System | Fork bomb `:(){ :|:& };:` | Resource exhaustion |

Also **logs** (but doesn't block) `git push --force-with-lease`.

## Install

```bash
# 1. Copy the hook
cp hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py

# 2. Make it executable
chmod +x ~/.claude/hooks/pre_tool_use.py
```

Done. The next time Claude Code tries to run a destructive command,
it will be blocked with a clear explanation.

## How It Works

1. Claude Code calls the hook before every `Bash` tool invocation
2. The hook receives the command via JSON on stdin
3. It checks the command against a regex blocklist
4. If dangerous → logs to `~/.claude/hooks/blocked.log`, returns `{"decision": "block"}`
5. If safe → returns exit code 0 (allow)

## Verify

```bash
# Test that dangerous commands are caught
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' \
  | python3 hooks/pre_tool_use.py
# Expected: {"decision": "block", "reason": "..."}

# Test that safe commands pass through
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' \
  | python3 hooks/pre_tool_use.py
# Expected: exit 0 (no output)
```

## Blocked Attempt Log

All blocked attempts are logged as JSON to `~/.claude/hooks/blocked.log`:

```json
{
  "timestamp": "2026-05-12T09:00:00Z",
  "level": "BLOCK",
  "command": "rm -rf /tmp/old-project",
  "details": "rm -rf (recursive force removal)...",
  "project_path": "/home/user/my-project"
}
```

## Override

This hook blocks commands inside Claude Code **only**. If you're certain
a blocked command is safe, run it manually in your terminal outside
Claude Code.

## License

MIT — same as the parent repository.
