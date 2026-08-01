# Destructive Command Guard for Claude Code

This repository contains a small `PreToolUse` hook for Claude Code. It denies
the high-risk shell patterns requested by bounty issue #3:

- `rm` with both recursive and force flags, such as `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` when the statement has no `WHERE` clause

Every denied attempt is appended as one JSON record to
`~/.claude/hooks/blocked.log`, including an ISO-8601 UTC timestamp, the
original command, the matched reason, and the project path. Non-matching
commands produce no decision, so Claude Code's normal permission flow remains
in charge.

## Install

From this repository, run one command:

```bash
python3 install.py
```

On Windows, use `py -3 install.py`. The installer copies the hook to
`~/.claude/hooks/block-destructive.py` and merges a `PreToolUse`/`Bash` entry
into `~/.claude/settings.json` without removing existing settings or hooks.

The generated settings entry is equivalent to:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

Claude Code passes the `PreToolUse` event as JSON on stdin. When a command is
blocked, the hook returns the documented `hookSpecificOutput` object with a
`permissionDecision` of `deny` and a reason Claude can act on.

## Test

The test suite uses only Python's standard library:

```bash
python3 -m unittest discover -s tests -v
```

## Safety notes

The detector intentionally errs on the side of blocking the listed destructive
patterns. It never executes the received command, never sends it to a network
service, and still allows ordinary commands such as `pwd`, `ls`, `npm test`, a
plain file removal, a normal push, and a `DELETE FROM ... WHERE ...` statement.
