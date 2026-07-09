# Destructive Command Guard Hook

Claude Code `PreToolUse` hook for Bash commands. It blocks destructive commands before execution, logs each blocked attempt, and stays silent for normal commands.

## Install

```bash
python3 hooks/install.py
```

Then add `hooks/settings.example.json` to your Claude Code settings, or use the snippet printed by the installer.

Shell installer alternative:

```bash
./hooks/install.sh
```

## What It Blocks

The hook exits with code `2` and writes a clear message to stderr for:

- `rm -rf` / `rm -fr` style forced recursive deletion
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended as JSONL to:

```text
~/.claude/hooks/blocked.log
```

Each log row includes:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Examples

Blocked:

```bash
rm -rf build
git push --force origin main
psql -c 'DROP TABLE users'
psql -c 'DELETE FROM users'
mysql -e 'TRUNCATE sessions'
```

Allowed:

```bash
rm build.log
git push origin main
psql -c 'DELETE FROM users WHERE id = 1'
python3 -m pytest
npm test
```

## Validate

```bash
python3 hooks/test_destructive_command_guard.py
```

Expected output:

```text
destructive-command-guard: all tests passed
```

## Claude Code Hook Settings

The same JSON lives in `hooks/settings.example.json`.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive-command-guard.py"
          }
        ]
      }
    ]
  }
}
```
