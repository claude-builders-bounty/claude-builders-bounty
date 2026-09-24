## Summary
This PR adds a Claude Code `PreToolUse` hook that blocks destructive Bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without `WHERE`) before execution. It logs every block to `~/.claude/hooks/blocked.log` with timestamp, command and project path, returns a clear reason to Claude, and ships with a README and a test script.

## Identified risks
- The `git push --force` regex matches `git push ... --force` but misses the short form `git push -f` and `--force-with-lease`.
- `rm -r` without `-f` and `rm -rf` with `-` reordering (e.g. `rm -fr`) are not covered by the `rm -rf` pattern.
- The hook only guards the `Bash` tool; destructive SQL issued through a different tool would not be intercepted.

## Improvement suggestions
- Broaden the git rule to `git push .*(-f|--force|--force-with-lease)`.
- Add a dry-run flag so the hook can be exercised without mutating `~/.claude/hooks/blocked.log`.

## Confidence
Medium — the required patterns are covered and the test script verifies them, but several destructive variants remain uncaught.
