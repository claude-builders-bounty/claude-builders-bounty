# block-destructive (Claude Code PreToolUse hook)

Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and
`DELETE FROM` without `WHERE` before Claude Code can run them.

Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
python3 -c "import json,os,pathlib; p=pathlib.Path.home()/'.claude'/'settings.json'; p.parent.mkdir(parents=True, exist_ok=True); d=json.loads(p.read_text()) if p.exists() else {}; h=d.setdefault('hooks',{}).setdefault('PreToolUse',[]); cmd='python3 '+str(pathlib.Path.home()/'.claude'/'hooks'/'block_destructive.py'); h.append({'matcher':'Bash','hooks':[{'type':'command','command':cmd}]}) if not any(cmd in str(x) for x in h) else None; p.write_text(json.dumps(d, indent=2))"
```

Restart Claude Code. Blocked attempts are appended to `~/.claude/hooks/blocked.log`
as `timestamp<TAB>project_path<TAB>command`.

## What it blocks

| Pattern | Allowed? |
|---|---|
| `rm -rf /tmp/x` | no |
| `git push --force` / `git push -f` | no |
| `DROP TABLE users` | no |
| `TRUNCATE invoices` | no |
| `DELETE FROM users` | no |
| `DELETE FROM users WHERE id=1` | yes |
| `ls`, `git status`, `pytest` | yes |

On a block the hook prints JSON with `permissionDecision: deny` and a reason
Claude can read, then continues (exit 0) so normal commands are untouched.

## Test without Claude Code

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp"}' | python3 block_destructive.py
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' | python3 block_destructive.py; echo exit:$?
```
