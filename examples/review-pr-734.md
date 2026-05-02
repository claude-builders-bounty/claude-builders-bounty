## PR Review — feat: add destructive command guard hook

### Summary
This PR changes 3 file(s) with 137 additions and 0 deletions across 3 diff hunk(s). The touched areas are: 2 docs, 1 code.
The review below is generated from the public GitHub PR diff and is intended as a structured first pass for Claude Code or human reviewers.

### Identified risks
- Potentially destructive command or SQL pattern appears; confirm safeguards and rollback path.

### Improvement suggestions
- Run the project test/lint commands and include the exact output in the PR.
- Check examples and setup commands by copying them into a clean shell/session.
- Confirm the implementation maps directly to the issue acceptance criteria.

### Confidence score: Medium
