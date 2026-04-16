# pre-tool-use-block-destructive

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

| Category | Patterns |
|----------|----------|
| **File system** | `rm -rf`, `shred`, `dd of=/dev/...`, `mkfs`, `chmod 777` |
| **Database** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` (without WHERE) |
| **Git** | `git push --force`, `git clean --force`, `git reset --hard`, deleting `main`/`master` |
| **System** | `shutdown`, `reboot`, `kill -9`, `systemctl stop/disable` |
| **Pipes** | `curl | bash`, `wget | sh` |

## Install

```bash
# 1. Copy the hook files
cp hooks/pre-tool-use-block-destructive.py ~/.claude/hooks/
cp hooks/pre-tool-use-block-destructive.sh ~/.claude/hooks/

# 2. Register the hook with Claude Code
claude hooks set pre-tool-use-block-destructive --type pre-tool-use --command "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"
```

That's it. The hook activates immediately for all new Claude Code sessions.

## How It Works

1. Claude Code sends tool call details as JSON to the hook's stdin
2. The hook inspects `tool_input.command` for blocked patterns
3. If a match is found, it returns `{"decision": "block", "reason": "..."}` and logs to `~/.claude/hooks/blocked.log`
4. Claude receives the block signal and explains to the user why the command was refused
5. Safe commands pass through with `{"decision": "allow"}`

## Log File

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-04-16T18:30:00.000000+00:00] BLOCKED
  tool: Bash
  reason: rm -rf detected
  command: rm -rf /important/data
  cwd: /home/user/project
---
```

## Test

```bash
# Run the test suite
python3 hooks/tests/test_hook.py

# Manual test — should be BLOCKED:
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 hooks/pre-tool-use-block-destructive.py

# Manual test — should be ALLOWED:
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 hooks/pre-tool-use-block-destructive.py

# Manual test — non-Bash tool should be ALLOWED:
echo '{"tool_name":"Read","tool_input":{"file_path":"/etc/passwd"}}' | python3 hooks/pre-tool-use-block-destructive.py
```

## False Positive Handling

- Commands with `--dry-run` flags are always allowed
- The hook only intercepts the `Bash` tool — file reads, edits, and other tools pass through

## Requirements

- Python 3.8+
- Claude Code (for hook registration)
