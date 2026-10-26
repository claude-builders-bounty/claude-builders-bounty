# block-destructive.sh — PreToolUse hook that blocks destructive Bash commands

A dependency-free **bash** hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks).
It runs as a `PreToolUse` hook on the `Bash` tool: before every Bash command
executes, the hook inspects the command and **blocks destructive commands
before they run**, explaining to Claude why.

Pure bash + coreutils — no `jq`, no Python, no network.

## What it blocks

| Pattern | Examples |
| --- | --- |
| `rm` with both recursive + force flags | `rm -rf /`, `rm -fr ./build`, `rm -r -f /tmp/data`, `rm --recursive --force /var` |
| `DROP TABLE` (case-insensitive) | `DROP TABLE users`, `drop table if exists users` |
| `git push` force-push | `git push --force`, `git push -f origin main`, `git push --force-with-lease` |
| `TRUNCATE` (case-insensitive) | `TRUNCATE TABLE sessions`, `truncate users` |
| `DELETE FROM` **without** a `WHERE` clause | `DELETE FROM users`, `DELETE FROM orders LIMIT 5` |

`DELETE FROM ... WHERE ...` is **allowed** (e.g. `DELETE FROM users WHERE id=1`).

Quoted strings are stripped before matching, so mentions such as
`echo "TRUNCATE is a word"` or `echo "DROP TABLE users"` do **not** trigger the hook.

## What it does when it blocks

- Prints a JSON decision to stdout (the documented `PreToolUse`
  `hookSpecificOutput`/`permissionDecision: "deny"` form, plus a top-level
  `decision: "block"` for older clients) **and** exits with code 2, which
  blocks the tool call per the Claude Code hooks contract.
- Prints a clear reason to stderr, which Claude sees.
- Appends one line to `~/.claude/hooks/blocked.log` (directory created if
  missing): `<ISO timestamp> | command=<attempted command> | cwd=<project path>`.

Normal commands pass silently (exit 0, no output) — the hook does not
interfere with ordinary Bash usage.

## Installation (2 commands)

**1. Install the hook script** (one command):

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hook/block-destructive.sh -o ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
```

**2. Register it in `~/.claude/settings.json`:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

Restart Claude Code (or start a new session) and the hook is live.

## Self-test

```bash
bash test.sh
```

`test.sh` pipes sample PreToolUse JSON payloads through the hook via stdin,
asserts the expected block/allow verdict for each case, checks that
`blocked.log` received exactly one line per blocked attempt, and prints
PASS/FAIL per case. It uses a throwaway `HOME`, so it never touches your real
`~/.claude`.

## Notes & limitations

- `rm -r` (recursive **without** force) is allowed, per the spec (only the
  recursive+force combination is blocked).
- Matching happens on the raw command text; SQL passed *inside* a quoted
  argument (e.g. `mysql -e "DROP TABLE users"`) is not inspected, which is
  the same trade-off that keeps `echo "TRUNCATE is a word"` from triggering.
- The hook is best-effort text matching, not a full shell parser; it covers
  the documented patterns and common variants (chained commands, flag
  combinations, case differences) without false-positive crashes.
