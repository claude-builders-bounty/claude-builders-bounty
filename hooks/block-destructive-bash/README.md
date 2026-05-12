# Destructive Bash Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

From this repository:

```bash
python3 hooks/block-destructive-bash/install.py
```

Restart Claude Code after installing so it reloads `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` variants, including `rm -fr`, `rm -r -f`, and `sudo rm -rf`
- `git push --force` variants, including `git push -f`
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with:

- UTC timestamp
- attempted command
- project path
- block reason

Normal Bash commands exit without output so Claude Code continues normally.

## Claude Code Settings

The installer adds this `PreToolUse` hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/python",
            "args": ["/home/user/.claude/hooks/block_destructive_bash.py"]
          }
        ]
      }
    ]
  }
}
```

The hook follows the Claude Code command-hook format: it receives hook JSON on stdin and, when blocking, returns a `PreToolUse` `permissionDecision` of `deny`.

## Test

```bash
python3 -m unittest hooks/block-destructive-bash/test_block_destructive_bash.py
```
