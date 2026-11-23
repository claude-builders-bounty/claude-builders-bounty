# Claude Code Destructive Bash Command Blocker Hook (Issue #3)

Pre-tool-use security hook that blocks destructive commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause) before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
python3 -c 'import json,pathlib;p=pathlib.Path.home()/".claude/settings.json";d=json.loads(p.read_text()) if p.is_file() else {};d.setdefault("hooks",{})["PreToolUse"]=[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/pre_tool_use.py"}]}];p.write_text(json.dumps(d,indent=2))'
```

## Verification

Run the built-in self-test suite:
```bash
python3 hooks/pre_tool_use.py
```
