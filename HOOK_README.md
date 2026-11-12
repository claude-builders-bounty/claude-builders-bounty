# Claude Code Pre-Tool-Use Hook — Blocks Destructive Bash Commands

A `pre-tool-use` hook for Claude Code that intercepts dangerous bash commands
before they execute, prevents irreversible data loss, and logs every block.

## What it blocks
- `rm -rf` / `rm -fr` (recursive force delete)
- `DROP TABLE`
- `TRUNCATE TABLE`
- `git push --force` (and force-push refspecs like `+branch:branch`)
- `DELETE FROM` without a `WHERE` clause

## Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_block.py ~/.claude/hooks/pre_tool_use_block.py && chmod +x ~/.claude/hooks/pre_tool_use_block.py
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/pre_tool_use_block.py"}]}
    ]
  }
}
```

## How it works
1. Claude Code sends the tool payload (JSON) to the hook on stdin.
2. The hook inspects `tool_input.command` for dangerous patterns.
3. On a match it logs to `~/.claude/hooks/blocked.log` and returns a
   `permissionDecision: "deny"` payload (exit code 2).
4. Safe commands exit 0 and pass through untouched.

## Block log format
```
2026-11-12T17:27:58Z | project=/path/to/project | reason=recursive force delete (rm -rf) | command=rm -rf /tmp/foo
```

## Test results
9/9 cases pass — dangerous commands (rm -rf, DROP TABLE, git push --force,
DELETE without WHERE, TRUNCATE) are blocked; safe commands (ls, git status,
rm file.txt, DELETE ... WHERE id=1) pass through.
