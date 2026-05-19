# Claude PR Reviewer

Generate a structured Markdown review from a GitHub pull request diff.

## Setup and usage

```bash
chmod +x tools/pr-reviewer/claude-review
GITHUB_TOKEN=optional_token tools/pr-reviewer/claude-review --pr https://github.com/owner/repo/pull/123
```

`GITHUB_TOKEN` is optional for public repositories but recommended to avoid GitHub API rate limits.

## Output format

The CLI prints Markdown with:

- Summary of changes
- Identified risks
- Improvement suggestions
- Testing notes
- Confidence score: `Low`, `Medium`, or `High`

## Sample output: public PR 1

```md
# PR Review Summary

## Summary
Handle oversized avatar uploads gracefully changes 5 file(s) with approximately +120/-34 diff lines. The PR body starts with: Closes #31

## Identified Risks
- No obvious high-risk patterns detected from the diff alone; still review logic and tests manually.

## Improvement Suggestions
- Confirm the PR includes a focused test or documented manual validation path.
- Check that the implementation scope matches the linked issue and does not add unrelated behavior.
- Review edge cases around empty inputs, API failures, and permission errors where relevant.

## Confidence
Medium
```

## Sample output: public PR 2

```md
# PR Review Summary

## Summary
Add pre-tool-use hook to block destructive bash commands changes 2 file(s) with approximately +122/-0 diff lines. The PR body starts with: Closes #3

## Identified Risks
- Command execution surface changed; verify inputs are trusted or sanitized.

## Improvement Suggestions
- Confirm the PR includes a focused test or documented manual validation path.
- Check that the implementation scope matches the linked issue and does not add unrelated behavior.
- Review edge cases around empty inputs, API failures, and permission errors where relevant.

## Confidence
High
```
