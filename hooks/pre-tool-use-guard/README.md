# Claude Code `PreToolUse` Destructive Bash Guard Hook

Intercepts destructive shell/SQL commands before Claude Code executes them (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause), logs every blocked attempt to `~/.claude/hooks/blocked.log`, and returns a structured explanation to Claude.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
cp settings.example.json ~/.claude/settings.json
```

## Features & Acceptance Criteria
- **Claude Code Hooks Format**: Reads `PreToolUse` JSON payload (`tool_name`, `tool_input.command`, `cwd`) from `stdin` and returns exit code `2` with `{"decision": "block", "reason": "..."}` when blocked, or `0` for normal commands.
- **Blocked Patterns**:
  - `rm -rf` / `rm -fr` / `rm --recursive --force`
  - `DROP TABLE`
  - `git push --force` / `git push -f`
  - `TRUNCATE` / `TRUNCATE TABLE`
  - `DELETE FROM <table>` without a `WHERE` clause (`DELETE FROM orders WHERE id = 42` is allowed)
- **Audit Logging**: Appends `[ISO-8601 timestamp] RULE=<rule> | PROJECT=<path> | COMMAND=<cmd>` to `~/.claude/hooks/blocked.log`.
