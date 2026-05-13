# Claude Code destructive-command PreToolUse hook

This hook satisfies bounty #3 by blocking destructive Bash commands before Claude Code runs them.

## Files

- `hooks/pre_tool_use_block_destructive.py` — the hook script.
- `tests/test_pre_tool_use_block_destructive.py` — regression tests for the required block/allow behavior.

## Install

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/pre_tool_use_block_destructive.py
chmod +x ~/.claude/hooks/pre_tool_use_block_destructive.py
```

Then add the hook to your Claude Code settings for the Bash tool:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre_tool_use_block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## Blocked patterns

The hook reads the Claude Code hook JSON payload from stdin and inspects `tool_input.command`.
It blocks:

- `rm -rf` and common flag variants such as `rm -fr`, `rm --recursive --force`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` when no `WHERE` appears before the end of the statement/line

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes:

- `timestamp` in UTC ISO-8601 format
- `command`
- `reason`
- `rule`

For tests or custom deployments, override the log destination with `CLAUDE_BLOCKED_LOG`.

## Test

```bash
python3 -m unittest discover -s tests
python3 -m py_compile hooks/pre_tool_use_block_destructive.py tests/test_pre_tool_use_block_destructive.py
git diff --check
```
