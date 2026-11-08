# Destructive-Command Guard — Claude Code PreToolUse Hook

A Claude Code `PreToolUse` hook that intercepts dangerous Bash commands
before they run, blocks them with a clear explanation to Claude, and logs
every blocked attempt.

Built for claude-builders-bounty issue #3 ($100, Opire).

## What it blocks

| Pattern | Example |
|---|---|
| Recursive force delete | `rm -rf /`, `rm -fr build`, `rm -r -f x` |
| SQL table drop | `DROP TABLE users` |
| Force push | `git push --force`, `git push -f` |
| SQL truncate | `TRUNCATE TABLE events` |
| Unbounded delete | `DELETE FROM users` (no `WHERE`) |

What it deliberately allows: `rm file.txt`, `rm -r dir` (no force),
`git push --force-with-lease` (the safer variant), and
`DELETE FROM ... WHERE ...`.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
cp hooks/pre-tool-use/block_destructive_bash.py ~/.claude/hooks/pre-tool-use/
```

Then register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Behavior

- Blocked calls return `permissionDecision: "deny"` with a reason that
  tells Claude exactly which pattern matched and that the attempt was logged.
- Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as:
  `timestamp \t project=<cwd> \t reason=<pattern> \t command=<attempted command>`
- Anything else passes through untouched (exit 0, no output). Unparseable
  input and non-Bash tools are never interfered with.

## Tests

```bash
python3 tests/test_block_destructive_bash.py   # 8 tests, stdlib only
```

Covers every blocked pattern plus the allowed near-misses above.
