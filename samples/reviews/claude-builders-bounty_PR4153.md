## Summary
Introduces a Claude Code `PreToolUse` Python hook that denies destructive bash (`rm -rf`, force-push, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`) and appends each block to `~/.claude/hooks/blocked.log`, with a two-command install README.

## Risks
- Regex false positives could block legitimate automation that embeds banned substrings in strings/comments.
- Hook denial UX depends on Claude Code honoring non-zero exit + JSON decision payload for the installed version.

## Suggestions
- Add a `--dry-run` / allowlist file for known-safe project scripts.
- Cover `git push --force-with-lease` explicitly if the policy should treat it like `--force`.

## Confidence
High — local stdin fixtures confirmed block/allow behavior for the listed patterns before submission.
