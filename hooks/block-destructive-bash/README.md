# 🛡️ Block Destructive Bash Commands — Claude Code Hook

A pre-tool-use hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks) that intercepts and blocks dangerous shell commands before they execute.

## What it blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `mkfs`, `dd` to device, `chmod 777`, recursive `chown` |
| **SQL** | `DROP TABLE/DB`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git** | `git push --force/-f`, `git reset --hard`, `git clean -f`, `git branch -D` |
| **Shell abuse** | Fork bombs, `curl \| bash` |

## Install (2 commands)

```bash
cp -r .claude/hooks/block-destructive-bash.py ~/./.claude/hooks/
cat .claude/settings.json >> .claude/settings.json
```

Or manually:

1. Copy `block-destructive-bash.py` into your project's `.claude/hooks/` directory
2. Merge the hook entry from `settings.json` into your `.claude/settings.json`

## How it works

1. Claude Code invokes the hook before every tool call
2. The hook reads the tool name + input from stdin (JSON)
3. If it's a bash command matching a destructive pattern → **blocked** (exit 2)
4. The agent receives a clear explanation of *why* the command was blocked
5. Every block is logged to `~/.claude/hooks/blocked.log`

## Blocked log format

```
[2026-05-24T10:30:00Z] BLOCKED | project=/home/user/my-app | command=rm -rf /tmp/data
```

## Allowlist / Safe contexts

Commands inside `grep`, `echo`, `printf`, comments, or `sed` are **not** blocked — the hook recognises documentation/research contexts.

## Extending

Add patterns to the `DESTRUCTIVE_PATTERNS` list in the script. Each entry is a `(compiled_regex, human_label)` tuple.

## Requirements

- Python 3.10+ (uses `str | None` syntax; for 3.9, change to `Optional[str]`)
- Claude Code with hooks support

## License

MIT
