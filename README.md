# Pre-Tool-Use Hook: Block Destructive Bash Commands

Claude Code hook that intercepts and blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
curl -sL https://raw.githubusercontent.com/kiknaio/claude-hooks/main/install.sh | bash
```

Or manually:
```bash
mkdir -p ~/.claude/hooks && cp block_dangerous.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_dangerous.py
```

## What it blocks

- `rm -rf` (recursive force delete)
- `DROP TABLE` (database table deletion)
- `git push --force` (force push)
- `TRUNCATE` (table truncation)
- `DELETE FROM` without `WHERE` clause

## How it works

The hook receives JSON input from Claude Code's pre-tool-use event, checks if it's a Bash command, scans for dangerous patterns, and blocks them with a clear message. All blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Log format

```
[2026-05-11T12:00:00.000000] BLOCKED: tool=Bash cmd='rm -rf /' path=/home/user/project
```

## Testing

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"}}' | python3 block_dangerous.py
# Output: {"decision": "block", "reason": "Blocked destructive command: rm -rf (recursive force delete). Use safer alternatives or add explicit safeguards."}
```
