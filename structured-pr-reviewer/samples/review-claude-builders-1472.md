## Structured PR Review

### Summary of changes
This PR changes 3 file(s) with +419/-0 lines. The main touched areas are destructive-bash-guard. Largest changes: destructive-bash-guard/block-destructive-bash.py, destructive-bash-guard/tests/test_block_destructive_bash.py, destructive-bash-guard/README.md.
PR title: **feat: add destructive bash command guard** by @liushihao456.

### Identified risks
- Potential DELETE FROM without WHERE detected; verify it cannot wipe entire tables unintentionally.

### Improvement suggestions
- Keep the PR description updated with validation steps and any known limitations.

### Confidence score
**Low**
