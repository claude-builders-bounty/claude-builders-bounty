# PreToolUse Guard — Destructive Command Blocker

A Claude Code `PreToolUse` hook that intercepts and blocks dangerous bash commands before execution.

**Fail-closed design**: if `jq` is missing, stdin is empty, or JSON is malformed, the hook *denies* execution rather than silently allowing it through. Most competing implementations fail-open (parsing error = allow), which defeats the purpose of a safety guard.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -fr` | `rm -rf /`, `rm -r -f .`, `sudo rm -rf /` |
| `rm --recursive --force` | `rm --recursive --force /data` |
| `git push --force` | `git push --force origin main`, `git push -f` |
| `git reset --hard` | `git reset --hard HEAD~3` |
| `git clean -fd` | `git clean -fd`, `git clean -fdx` |
| `DROP TABLE` | `psql -c "DROP TABLE users;"` |
| `TRUNCATE` | `mysql -e "TRUNCATE TABLE orders"` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

**Explicitly allowed** (not blocked):
- `git push --force-with-lease` (safe alternative)
- `git push --force-if-includes` (safe alternative)
- `rm file.txt` (no recursive+force combo)
- `DELETE FROM users WHERE id=1` (has WHERE clause)

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
./claude-builders-bounty/tools/pre-tool-use-guard/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`.

## How It Works

1. Claude Code invokes the hook before every `Bash` tool call
2. The hook reads the command from stdin JSON
3. If a destructive pattern matches, it returns a `deny` decision with an explanation
4. Every blocked attempt is logged to `~/.claude/hooks/blocked.log`

Log format (TSV):
```
2026-06-01T12:00:00Z    rm -rf /    /home/user/project    Destructive file removal (rm -rf)
```

## Safety Design

- **Fail-closed**: jq missing, empty stdin, malformed JSON → deny (not allow)
- **Atomic install**: settings.json updated via `mktemp` + `mv` to prevent corruption
- **No false positives on safe alternatives**: `--force-with-lease` and `--force-if-includes` are explicitly excluded
- **Handles flag variations**: `-rf`, `-fr`, `-r -f`, `--recursive --force`, mixed, with `sudo`/`xargs`/`env` prefixes

## Uninstall

```bash
rm ~/.claude/hooks/block-destructive.sh
```

Then remove the corresponding entry from `~/.claude/settings.json` under `hooks.PreToolUse`.

## Limitations

The hook inspects the literal command string. It cannot catch:
- Base64-encoded or `eval`-wrapped commands
- Variable indirection (`CMD="rm"; $CMD -rf /`)
- Equivalent destructive operations via other tools (e.g., `find / -delete`)

SQL patterns (`DROP TABLE`, `TRUNCATE`, `DELETE FROM`) are matched anywhere in the command text, including in contexts like `grep "DROP TABLE" file.sql`. This is an intentional conservative trade-off.

## Requirements

- `bash` (3.2+)
- `jq`
