## Summary
This PR changes 4 file(s), with 589 additions and 0 deletions. The main touched paths are `README.md`, `hooks/block_destructive_bash.py`, `scripts/install_block_destructive_bash_hook.py`, `tests/test_block_destructive_bash.py`.
The change is submitted by `@Treasure520520` in `claude-builders-bounty/claude-builders-bounty` PR #1033: feat: add destructive bash command blocker hook.

## Risks
- `README.md` is documentation-only unless paired with implementation changes.
- New command execution or dynamic evaluation appears in the diff.
- The patch removes test/assertion code; confirm coverage did not regress.

## Suggestions
- Call out the highest-risk behavior in the PR description with exact verification steps.
- Preview the rendered documentation to catch broken links, formatting, and headings.

## Confidence: Medium
