# Claude Code destructive Bash blocker

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

It denies:

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

Safe Bash commands continue through Claude Code's normal permission flow without hook output.

## Install

From the repository root:

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/'.claude/settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(p.read_text()) if p.exists() else {}
data.setdefault('hooks', {}).setdefault('PreToolUse', []).append({'matcher':'Bash','hooks':[{'type':'command','command':str(pathlib.Path.home()/'.claude/hooks/block-destructive-bash.py')}]})
p.write_text(json.dumps(data, indent=2) + '\n')
PY
```

That is two shell commands: one copies the hook, one registers it in Claude Code settings.

## Project-local configuration

This PR also includes `.claude/settings.json` for project-local usage:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive-bash.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 tests/test_block_destructive_bash.py
```

Expected output:

```text
PASS: blocked 7 dangerous commands and allowed 7 safe commands
```
