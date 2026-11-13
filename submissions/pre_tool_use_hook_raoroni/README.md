# Destructive Bash Command Guard — PreToolUse Hook

A lightweight Python `PreToolUse` hook that intercepts and blocks destructive Bash/SQL/Git commands before execution while allowing safe commands to run uninterrupted.

## Features & Acceptance Criteria Covered

- **Hooks Format:** Reads tool input JSON from `stdin`, returns structured block decision + exit code `2` on violation, and `0` on safe commands.
- **Blocked Patterns:**
  - `rm -rf` (including `-fr`, `-r -f`, `--recursive --force`)
  - `DROP TABLE`
  - `git push --force` / `git push -f`
  - `TRUNCATE` / `TRUNCATE TABLE`
  - `DELETE FROM <table>` without a `WHERE` clause (allows `DELETE FROM <table> WHERE ...`)
- **Audit Logging:** Appends every blocked attempt to `~/.claude/hooks/blocked.log` with ISO-8601 UTC timestamp, project path, and attempted command.
- **Clear Explanation:** Prints a descriptive block reason explaining why the command was prevented.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 -c 'import json, pathlib; p=pathlib.Path.home()/".claude/settings.json"; d=json.loads(p.read_text()) if p.exists() else {}; d.setdefault("hooks",{})["PreToolUse"]=[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block_destructive_bash.py"}]}]; p.write_text(json.dumps(d,indent=2))'
```

