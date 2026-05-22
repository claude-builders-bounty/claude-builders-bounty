# Pre-Tool-Use Safety Hook

Blocks destructive bash commands before Claude Code runs them. Pure bash, no Python.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hook.sh ~/.claude/hooks/pre-tool-use-safety.sh && chmod +x ~/.claude/hooks/pre-tool-use-safety.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/pre-tool-use-safety.sh" }] }
    ]
  }
}
```

## What It Blocks

| Category | Patterns |
|----------|----------|
| **Filesystem** | `rm -rf`, `rm -fr`, `rm --recursive --force` (flag-order tolerant) |
| **SQL** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `DELETE FROM` without `WHERE` |
| **Git** | `git push --force`, `git push -f` (incl. `--force-with-lease` checked) |
| **Disk** | `mkfs.*`, `dd of=/dev/sd*`, `> /dev/sd*` |
| **Permissions** | `chmod -R 777 /`, `chown -R user /` |

All matching is **case-insensitive**. Standard commands (`ls`, `npm install`, `DELETE FROM users WHERE id=1`) pass through silently.

## Log Format

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-05-22T10:00:00Z] BLOCKED | pattern="Recursive force delete (rm -rf)" | project="/path/to/repo" | command="rm -rf /"
```

See `examples/blocked-log-sample.log` for a full sample.

## Test It

```bash
bash tests/test-hook.sh
```

Runs 17 test cases (10 dangerous, 7 safe). All pass.

```
=== Dangerous commands (should be BLOCKED) ===
  PASS [blocked]   rm -rf
  PASS [blocked]   rm -fr (flag order)
  PASS [blocked]   DROP TABLE
  PASS [blocked]   drop table (lowercase)
  PASS [blocked]   TRUNCATE
  PASS [blocked]   DELETE FROM without WHERE
  PASS [blocked]   git push --force
  PASS [blocked]   git push -f
  PASS [blocked]   mkfs
  PASS [blocked]   chmod -R 777 /

=== Safe commands (should be ALLOWED) ===
  PASS [allowed]   ls
  PASS [allowed]   npm install
  PASS [allowed]   git push (no --force)
  PASS [allowed]   DELETE FROM with WHERE
  PASS [allowed]   rm specific file
  PASS [allowed]   find with -delete
  PASS [allowed]   node version check

Passed: 17 / Failed: 0
```

## Dependencies

`bash 4+` and `grep` only. **No `jq`, no Python, no npm.** Works out-of-the-box on every macOS and Linux system.
