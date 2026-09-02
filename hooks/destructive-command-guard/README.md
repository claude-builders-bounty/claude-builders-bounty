# Destructive Command Guard for Claude Code

A zero-dependency `PreToolUse` hook that denies high-confidence destructive Bash commands before Claude Code executes them.

## What it blocks

| Pattern | Examples blocked |
|---|---|
| Recursive forced deletion | `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force` |
| Forced Git push | `git push --force`, `git push -f`, `--force-with-lease`, `+refspec` |
| Destructive SQL | `DROP TABLE`, `TRUNCATE` |
| Unbounded deletion | `DELETE FROM ...` without a `WHERE` clause |

Normal commands remain untouched, including `rm file.txt`, ordinary `git push`, and `DELETE FROM ... WHERE ...`.

Every denial is appended as one JSON object per line to:

```text
~/.claude/hooks/blocked.log
```

Each record includes UTC timestamp, attempted command, project path, and denial reason.

## Install — 1 command

From the repository root:

```bash
python3 hooks/destructive-command-guard/install.py
```

The installer copies the hook to `~/.claude/hooks/block_destructive.py` and merges a `PreToolUse` entry into `~/.claude/settings.json` without replacing unrelated settings.

## Hook behavior

For a blocked Bash command the guard returns a structured denial:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked forced git push."
  }
}
```

For allowed commands, non-Bash tools, or malformed hook input, it exits successfully without emitting a denial. A temporary logging failure never turns a dangerous match into an allow.

## Tests

Run:

```bash
python3 hooks/destructive-command-guard/test_block_destructive.py
```

The suite covers reordered `rm` flags, `sudo rm -rf`, long flags, force-with-lease, `+refspec`, case-insensitive SQL, bounded deletes, safe commands, non-Bash events, malformed JSON, and JSONL audit logging.

No third-party Python packages are required.

## Design choices

- **Token-aware checks for `rm` and Git.** This catches flag-order variations that literal substring checks miss.
- **Statement-aware `DELETE` rule.** `DELETE FROM` is denied only when its statement has no `WHERE`.
- **Explicit safe-path tests.** A safety hook is useful only if it does not break normal development.
- **Fail-open on malformed unrelated hook input.** Bad input should not brick Claude Code; high-confidence dangerous commands are still denied.
- **Blocking is independent of logging.** If the audit file cannot be written, the deny decision is still returned.
- **Stdlib only.** The hook remains portable and installation stays one command.
