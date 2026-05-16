# Block Destructive Bash Hook

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

From this repository:

```bash
python3 hooks/block_destructive_bash/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive_bash.py` and adds a Bash-only `PreToolUse` hook to `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`, including split flags such as `rm -r -f` and long flags such as `rm --recursive --force`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- SQL containing `DELETE FROM` without a `WHERE` clause in the same statement

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- Attempted command
- Project path
- Rule and reason

## Manual Settings

If you do not want the installer to edit settings, copy the hook yourself and merge this into `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Local Test

```bash
python3 -m unittest hooks/block_destructive_bash/test_block_destructive_bash.py
```

Example blocked input:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | python3 hooks/block_destructive_bash/block_destructive_bash.py
```

The hook prints a Claude Code deny decision with a clear reason and writes the blocked attempt to the log.
