# Destructive Bash PreToolUse Hook

Claude Code `pre-tool-use` hook that blocks destructive bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py && chmod +x ~/.claude/hooks/block-destructive-bash.py
printf '%s\n' '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/block-destructive-bash.py"}]}]}}' > ~/.claude/settings.json
```

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- timestamp
- attempted command
- blocked pattern
- project path

Safe bash commands return `{"decision":"allow"}` and continue normally.
Blocked commands return both a top-level `decision: "block"` and a `hookSpecificOutput.permissionDecision: "deny"` payload for current Claude Code `PreToolUse` handling.

## Example

Input:

```json
{"tool_input":{"command":"rm -rf build","cwd":"/repo"}}
```

Output:

```json
{
  "decision": "block",
  "reason": "Blocked dangerous bash command pattern `rm -rf`. Recursive force deletion can irreversibly remove project or system files. The attempted command was logged to ~/.claude/hooks/blocked.log.",
  "hookSpecificOutput": {
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked dangerous bash command pattern `rm -rf`. Recursive force deletion can irreversibly remove project or system files. The attempted command was logged to ~/.claude/hooks/blocked.log."
  },
  "attempted_command": "rm -rf build"
}
```
