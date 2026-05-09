# Block Destructive Bash

Pre-tool-use hook for [Claude Code](https://docs.anthropic.com/claude-code/hooks)
that intercepts and denies destructive `Bash` commands before they execute.
Blocked attempts are appended to `~/.claude/hooks/blocked.log` with the
timestamp, command, project path, and reason. Closes [#3](../../issues/3).

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/hook.py -o ~/.claude/hooks/block_destructive_bash.py
python ~/.claude/hooks/block_destructive_bash.py --install
```

The first command downloads the hook into `~/.claude/hooks/`. The second
self-registers the hook by merging a `PreToolUse` entry into
`~/.claude/settings.json` (existing entries are preserved). Re-running
`--install` is idempotent — the settings entry is only added once.

## What it blocks

| Pattern | Reason | Notes |
|---|---|---|
| `rm -rf` / `-fr` / `-Rf` / `-rfv` / `--recursive --force` | Recursive force delete | Detected via shlex tokenization, so `echo "rm -rf"` is **not** blocked |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` / `DROP INDEX` / `DROP VIEW` | Irreversible SQL DDL | Quoted bodies of `psql -c '…'` / `mysql -e "…"` **are** scanned |
| `TRUNCATE [TABLE] x` | Bulk irreversible deletion | |
| `DELETE FROM x` (without `WHERE`) | Deletes every row | `DELETE FROM x WHERE id=1` is allowed |
| `git push --force` / `-f` | Force-push rewrites history | `--force-with-lease` is **explicitly allowed** |
| `dd … of=/dev/sd*` / `nvme*` / `hd*` | Raw block-device write | |
| `mkfs.* /dev/…` | Filesystem format | |
| `> /dev/sd*` redirects | Raw block-device redirect | |
| `chmod -R 000` | Locks tree out of itself | |
| `:(){ :\|: & };:` | Fork bomb | |

False positives are tested aggressively (see `tests/test_hook.py`):

- `grep 'DROP TABLE' file.sql` — allowed (no SQL CLI present)
- `# rm -rf is dangerous` — allowed (line comment)
- `echo "rm -rf"` — allowed (quoted, no real `rm` invocation)
- `git push --force-with-lease` — allowed
- `DELETE FROM users WHERE id = 1` — allowed

## How a block looks to Claude

When a destructive command fires, the hook emits the modern Claude Code
hook protocol:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive command: rm with -r/-R and -f flags (recursive force delete). Logged to /home/you/.claude/hooks/blocked.log. Override by editing /home/you/.claude/settings.json or removing the hook."
  }
}
```

Claude receives the reason and can suggest a safer alternative. The audit log
entry is one JSON line per blocked attempt:

```json
{"timestamp":"2026-05-08T23:31:14.221+00:00","command":"rm -rf /tmp/foo","reason":"rm with -r/-R and -f flags (recursive force delete)","project":"/home/you/code/myapp"}
```

## Failure modes

- **Malformed hook input** — fails open (allows the command). Better to let a
  command through than to break Claude Code on a hook bug.
- **Settings file already has unrelated PreToolUse entries** — they're preserved;
  only this hook's entry is added.
- **Settings file is invalid JSON** — installer aborts with a clear error and
  does not overwrite. Fix the JSON, re-run `--install`.

## Tests

Stdlib only — no pytest required.

```bash
python hooks/block-destructive-bash/tests/test_hook.py -v
```

11 tests cover 33 destructive commands and 23 benign ones, plus the hook's
JSON I/O contract (block, allow, ignore non-Bash tools, ignore PostToolUse,
fail open on malformed input).

## Uninstall

Remove the hook entry from `~/.claude/settings.json` (under
`hooks.PreToolUse`) and optionally delete `~/.claude/hooks/block_destructive_bash.py`.
