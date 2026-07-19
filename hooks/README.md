# Destructive Bash Command Safety Hook

A lightweight, zero-dependency Python `pre-tool-use` hook for Claude Code that intercepts and blocks high-risk bash commands before execution.

## Features

- **Blocks Dangerous Commands**:
  - `rm -rf` / `rm -fr` (recursive forced file deletion)
  - `git push --force` / `git push -f` (destructive history rewrite)
  - `DROP TABLE` (SQL table deletion)
  - `TRUNCATE` (SQL table truncation)
  - `DELETE FROM ...` without a `WHERE` clause (unbounded SQL table deletion)
  - `mkfs` / `dd` disk formatting commands
- **Audit Logging**: Logs every blocked command attempt to `~/.claude/hooks/blocked.log` in JSON Lines format (`timestamp`, `command`, `project_path`, `reason`).
- **Claude Feedback**: Returns a clear JSON response instructing Claude why the command was blocked.

## Installation (2 steps)

```bash
mkdir -p ~/.claude/hooks
cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

## Testing

```bash
echo '{"tool":"bash","command":"rm -rf /tmp/test","cwd":"/workspace"}' | python3 ~/.claude/hooks/block_destructive_bash.py
```

Output:
```json
{"decision": "block", "reason": "BLOCKED BY SAFETY HOOK: Recursive forced deletion (rm -rf). Attempted command: `rm -rf /tmp/test`. If this action is intentional, execute manually."}
```
