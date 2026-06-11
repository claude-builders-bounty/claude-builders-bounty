# Destructive Command Guard for Claude Code

This is a Claude Code `PreToolUse` hook for the `Bash` tool. It blocks commands
that are likely to destroy files, database tables, rows, or shared Git history
before Claude Code can execute them.

## What It Blocks

| Pattern | Reason |
| --- | --- |
| `rm -rf`, `rm -fr`, `rm -Rf`, `rm --recursive --force` | Recursive forced deletes can wipe working trees or user files. |
| `DROP TABLE` | Destroys a database table. |
| `TRUNCATE` | Removes all rows from a table. |
| `DELETE FROM ...` without `WHERE` | Deletes all rows from the target table. |
| `git push --force`, `git push -f`, `git push --force-with-lease` | Rewrites remote history in shared repositories. |

Safe Bash commands produce no output and continue through Claude Code's normal
permission flow.

## Install in Two Commands

Run these from the root of the project you want to protect:

```bash
cp -R hooks/pre-tool-use-destructive-command-guard/.claude .
python3 -m unittest discover hooks/pre-tool-use-destructive-command-guard/tests
```

Claude Code reads `.claude/settings.json` automatically for the project. The
settings file registers the hook for `PreToolUse` events whose matcher is
`Bash`, invokes the hook with `python3`, and uses `${CLAUDE_PROJECT_DIR}` so it
still works after Claude changes directories inside the project. The script path
is quoted so projects inside directories with spaces still work.
No executable bit or `chmod` step is required.

## Hook Behavior

Claude Code sends hook input as JSON on stdin. For Bash calls, the attempted
command is read from:

```json
{
  "tool_input": {
    "command": "rm -rf dist"
  }
}
```

When a command is blocked, the hook returns structured JSON on stdout:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Recursive force delete blocked: rm with both recursive and force flags. Refuse the command and suggest a safer, reviewed alternative."
  }
}
```

The hook exits with code `0` and relies on `permissionDecision: "deny"` for a
clear, Claude-readable block reason.

## Blocked Attempt Log

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- UTC timestamp
- attempted command
- project path
- block reason

Example:

```json
{"timestamp":"2026-06-11T09:00:00Z","project_path":"/workspace/app","attempted_command":"git push --force origin main","reason":"Git force push blocked: force-pushing rewrites remote history"}
```

## Test Locally

No third-party packages are required.

```bash
python3 -m unittest discover hooks/pre-tool-use-destructive-command-guard/tests
```

Manual blocked-command check:

```bash
printf '%s\n' '{"tool_input":{"command":"rm -rf dist"},"cwd":"/workspace/app"}' \
  | python3 hooks/pre-tool-use-destructive-command-guard/.claude/hooks/destructive_command_guard.py
```

Manual safe-command check:

```bash
printf '%s\n' '{"tool_input":{"command":"ls -la"},"cwd":"/workspace/app"}' \
  | python3 hooks/pre-tool-use-destructive-command-guard/.claude/hooks/destructive_command_guard.py
```

The safe command should print nothing and exit `0`.
