# Destructive Bash Command Blocker

This is a Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

It blocks:

- `rm -rf` variants, including `rm -fr` and `sudo rm -Rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Blocked attempts are written to `~/.claude/hooks/blocked.log` with a UTC timestamp, rule name, project path, and attempted command.

## Install

From this directory:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Add the hook to your Claude Code settings:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path.home() / ".claude" / "settings.json"
path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(path.read_text() if path.exists() else "{}")
settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
settings["hooks"]["PreToolUse"].append({
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(Path.home() / ".claude" / "hooks" / "block_destructive_bash.py"),
    }],
})
path.write_text(json.dumps(settings, indent=2) + "\n")
PY
```

## Behavior

Claude Code command hooks receive JSON on stdin. This hook reads `tool_input.command` for Bash calls only.

When a command is safe, it exits `0` and does not interfere. When a command matches a blocked pattern, it logs the attempt, prints a clear explanation to stderr, and exits `2`. Claude Code treats exit code `2` from a `PreToolUse` hook as a blocking result.

Example blocked message:

```text
Blocked destructive Bash command: Recursive forced removal is blocked. Rule: rm -rf. Rewrite the command into a safer, explicit operation.
```

## Run Tests

```bash
python3 -m unittest discover -s tests
```

## Sample Results

```text
$ python3 -m unittest discover -s tests
.....
----------------------------------------------------------------------
Ran 5 tests in 0.03s

OK
```
