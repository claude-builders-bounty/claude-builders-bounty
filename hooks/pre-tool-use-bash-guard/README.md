# Claude Code Pre-Tool-Use Destructive Bash Guard (Bounty #3)

Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause before execution, logs every blocked command to `~/.claude/hooks/blocked.log` (timestamp, attempted command, project path), and returns a clear explanation to Claude.

## Installation (2 Commands)
```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use-bash-guard/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 -c 'import json, pathlib; p=pathlib.Path.home()/".claude/settings.json"; d=json.loads(p.read_text()) if p.exists() else {}; d.setdefault("hooks",{})["PreToolUse"]=[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/block_destructive_bash.py"}]}]; p.write_text(json.dumps(d,indent=2))'
```
