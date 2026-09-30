# Pre-Tool-Use Hook: Block Destructive Bash Commands 🛡️

A security pre-tool-use hook for **Claude Code** that intercepts and blocks dangerous, irreversible bash operations before execution.

---

## Features

- **Automated Protection**: Intercepts `Bash` / terminal execution requests before they run.
- **Pattern Blocking**:
  - `rm -rf` (and flag variations like `-fr`, `-r -f`)
  - `DROP TABLE`
  - `git push --force` (including `--force-with-lease` and `-f`)
  - `TRUNCATE`
  - `DELETE FROM` statements missing a `WHERE` clause
- **Audit Logging**: Logs every blocked execution attempt to `~/.claude/hooks/blocked.log` with timestamp, project directory, and command details.
- **Informative Feedback**: Returns a clean explanation to Claude explaining why the action was prevented.

---

## Quick Installation (2 Commands)

Run these two commands in your terminal to install the hook:

```bash
mkdir -p ~/.claude/hooks
cp hooks/block_destructive_commands.py ~/.claude/hooks/block_destructive_commands.py && chmod +x ~/.claude/hooks/block_destructive_commands.py
```

---

## Configuration

Add the hook entry to your `~/.claude/settings.json` (or `~/.claude/config.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "command": "~/.claude/hooks/block_destructive_commands.py"
      }
    ]
  }
}
```

---

## Testing

Run the unit test suite to verify pattern matching and logging logic:

```bash
PYTHONPATH=. pytest tests/test_block_destructive_commands.py
```
