# Block Destructive Commands — Claude Code PreToolUse Hook

A `pre-tool-use` hook for [Claude Code](https://docs.anthropic.com/claude-code) that intercepts and blocks dangerous bash commands before they execute.

## What it blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `chmod 777`, `chown -R`, `mkfs`, `dd` to device |
| **SQL** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE` without `WHERE` |
| **Git** | `push --force`, `push -f`, `reset --hard`, `clean -f`, `checkout -- .` |
| **System** | fork bombs, `kill -9 1`, `shutdown`, `reboot` |
| **Supply chain** | `curl \| bash`, `wget \| python` |

## What it does NOT block

Normal commands (`ls`, `npm install`, `git commit`, `python manage.py migrate`, etc.) pass through untouched.

### Allowlisted paths

Commands targeting these paths are allowed even if they match a dangerous pattern:

- `/tmp/`, `/var/tmp/`
- `~/.cache/`
- `node_modules/`, `.next/`, `dist/`, `build/`
- `__pycache__/`, `.pytest_cache/`, `coverage/`

This means `rm -rf node_modules/` works, but `rm -rf /` does not.

## Installation

```bash
curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/block-destructive-commands/hook.py | python3 - --install
```

That's it. One command. It will:

1. Copy the hook to `~/.claude/hooks/block_destructive.py`
2. Register it as a `PreToolUse` hook in `~/.claude/settings.json`

## Uninstall

```bash
~/.claude/hooks/block_destructive.py --uninstall
```

## Self-test

```bash
~/.claude/hooks/block_destructive.py --test
```

Runs 25 pattern-matching tests and reports pass/fail.

## How it works

When Claude Code invokes a bash tool, it sends the tool context as JSON to the hook's stdin. The hook:

1. Extracts the command string
2. Matches it against 22+ destructive patterns
3. Checks the allowlist for high-severity (non-critical) patterns
4. If blocked: logs to `~/.claude/hooks/blocked.log` and exits 1
5. If allowed: exits 0

Exit code 1 tells Claude Code to reject the tool invocation. Claude sees the error message and can explain to the user why the command was blocked.

## Log format

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-07-13T10:30:45.123456] severity=critical reason='rm -rf' path=/home/user/project command='rm -rf /'
```

Each entry includes: timestamp, severity level, matched pattern, working directory, and the full command.

## Configuration (optional)

Create `~/.claude/hooks/guard.config.json` to customize:

```json
{
  "safe_paths": [
    "my-build-dir/",
    "vendor/"
  ],
  "extra_blocked": [
    {
      "pattern": "\\bsudo\\b",
      "label": "sudo commands"
    }
  ]
}
```

- `safe_paths`: Additional paths to allowlist (appended to defaults)
- `extra_blocked`: Additional regex patterns to block

## Requirements

- Python 3.8+
- Claude Code

## Design decisions

**Why a blocklist instead of an allowlist?** An allowlist would be too restrictive and require constant maintenance. The set of dangerous commands is finite and well-known; the set of safe commands is infinite.

**Why allowlist paths?** `rm -rf node_modules/` is the most common "destructive" command in development and is always safe. Blocking it would make the hook too annoying to keep enabled.

**Why log to a file instead of stdout?** The hook's stdout/stderr goes to Claude Code's error handling. The log file persists for human review and isn't lost between sessions.

**Why `curl | python3 - --install`?** Single command, no git clone needed, works on any machine with Python 3.
