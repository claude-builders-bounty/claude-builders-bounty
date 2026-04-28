# block-destructive-bash hook

A Claude Code `PreToolUse` hook (Python 3) that blocks dangerous bash commands before execution, logs every blocked attempt, and explains the block back to the model so it can adapt.

Submitted for [claude-builders-bounty issue #3](../../issues/3).

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/block-destructive-bash/install.sh
```

`install.sh` copies the hook into `~/.claude/hooks/`, marks it executable, and idempotently registers it under `hooks.PreToolUse[]` in `~/.claude/settings.json` with `matcher: "Bash"`. Restart Claude Code (or start a new session) for it to take effect.

## What it blocks

| Pattern | Why blocked |
|---|---|
| `rm -rf` (any flag order, including `-fr`, `--recursive --force`) | Recursive force-delete is the easiest way to wipe the wrong tree from a typo or unset variable |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Almost always wrong outside a migration file |
| `git push --force` (and `git push -f`) | Overwrites remote history. The safe variant `--force-with-lease` is **explicitly allowed**. |
| `TRUNCATE` / `TRUNCATE TABLE` | Non-recoverable wipe with no row-level audit trail |
| `DELETE FROM <table>` with **no `WHERE` clause** | Removes every row in the table |

## What it explicitly allows

- `git push --force-with-lease` (the safe force-push variant)
- `rm` without `-rf` (single files, `rm -r build/`, `rm -i`, etc.)
- `DELETE FROM ... WHERE ...` of any shape
- Any non-Bash tool call (the hook short-circuits to `approve` for anything that is not Bash)
- Malformed event JSON (defensive: approve so the hook never breaks the session)

## Logging

Every block is appended as one JSON line to `~/.claude/hooks/blocked.log`:

```json
{"ts": "2026-04-27T20:57:18-04:00", "command": "psql -c 'DROP TABLE users'", "project_path": "/home/me/proj", "rule": "DROP TABLE/DATABASE/SCHEMA"}
```

`tail -f ~/.claude/hooks/blocked.log` to watch in real time.

## Block message back to Claude

When a command is blocked, the hook returns `{"decision": "block", "reason": "..."}`. Claude Code surfaces the reason text back to the model. Example:

```
Blocked by destructive-bash hook (rule: rm -rf).

Why: Recursive force-delete. Easy to widen with a typo or unset variable
and wipe the wrong tree. Use `trash`/move-to-recycle, or be explicit
about each path with `rm -i`, or run targeted `find ... -delete`.

This attempt was logged to /home/me/.claude/hooks/blocked.log.
If you genuinely need to run this, do it manually in a terminal,
or remove the rule from the hook for this session.
```

This means Claude *understands the block and adapts on its next turn*, instead of just hitting a wall.

## Tests

```bash
python3 test_block_destructive_bash.py
```

25 cases covering every blocked pattern, every safe variant explicitly allowed, and the defensive edges (non-Bash tool short-circuits, empty command, malformed JSON). All pass.

## Known false positive (documented, not a bug)

The hook is **text-based** (regex on the command string), not a shell-AST parser. So this:

```bash
echo 'do not run rm -rf'
```

is blocked, even though it is harmless. This is a deliberate trade-off: a pure regex is simple to audit and impossible to bypass with quoting tricks; a real bash parser would be ~1000 lines and still vulnerable to `eval $VAR`. The chosen rules ban *the substrings*, full stop.

If you hit a genuine false positive, either:
1. Reword the command (`echo 'do not run "rm" "-rf"'`)
2. Run it directly in your own terminal (the hook only governs Claude's tool calls)
3. Edit the regex in `block_destructive_bash.py` for your repo's needs

## Files

- `block_destructive_bash.py` — the hook itself, single Python 3 file, no third-party deps
- `install.sh` — installs the hook + wires it into `~/.claude/settings.json` (idempotent)
- `test_block_destructive_bash.py` — self-contained test runner with 25 cases

## License

MIT — same as the parent repo.

## Resources

- [Claude Code hooks docs](https://docs.anthropic.com/claude-code/hooks)
