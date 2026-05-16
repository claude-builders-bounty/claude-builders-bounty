# Destructive Bash Command Guard

Claude Code `PreToolUse` hook that inspects Bash tool calls before execution and denies high-risk commands with a structured permission decision.

## Install

From this repository:

```bash
python3 hooks/install.py
```

The installer copies `block_destructive_bash.py` to `~/.claude/hooks/`, makes it executable, and adds a `PreToolUse` Bash matcher to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent `rm -fr`, `rm -Rf`, `rm --recursive --force` forms, including common wrappers like `sudo rm -rf`.
- `git push --force`, `git push --force-with-lease`, and `git push -f`.
- SQL statements containing `DROP TABLE` or `TRUNCATE`.
- `DELETE FROM ...` statements that do not include a `WHERE` clause.

Allowed commands exit with status `0` and no stdout, so normal Bash commands continue without extra context or prompts.

## Blocked Attempt Log

Every blocked command appends one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each entry includes a UTC timestamp, attempted command, project path, and block reason.

## Manual Settings Snippet

If you do not use the installer, add this to `~/.claude/settings.json` after copying the script to `~/.claude/hooks/block_destructive_bash.py`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Quick Check

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' | ~/.claude/hooks/block_destructive_bash.py
```

Expected output contains `permissionDecision: "deny"` and a clear reason for Claude.
