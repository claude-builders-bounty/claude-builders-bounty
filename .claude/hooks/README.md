# Destructive Bash Guard — Claude Code PreToolUse Hook

A `PreToolUse` hook that intercepts irreversibly destructive shell commands
**before** Claude Code executes them, explains to Claude *why* the command was
blocked, and logs every blocked attempt.

## What it blocks

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` / `rm -fr` (any recursive + force) | `rm -rf /`, `sudo rm -rf ~` | No confirmation, no recovery |
| `rm -r` at dangerous locations | `rm -r /etc`, `rm -r ..` | System / home / repo-root destruction |
| `git push --force` / `-f` | `git push --force origin main` | Rewrites shared history (`--force-with-lease` still allowed) |
| `DROP TABLE` | `sqlite3 app.db 'DROP TABLE users'` | Irreversible schema + data loss |
| `TRUNCATE` | `psql -c "TRUNCATE sessions"` | Wipes a table |
| `DELETE FROM` without `WHERE` | `DELETE FROM users` | Deletes every row |
| `mkfs`, `dd … of=/dev/…` | `mkfs.ext4 /dev/sda1` | Formats / overwrites devices |
| Fork bombs | `:(){ :|:& };:` | Hangs the machine |
| Raw-disk redirection | `echo x > /dev/sda` | Corrupts the device |
| PowerShell equivalents | `Remove-Item -Recurse -Force C:\` | Same protection on Windows |

Smuggling attempts are covered too: chained commands (`&&`, `;`, `|`), `sudo`
prefixes, `VAR=val` prefixes, `sh -c "…"`, and `$(…)` / backtick substitution
are all unwrapped and inspected. SQL keywords inside non-SQL commands (e.g.
`echo "don't DROP TABLE"`, `grep -r "rm -rf" .`) pass through untouched.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block-destructive-bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Then register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python3 ~/.claude/hooks/block-destructive-bash.py" }
        ]
      }
    ]
  }
}
```

Use `"matcher": "Bash|PowerShell"` if you also use the PowerShell tool.
Requires Python 3.8+ — no third-party packages.

## How it works

1. Claude Code sends the `PreToolUse` JSON payload on stdin
   (`tool_name`, `tool_input.command`, `cwd`, …).
2. The hook normalises the command (strips `sudo`, env assignments, splits
   chained segments) and checks each segment against the block list.
3. **Blocked:** appends `timestamp | cwd | command` to
   `~/.claude/hooks/blocked.log`, prints a JSON
   `hookSpecificOutput.permissionDecision: "deny"` decision (understood by
   current Claude Code) **and** exits `2` with the reason on stderr
   (understood by older versions). The `permissionDecisionReason` is shown to
   Claude so it can explain and offer a safe alternative.
4. **Allowed:** exits `0` silently — zero latency impact on normal commands.

## Blocked-attempt log

`~/.claude/hooks/blocked.log` — one line per block:

```
2026-09-16T08:59:49+00:00 | cwd=/home/user/proj | command=git push --force origin main
```

## Testing

```bash
python3 .claude/hooks/tests/test_hook.py
```

42 cases: every blocked pattern (including smuggling variants), plus
false-positive guards (`git push --force-with-lease`, `DELETE … WHERE`,
`grep -r "rm -rf"`, coreutils `truncate`, non-shell tools, empty input).
Tests run the real hook as a subprocess against an isolated temp `HOME`, so
your real `~/.claude` is never touched. All 42 pass.

## Known limitations

- Commands constructed dynamically at runtime (e.g. a variable holding
  `rm -rf` expanded by the shell) are inspected as written, not as expanded.
- The hook sees the command string before shell expansion; exotic quoting
  tricks may evade static inspection. It is a safety net, not a sandbox —
  keep Claude Code's permission system enabled alongside it.
- A hook that crashes or receives malformed JSON fails open (allows the
  command) with a stderr warning, so a broken hook can never brick a session.
