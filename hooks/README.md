# Block destructive bash commands (Claude Code hook)

`PreToolUse` hook that intercepts dangerous Bash tool calls before they run.

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` (and `-fr` / `-r -f`) | `rm -rf /tmp/build` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` / `-f` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE sessions;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

Safe commands (`ls`, `git status`, `rm file.txt`, `DELETE FROM t WHERE id=1`, etc.) are left alone.

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as:

```text
<UTC timestamp><TAB><command><TAB><project path>
```

Claude receives a clear deny reason via `permissionDecisionReason`.

## Install (2 commands)

From this repo root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-commands.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-commands.py
```

```bash
python3 -c "import json,pathlib; p=pathlib.Path.home()/'.claude'/'settings.json'; d=json.loads(p.read_text()) if p.exists() else {}; d.setdefault('hooks',{}).setdefault('PreToolUse',[]); cmd='python3 '+str(pathlib.Path.home()/'.claude'/'hooks'/'block-destructive-commands.py'); hooks=d['hooks']['PreToolUse']; entry={'matcher':'Bash','hooks':[{'type':'command','command':cmd}]}; hooks[:]=[h for h in hooks if not (isinstance(h,dict) and any((x.get('command')==cmd) for x in h.get('hooks') or []))]; hooks.append(entry); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(d, indent=2)+'\n')"
```

Restart Claude Code (or start a new session) so settings reload.

## Manual settings snippet

If you prefer to edit `~/.claude/settings.json` yourself, add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
          }
        ]
      }
    ]
  }
}
```

## Smoke test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp/project"}' \
  | python3 hooks/block-destructive-commands.py
```

Expect JSON with `"permissionDecision": "deny"`. Safe command:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/project"}' \
  | python3 hooks/block-destructive-commands.py
```

Expect empty output (allow / no decision).
