# Block Destructive Bash Hook

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they
run.

## Install

From this repository root:

```bash
bash hooks/block-destructive-bash/install.sh
```

Restart Claude Code after installation so it reloads `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent `rm -fr`, `rm -r -f`, `rm --recursive --force`
- `git push --force` and `git push -f`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- SQL containing `DELETE FROM` without a `WHERE` clause in the same statement

Normal commands such as `npm test`, `git status`, `git push origin main`, and
`rm file.txt` are allowed.

## Files Installed

The installer creates:

```text
~/.claude/hooks/block_destructive_bash.py
~/.claude/hooks/blocked.log
```

It also adds this user-level hook configuration to `~/.claude/settings.json`:

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

The installer writes one command string, which matches Claude Code's hook
configuration format. On Windows, it writes `python` instead of `python3` so the
hook uses the standard Python launcher on PATH.

## Log Format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as one JSON
object per line:

```json
{"timestamp":"2026-05-14T19:45:00Z","project_path":"/path/to/project","attempted_command":"rm -rf dist","reason":"rm recursive force"}
```

## Manual Test

```bash
python3 hooks/block-destructive-bash/test_block_destructive_bash.py
```

The test suite covers the required blocked patterns and common allowed commands.
