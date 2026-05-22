# Destructive Bash Guard for Claude Code

A dependency-free `PreToolUse` hook that prevents Claude Code from running high-risk Bash commands before they reach the shell.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended as JSONL to:

```text
~/.claude/hooks/blocked.log
```

Each log entry contains the UTC timestamp, attempted command, project path, and matched rule.

## Install in 2 commands

Run from this repository root:

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-bash-guard/destructive_bash_guard.py ~/.claude/hooks/destructive_bash_guard.py && chmod +x ~/.claude/hooks/destructive_bash_guard.py
python3 hooks/destructive-bash-guard/install_settings.py
```

The second command safely merges this hook into `~/.claude/settings.json` under `hooks.PreToolUse` with matcher `Bash`.

## Manual settings snippet

If you prefer to edit settings yourself, add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

Normal commands pass without output:

```bash
ls -la
python3 -m pytest
```

Dangerous commands are blocked with exit code `2` and a clear explanation for Claude:

```text
Blocked destructive Bash command before execution.
Pattern: rm -rf
Why: recursive forced removal can delete project or system files.
Project: /path/to/project
Log: /home/user/.claude/hooks/blocked.log
If this action is truly required, ask the user for an explicit, scoped confirmation and use a safer command.
```

## Test locally

```bash
python3 tests/test_destructive_bash_guard.py
```
