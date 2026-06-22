# PR Review: anthropics/claude-code#69916 — fix: print error message before silent exit in edit-issue-labels.sh

## Summary
This PR adds an error message to `scripts/edit-issue-labels.sh` when the script is called without any `--add-label` or `--remove-label` arguments. Previously, the script would silently exit with code 1, making it hard to debug usage errors.

## Risks
- The error message goes to stderr (>&2), which is correct behavior for error output
- No risk of breaking existing functionality — this only adds output to an existing early-exit path
- The exit code (1) is preserved, so CI pipelines that check for failure won't be affected

## Suggestions
- Consider adding a usage hint in the error message (e.g., "Usage: edit-issue-labels.sh --add-label foo --remove-label bar")
- Could also print the script's help text on error for a better developer experience

## Confidence
High
