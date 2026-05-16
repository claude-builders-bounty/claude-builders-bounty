# Destructive Command PreToolUse Hook

Blocks destructive Claude Code Bash calls before execution and logs each blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, project path, and reason.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command/pre-tool-use-destroy ~/.claude/hooks/pre-tool-use-destroy && chmod +x ~/.claude/hooks/pre-tool-use-destroy
python3 - <<'EOF'
import json, pathlib
p = pathlib.Path.home() / ".claude" / "settings.json"
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault("hooks", {}).setdefault("PreToolUse", []).append({"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/pre-tool-use-destroy"}]})
p.write_text(json.dumps(data, indent=2) + "\n")
EOF
```

## Blocks

- `rm -rf` style recursive forced deletes
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include `WHERE`

Safe commands, including `DELETE FROM ... WHERE ...`, are allowed.
