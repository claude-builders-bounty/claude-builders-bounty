# bash-guard — Claude Code PreToolUse hook that blocks destructive bash commands

Blocks dangerous shell/SQL commands **before** Claude Code runs them, logs every
blocked attempt, and tells Claude exactly why it was stopped.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/<you>/bash-guard/main/bash-guard.py -o ~/.claude/hooks/bash-guard.py && chmod +x ~/.claude/hooks/bash-guard.py
```

```bash
python3 - <<'PY'
import json, os, pathlib
p = pathlib.Path.home() / ".claude/settings.json"
cfg = json.loads(p.read_text()) if p.exists() else {}
hook = {"type": "command", "command": "python3 ~/.claude/hooks/bash-guard.py"}
hooks = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
if not any(h.get("matcher") == "Bash" for h in hooks):
    hooks.append({"matcher": "Bash", "hooks": [hook]})
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(cfg, indent=2))
print("installed ->", p)
PY
```

(If you prefer a local copy instead of curl, drop `bash-guard.py` into
`~/.claude/hooks/` yourself and run only the second command.)

## What it blocks

| Rule | Example it stops | Why |
|------|------------------|-----|
| `rm -rf` | `rm -rf node_modules`, `sudo rm -rf /` | recursive + forced deletion is irreversible |
| `DROP TABLE` | `psql -c "DROP TABLE users;"` | destroys data and schema |
| `TRUNCATE` | `TRUNCATE TABLE logs;` | removes all rows, no undo |
| `DELETE without WHERE` | `DELETE FROM users;` | deletes every row |
| `git push --force` | `git push -f`, `git push --force-with-lease` | rewrites shared remote history |

Safe look-alikes are **not** blocked: `rm -f file`, `rm -r dir`, `rm file`,
`git push origin main`, `git push --follow-tags`, `DELETE FROM t WHERE id=3;`.
Quoted *text* is ignored too — `echo 'rm -rf is dangerous'` passes, because the
string is mentioned, not executed.

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as one JSON
object per line:

```json
{"timestamp":"2026-09-27T13:53:00+00:00","command":"rm -rf /tmp/x","project_path":"/tmp/proj","rules":["rm -rf"]}
```

```bash
tail -f ~/.claude/hooks/blocked.log | jq .
```

## How it responds

The hook implements the official Claude Code [`PreToolUse` decision](https://code.claude.com/docs/en/hooks):
on a violation it writes

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}
```

to stdout and exits `2`, so Claude sees a clear explanation and the tool call is
denied. On a safe command it exits `0` with no output, leaving the normal
permission flow untouched.

## Test

```bash
python3 test_bash_guard.py
```

21 cases covering every rule plus the false-positive look-alikes — all pass.

## Limits (by design)

- It matches on command **text**, not a full shell AST, so a determined
  obfuscation (`r''m -rf`) can slip past. It is a guardrail against the common
  accidental destructive command, not a sandbox.
- Windows paths/PowerShell are out of scope for this Python version.

## License

MIT
