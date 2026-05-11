# Destructive Bash Guard for Claude Code

This is a `PreToolUse` hook for Claude Code's Bash tool. It blocks high-risk commands before they run, logs each blocked attempt, and leaves normal Bash commands alone.

## Install

From this repository:

```bash
python3 .claude/hooks/block_destructive_bash.py --install
```

Restart Claude Code after installing so it reloads `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and equivalent recursive forced `rm` flags such as `rm -fr`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause before the statement boundary

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each log line is JSON with:

- `timestamp`
- `reason`
- `command`
- `project_path`

## Claude Code Hook Format

The installed settings entry is:

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

Claude Code sends hook data as JSON on `stdin`. When this hook finds a dangerous Bash command, it exits with code `2` and writes the reason to `stderr`, which blocks the tool call and gives Claude feedback.

## Quick Verification

Run the included tests:

```bash
python3 -m unittest discover -s tests
```

Manual safe command example:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | python3 .claude/hooks/block_destructive_bash.py
```

Manual blocked command example:

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp"}' | python3 .claude/hooks/block_destructive_bash.py
```

The blocked example exits with code `2` and writes an audit line to `~/.claude/hooks/blocked.log`.
