# claude-destructive-guard

A Claude Code **`PreToolUse` hook** that intercepts dangerous bash commands
*before* they run, blocks them, and logs the attempt. It keeps Claude (or a
fat-fingered you) from running an irreversible command by accident.

## What it blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` | `rm -rf ./build`, `rm -fr`, `rm -r -f`, `sudo rm -Rf …` | recursive **and** force delete — wipes trees irreversibly |
| `git push --force` | `git push --force`, `git push -f` | overwrites shared remote history (`--force-with-lease` is **allowed**) |
| `DROP TABLE` / `DROP DATABASE` | `psql -c 'DROP TABLE users'` | destroys a table/database |
| `TRUNCATE` | `TRUNCATE logs` | empties a table, no undo |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions` | deletes every row (a `WHERE` clause is **allowed**) |

Normal commands pass straight through — `rm file.txt`, `rm -r dir` (no force),
`git push`, `DELETE … WHERE id=5`, `SELECT …`, etc. See `test_hook.py` for the
full allow/block matrix (22 cases).

## Install (2 commands)

```bash
git clone https://github.com/<you>/claude-destructive-guard.git
bash claude-destructive-guard/install.sh
```

The installer copies `block-destructive.py` to `~/.claude/hooks/` and registers
a `PreToolUse` hook for the `Bash` tool in `~/.claude/settings.json`
(idempotent — safe to re-run). **Restart Claude Code** (or start a new session)
to load it.

<details>
<summary>Manual install (if you'd rather not run the script)</summary>

1. `cp block-destructive.py ~/.claude/hooks/`
2. Merge `settings.snippet.json` into `~/.claude/settings.json` (under `hooks`).
</details>

## What you see when it fires

The command never executes. Claude receives a clear explanation:

```
🛑 Blocked by destructive-command guard: recursive force delete (`rm -rf`) —
can wipe entire directory trees irreversibly.
Matched rule: rm -rf. Logged to ~/.claude/hooks/blocked.log.
If this is genuinely intended, run it yourself in a terminal, or narrow the
command (add a WHERE clause, use --force-with-lease, delete specific paths…).
```

Every block is appended to `~/.claude/hooks/blocked.log`, tab-separated:

```
2026-07-01T13:17:18+07:00	[rm -rf]	/Users/you/project	rm -rf ./build
└ timestamp (ISO 8601)   └ rule      └ project path       └ attempted command
```

## Test it

```bash
python3 test_hook.py
```

Runs the hook exactly the way Claude Code does (event JSON on stdin) and asserts
each command is blocked or allowed as expected. Tests write to a throwaway log
(`CLAUDE_HOOK_LOG` env override), never your real one.

## How it works

Claude Code sends every tool call to registered `PreToolUse` hooks as JSON on
stdin. This hook only inspects `Bash` calls, splits the command on shell
separators (`;` `&&` `|`), and tests each segment against the rules above. On a
match it prints a `permissionDecision: "deny"` object — the documented way for a
`PreToolUse` hook to veto a tool call — and logs the attempt.

**Fail-open by design:** any unexpected input or internal error exits cleanly
without blocking, so the hook can never wedge your session.

### Known trade-offs (intentional)

- **Heuristic, not a sandbox.** It pattern-matches command *text*; it won't catch
  a destructive command hidden inside a script you invoke (`./deploy.sh`) or
  obfuscated (`r""m -rf`). It's a guardrail against the common, obvious mistakes,
  not a security boundary.
- **Leading-command aware.** `grep -rf patterns src/` is allowed because the
  segment starts with `grep`, not `rm` — the `-rf` there is unrelated.
- Tune the rules by editing `RULES` / the detector functions in
  `block-destructive.py`.

## Requirements

Python 3.8+ (standard library only). No dependencies.

## License

MIT
