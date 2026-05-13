# Claude Code Destructive Bash Guard

PreToolUse hook for Claude Code that blocks destructive bash commands before they run.

## Blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE` / `TRUNCATE TABLE`
- `git push --force` and `git push -f`
- `DELETE FROM ...` without a `WHERE` clause

Every blocked attempt is logged to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- `timestamp`
- `project_path`
- `reason`
- `command`

## Install

From your project root:

```bash
mkdir -p .claude/hooks
cp block_destructive_bash.py .claude/hooks/block_destructive_bash.py
chmod +x .claude/hooks/block_destructive_bash.py
```

Add this to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python .claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Safe Example

```bash
npm test
```

Allowed. No output from the hook.

## Blocked Example

```bash
rm -rf ./dist
```

Denied with a clear reason:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Refusing to run recursive force deletion. Review the target path and delete manually if intentional."
  }
}
```

## Test

```bash
python -m unittest discover tests
```

or:

```bash
python -m pytest tests
```

