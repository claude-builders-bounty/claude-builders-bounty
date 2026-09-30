# PreToolUse Bash Guard Hook

A Python Claude Code `PreToolUse` hook that blocks destructive Bash commands while allowing dangerous-looking text that is only data.

## Installation

Two shell commands:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use/hooks/pre_tool_guard.py ~/.claude/hooks/
python3 -c 'import json,pathlib; p=pathlib.Path.home()/".claude/settings.json"; d=json.loads(p.read_text()) if p.exists() else {}; e={"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/pre_tool_guard.py"}]}; a=d.setdefault("hooks",{}).setdefault("PreToolUse",[]); e not in a and a.append(e); p.write_text(json.dumps(d,indent=2))'
```

The resulting registration is equivalent to:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/pre_tool_guard.py"}
        ]
      }
    ]
  }
}
```

## Blocked commands

- `rm` with recursive + force flags (`-rf`, `-fr`, `-r -f`, `--recursive --force`)
- `git push` with exact `--force` or `-f` (not `--force-with-lease`)
- SQL `DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without `WHERE` when passed to a SQL client
- Dangerous commands inside shell chains, `sh`/`bash -c`, command substitution, and backticks

Quoted or echoed text is treated as data unless it occurs in an execution context.

## Logging

Every blocked attempt appends one line to `~/.claude/hooks/blocked.log` containing a UTC timestamp, the original command, and the project path.
