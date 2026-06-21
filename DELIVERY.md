# Delivery notes for issue #3

## Issue readout

Issue: <https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3>

Bounty: **$100** via Opire.

Acceptance criteria implemented:

- Claude Code `PreToolUse` hook in Python under `.claude/hooks/`
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`
- Logs every blocked attempt to `~/.claude/hooks/blocked.log`
- Log includes timestamp, attempted command, project path, plus reason
- Emits a clear deny message to Claude Code via `hookSpecificOutput.permissionDecisionReason`
- Allows normal Bash commands silently
- README install is 2 shell commands
- Test script covers dangerous and safe commands

## Files to include in PR

- `.claude/hooks/block-destructive-bash.py`
- `.claude/settings.json`
- `tests/test_block_destructive_bash.py`
- `bounty-3-destructive-bash-hook/README.md`

Optional PR cleanup: if maintainers prefer top-level docs, move `bounty-3-destructive-bash-hook/README.md` to a more conventional path such as `hooks/destructive-bash-blocker/README.md` together with the hook. Current layout keeps the repository's original README intact.

## Test result

Command run locally:

```bash
python3 tests/test_block_destructive_bash.py
```

Result:

```text
PASS: blocked 7 dangerous commands and allowed 7 safe commands
```

Manual denial/log smoke test also passed for `rm -rf /tmp/demo`; the hook printed Claude Code deny JSON and wrote one JSONL record to `~/.claude/hooks/blocked.log` in an isolated temporary HOME.

## Suggested PR title

Add Claude Code hook to block destructive Bash commands

## Suggested PR description

```markdown
## Summary

Adds a Claude Code `PreToolUse` hook that denies destructive Bash commands before execution.

The hook blocks:

- `rm -rf` / `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, project path, and reason. Safe Bash commands emit no hook output and continue through the normal Claude Code permission flow.

## Files

- `.claude/hooks/block-destructive-bash.py`
- `.claude/settings.json`
- `tests/test_block_destructive_bash.py`
- `bounty-3-destructive-bash-hook/README.md`

## Test

```bash
python3 tests/test_block_destructive_bash.py
```

Output:

```text
PASS: blocked 7 dangerous commands and allowed 7 safe commands
```

Closes #3.
```

## Suggested issue comment

```markdown
/opire try

I have a local implementation ready for the destructive Bash command blocker:

- Python Claude Code `PreToolUse` hook
- Blocks `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`
- Logs blocked attempts to `~/.claude/hooks/blocked.log`
- Includes 2-command install docs and a test script for dangerous/safe commands

Local test result: `PASS: blocked 7 dangerous commands and allowed 7 safe commands`.
```

## Backup bounty quick review

- #1 `$50` changelog generator: easier technically, but lower bounty and there are many existing PRs; likely more competition.
- #2 `$75` Next.js + SQLite `CLAUDE.md`: writing-only and straightforward, but acceptance is subjective and also has many PRs.
- #3 remains best primary target: highest among #1/#2/#3 and objective tests/acceptance criteria.
