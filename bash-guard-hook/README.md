# Bash Guard Hook

A Claude Code `PreToolUse` hook that blocks destructive Bash commands before
they run. Built for the [Claude Builders Bounty](https://github.com/claude-builders-bounty/claude-builders-bounty)
issue **#3** ($100).

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` (also `-fr`, `-r -f`, `--recursive --force`) | Recursive, forced delete — no undo |
| `DROP TABLE` | Permanently drops a table and all its data |
| `git push --force` / `git push -f` | Rewrites shared history |
| `TRUNCATE` (SQL) | Instantly empties a table |
| `DELETE FROM` without a `WHERE` clause | Deletes every row in the table |

When a command is blocked, Claude sees a message explaining which pattern
matched, why it is dangerous, and a safer alternative — and the attempt is
logged to `~/.claude/hooks/blocked.log` with a timestamp, the command, and
the project path.

## Installation (1 command)

```bash
bash install.sh
```

That copies the hook to `~/.claude/hooks/`, makes it executable, and
registers it in `~/.claude/settings.json` (creating the file if needed,
leaving your other settings alone). Running it twice does not duplicate
the registration.

Manual install (2 commands) if you prefer:

```bash
mkdir -p ~/.claude/hooks && cp block-destructive-bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Then merge the `hooks` object from `settings.json` into your
`~/.claude/settings.json` (see `settings.json` in this folder for the exact
snippet).

## How it works

Claude Code sends every Bash tool call to the hook as JSON on stdin. The
hook exits `0` to allow the command (silent) or `2` to block it, with the
reason printed to stderr — Claude sees that message and can choose a safer
command instead.

The hook is shell-aware, so it only judges commands the shell would
actually run:

- `rm -rf` inside a quoted string (`echo "rm -rf /"`) or a comment
  (`# rm -rf /`) is **allowed** — the shell would not run it.
- `DELETE FROM users WHERE id = 42` is **allowed**; only a WHERE-less
  `DELETE FROM` is blocked.
- `git push --force-with-lease` is **allowed** — it is the safe variant.
- `truncate -s 0 app.log` is **allowed** — that is the `truncate` file
  utility, not SQL.
- `rm -r /tmp/old` and `rm -f file.txt` are **allowed** — only the
  recursive *and* forced combination is blocked.

Design decisions worth knowing:

- **SQL is checked in its quoted form.** `psql -c "DROP TABLE users"` is
  the real-world destructive form, so the hook looks for SQL keywords
  inside quoted strings too. That means `echo "DROP TABLE users"` is also
  blocked — a deliberate trade-off in favour of catching real SQL payloads.
- **Only Bash tool calls are checked.** Other tools pass through untouched,
  and malformed hook input fails open (exit 0) so a hook bug never breaks
  your session.
- **This is a guardrail, not a sandbox.** A determined command can still
  get around it (for example, quoting the command name itself: `"rm" -rf /`,
  or executing SQL from a file with `psql -f schema.sql`). It stops the
  common accidents, which is what it is for.

## Configuration

- **Log file:** `~/.claude/hooks/blocked.log` by default. Override with the
  `BASH_GUARD_LOG` environment variable, e.g. in your settings command:
  `BASH_GUARD_LOG=/tmp/blocked.log python3 ~/.claude/hooks/block-destructive-bash.py`
- **Python:** stdlib only, no dependencies. Requires Python 3.8+.

## Testing

```bash
python3 test_hook.py
```

Runs 43 cases against the hook with a throwaway `HOME` (your real
`blocked.log` is never touched): blocked commands (exit 2, reason in the
message, one log line with timestamp + command + project path), allowed
commands (exit 0, silent, log untouched), plus non-Bash tools, malformed
JSON, and empty commands.

## Uninstall

```bash
rm ~/.claude/hooks/block-destructive-bash.py
```

Then remove the `PreToolUse` entry for this hook from
`~/.claude/settings.json`.
