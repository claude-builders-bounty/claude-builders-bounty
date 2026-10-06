# block_bash — a PreToolUse hook that blocks destructive bash commands

A dependency-free Python hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks).
It sits in front of the `Bash` tool, reads the command Claude is about to run,
and denies the dangerous ones with a reason Claude can act on — while leaving
everyday commands completely alone.

Blocked by default:

| Pattern | Why |
|---|---|
| `rm -rf` (and `rm -fr`, `--force`, `--recursive`) | Recursive force delete, e.g. `rm -rf /` or `rm -rf $HOME` |
| `DROP TABLE` (incl. `DROP TEMPORARY TABLE`) | Destroys a schema and everything in it |
| `git push --force` / `-f` / `+refspec` | Rewrites published history; `main` is not recoverable locally |
| `TRUNCATE` | Empties a table |
| `DELETE FROM` without `WHERE` | Removes every row |

## Install

```bash
git clone <this-repo> && bash claude-hooks-guard/install.sh
```

That is the whole install. It copies `block_bash.py` to `~/.claude/hooks/` and
registers it under `PreToolUse` with the `Bash` matcher in `~/.claude/settings.json`.
Existing settings are preserved, and re-running the script is safe.

Restart Claude Code after installing.

## What it looks like in action

```
Claude wants to run: rm -rf ~/.cache/app

BLOCKED by block_bash.py: recursive force delete of files (rm -rf / variants).
This command is destructive and was not executed. Rewrite it as a narrower
command (target a specific path, add a WHERE clause, or use
--force-with-lease), or ask the user to run it manually if they truly mean it.
```

Every block is appended to `~/.claude/hooks/blocked.log`:

```
[2026-10-07T01:12:44+03:00] blocked=rm-rf project=/home/me/api command='rm -rf ~/api'
```

## Design notes

- **Segment-aware.** The command is split on `&&`, `||`, `;`, `|`, `&` and newlines,
  then each segment is checked, so `echo hi && rm -rf /` is still caught.
- **Quoting-aware.** Quotes, `${VAR}` and `$(...)` are normalised away first, so
  `bash -c 'rm -rf /'` and `rm -rf "$HOME"` cannot slip through.
- **No false positives on display commands.** `echo 'run rm -rf build'` and
  `grep -rn 'DROP TABLE' ./docs` are text, not attacks, and pass straight through.
- **`DELETE FROM ... WHERE ...` is allowed** — the risk is the missing `WHERE`, not the verb.
- **Never breaks the tool.** A malformed payload, an unreadable stdin, or a log
  file that cannot be written all fall through to "allow", so the hook degrades
  instead of bricking the session.

## Tests

```bash
python3 test_block_bash.py
```

Covers every block rule, the quoting bypasses, `DELETE ... WHERE`, a set of
ordinary commands that must never be blocked, and the log line format.
