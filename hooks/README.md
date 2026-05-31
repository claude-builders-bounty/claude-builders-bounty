# Claude Code Destructive Bash Blocker

PreToolUse hook for Claude Code that blocks destructive Bash commands before execution and logs every blocked attempt.

## Install

```bash
python3 ~/.claude/hooks/block_destructive_bash.py --install
```

If you are installing from this repository, first copy `block_destructive_bash.py` into `~/.claude/hooks/`, then run the command above.

## What It Blocks

- `rm -rf` and equivalent `rm -fr` flag order.
- `DROP TABLE`.
- `git push --force`, including `--force-with-lease` and `-f`.
- `TRUNCATE`.
- `DELETE FROM` statements that do not include a `WHERE` clause before the statement terminator.

Normal Bash commands pass through without output.

## Log File

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- `timestamp`
- `command`
- `project_path`

## Claude Code Settings

The installer adds this hook entry to `~/.claude/settings.json`. A copy is also available at `settings.example.json`.

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

The actual installed command uses the current Python interpreter and an absolute path.

## Manual Test

Allowed command:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"/tmp/demo"}' | python3 block_destructive_bash.py
```

Blocked command:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/demo"}' | python3 block_destructive_bash.py
```

The blocked command returns a Claude Code denial response with a clear reason.
