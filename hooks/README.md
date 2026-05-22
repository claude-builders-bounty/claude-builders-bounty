# Destructive Bash Command Guard

This is a Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

It blocks:

- `rm -rf` and close variants such as `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `--force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

## Install

```bash
mkdir -p .claude/hooks && cp hooks/block_destructive_bash.py .claude/hooks/block_destructive_bash.py && chmod +x .claude/hooks/block_destructive_bash.py
```

```bash
python3 - <<'PY'
import json, pathlib
settings = pathlib.Path(".claude/settings.json")
settings.parent.mkdir(parents=True, exist_ok=True)
config = json.loads(settings.read_text() if settings.exists() else "{}")
config.setdefault("hooks", {})["PreToolUse"] = [{
  "matcher": "Bash",
  "hooks": [{"type": "command", "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block_destructive_bash.py"}]
}]
settings.write_text(json.dumps(config, indent=2) + "\n")
PY
```

This writes the hook configuration below to `.claude/settings.json`:

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"${CLAUDE_PROJECT_DIR}/.claude/hooks/block_destructive_bash.py"}]}]}}
```

The hook exits with code `2` when it blocks a command, which prevents the Bash tool call and sends the reason back to Claude.

## Log Format

Each blocked attempt is appended as one JSON line:

```json
{"timestamp":"2026-05-22T00:00:00+00:00","attempted_command":"rm -rf build","project_path":"/path/to/project","reason":"rm -rf style recursive forced deletion is blocked"}
```

## Test Locally

```bash
python3 hooks/test_block_destructive_bash.py
```
