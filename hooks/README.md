# Destructive Command Guard Hook for Claude Code

A robust `pre-tool-use` security hook that intercepts dangerous bash commands before they are executed by Claude Code.

## Features

- **Blocks Dangerous Commands**: Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- **Detailed Logging**: Logs all blocked attempts with a timestamp, attempted command, and project path to `~/.claude/hooks/blocked.log`.
- **Clear Explanation**: Displays a clear message to the model explaining which command was blocked and the specific security violation.
- **Smart Filtering**: Does not block read-only or safe display commands (e.g. `git diff`, `git log`, `echo`, `cat`, `grep`) containing these keywords, preventing false positives.

## Installation (2 commands)

To install the hook and register it globally in Claude Code:

### Step 1: Copy the hook script
```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive_command_hook.py ~/.claude/hooks/destructive_command_hook.py && chmod +x ~/.claude/hooks/destructive_command_hook.py
```

### Step 2: Register the hook in settings.json
```bash
python3 -c "import json, os; p=os.path.expanduser('~/.claude/settings.json'); os.makedirs(os.path.dirname(p), exist_ok=True); d=json.load(open(p)) if os.path.exists(p) else {}; d.setdefault('hooks', {}).setdefault('PreToolUse', []).append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': 'python3', 'args': [os.path.expanduser('~/.claude/hooks/destructive_command_hook.py')], 'timeout': 10}]}); json.dump(d, open(p, 'w'), indent=2)"
```

## How it works

When Claude attempts to call the `Bash` tool, this hook is invoked first. It checks the command against safety rules:
1. If the command violates a rule, it exits with code `2` (blocking the tool) and prints the explanation to stderr.
2. If the command is safe, it exits with `0` (allowing execution to proceed).
