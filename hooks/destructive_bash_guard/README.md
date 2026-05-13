# Destructive Bash Guard

A Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_bash_guard/destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py && chmod +x ~/.claude/hooks/destructive_bash_guard.py
python3 hooks/destructive_bash_guard/install.py
```

The installer adds a `PreToolUse` hook for the `Bash` tool to `~/.claude/settings.json`.

## What Gets Blocked

| Pattern | Example |
| --- | --- |
| Recursive forced deletes | `rm -rf build`, `sudo rm -Rf /tmp/app` |
| Destructive SQL schema changes | `DROP TABLE users` |
| Table truncation | `TRUNCATE TABLE audit_log` |
| Unscoped row deletion | `DELETE FROM users` |
| Forced Git pushes | `git push --force origin main`, `git push -f` |

Normal Bash commands are allowed. Safer variants such as `DELETE FROM users WHERE id = 1`,
`git push --force-with-lease`, and `rm -r build` do not get blocked by this hook.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- attempted command
- project path
- matched rule
- block reason

## Claude Code Hook Format

The hook reads Claude Code JSON from `stdin`, checks `tool_name == "Bash"`, and inspects
`tool_input.command`. When a command is blocked, it returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Clear block reason shown to Claude"
  }
}
```

This follows Claude Code's current `PreToolUse` decision format and does not interfere with
other tools or safe Bash commands.
