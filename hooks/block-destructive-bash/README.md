# block-destructive-bash

PreToolUse hook for Claude Code that intercepts and blocks destructive Bash commands before execution.

## Features
- **Accidental Deletion Prevention**: Blocks `rm -rf` / `rm -fr` / recursive force flags.
- **Database Safety**: Blocks destructive SQL statements (`DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, and unbounded `DELETE FROM` without a `WHERE` clause).
- **Git Protection**: Blocks unsafe force push (`git push --force`, `git push -f`), while permitting safe `--force-with-lease`.
- **System Guard**: Blocks raw drive writes (`dd ... of=/dev/...`), disk formatting (`mkfs`), fork bombs, and recursive dangerous permissions (`chmod -R 777`).
- **Comprehensive Logging**: Appends all blocked actions to `~/.claude/hooks/blocked.log` with ISO timestamp, violation pattern, command, and project directory.
- **Fail-Open Architecture**: Malformed payloads or non-Bash tools pass through safely without interrupting the Claude Code session.

---

## Installation (2 commands)

### Command 1: Copy hook script to Claude hooks directory
```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

### Command 2: Register PreToolUse hook in Claude settings
```bash
python3 -c "import json, os; p = os.path.expanduser('~/.claude/settings.json'); os.makedirs(os.path.dirname(p), exist_ok=True); d = json.load(open(p)) if os.path.exists(p) else {}; d.setdefault('hooks', {})['PreToolUse'] = [{'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3 ' + os.path.expanduser('~/.claude/hooks/block_destructive.py')}]}]; json.dump(d, open(p, 'w'), indent=2); print('Successfully installed hook in ~/.claude/settings.json')"
```

*(Alternatively, merge the contents of `settings.example.json` into your `~/.claude/settings.json` manually).*

---

## Settings Configuration

Your `~/.claude/settings.json` hook block:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOME/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

---

## Blocked Patterns Reference

| Pattern | Example Matched Command | Status |
|---|---|---|
| `rm -rf` | `rm -rf /dir`, `rm -r -f .`, `rm -fr tmp` | Blocked (exit 2) |
| `DROP TABLE / DATABASE` | `mysql -e 'DROP TABLE users;'` | Blocked (exit 2) |
| `TRUNCATE` | `TRUNCATE TABLE logs;`, `TRUNCATE orders;` | Blocked (exit 2) |
| `DELETE FROM` without `WHERE` | `sqlite3 db.sqlite 'DELETE FROM sessions'` | Blocked (exit 2) |
| `git push --force` | `git push --force origin main`, `git push -f` | Blocked (exit 2) |
| `mkfs` / raw disk write | `mkfs.ext4 /dev/sdb1`, `dd of=/dev/sda` | Blocked (exit 2) |
| Fork bomb | `:(){ :|:& };:` | Blocked (exit 2) |
| Recursive 777 | `chmod -R 777 /var/www` | Blocked (exit 2) |

### Allowed Commands Example
- `git push --force-with-lease origin main` (Safe force push)
- `rm file.txt` / `rm -r src/` (Non-forced removal)
- `DELETE FROM users WHERE id = 12` (Bounded deletion)
- Standard development commands: `npm run build`, `python manage.py migrate`, `pytest`

---

## Log Output Format

Every intercepted attempt is logged to `~/.claude/hooks/blocked.log`:

```
<ISO-8601 Timestamp>\t<Pattern Reason>\t<Attempted Command>\t<Project Working Directory>
```

Example:
```
2026-11-05T14:40:00	rm -rf (recursive force deletion)	rm -rf /tmp/data	/home/user/myproject
```

---

## Running Tests

Run the test suite using Python's standard `unittest` (no external dependencies required):

```bash
python3 tests/test_hook.py
```
