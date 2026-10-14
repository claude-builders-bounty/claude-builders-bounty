# block-destructive-bash

A Claude Code PreToolUse hook that intercepts dangerous bash commands **before**
they execute, blocks them, explains why to Claude, and logs every attempt.

## Install (1 command)

```bash
bash install.sh
```

This copies the hook to `~/.claude/hooks/` and registers it in
`~/.claude/settings.json` (idempotent — safe to re-run). Restart Claude Code
after installing.

## What it blocks

| Pattern | Examples blocked |
|---|---|
| Recursive force delete | `rm -rf /`, `sudo rm -rf ./build`, `rm -fr node_modules`, `rm -r -f dist`, `rm --recursive --force cache` |
| Force push | `git push --force origin main`, `git push -f` (`--force-with-lease` passes — it is the safe alternative) |
| SQL destruction | `DROP TABLE users`, `TRUNCATE TABLE sessions` |
| Unqualified DELETE | `DELETE FROM users` with no `WHERE` clause |
| History rewrite | `git reset --hard HEAD~5` |

Everything else passes through untouched (`ls`, `git push`, `git commit`,
`rm single-file`, `DELETE ... WHERE id = 1`, and all non-Bash tools).

## How it works

Claude Code calls PreToolUse hooks with a JSON payload on stdin
(`{"tool_name": "Bash", "tool_input": {"command": "..."}}`). The hook:

1. Parses the payload (jq when available, python3 fallback — no hard dependency)
2. Pattern-matches the command against the destructive classes above
3. On a match, appends a JSON line to `~/.claude/hooks/blocked.log` with the
   timestamp, attempted command, and project path, prints an explanation to
   stderr (Claude sees it), and exits 2 — which blocks the tool call

## Files

- `block-destructive-bash.sh` — the hook (bash, no dependencies beyond git/coreutils; python3 only as JSON fallback)
- `install.sh` — one-command installer
- `test-hook.sh` — test harness (22 assertions: 11 must-block, 10 must-allow, 1 non-Bash passthrough, plus log-schema validation)
- `SKILL.md` — Claude Code skill wrapper

## Tested

`bash test-hook.sh` → **22 passed, 0 failed** (bash + python3 fallback paths
both verified; see `examples/PROVENANCE.md`).
