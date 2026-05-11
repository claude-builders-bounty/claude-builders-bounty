# Review a GitHub Pull Request

Reviews a GitHub pull request and produces a structured Markdown report covering summary, risks, improvement suggestions, and confidence score.

## Usage

```
/review-pr https://github.com/owner/repo/pull/N
```

## Instructions

When this skill is invoked with a GitHub PR URL:

1. Use the Bash tool to fetch the PR metadata:
   ```bash
   curl -s "https://api.github.com/repos/OWNER/REPO/pulls/NUMBER"
   ```

2. Use the Bash tool to fetch the diff:
   ```bash
   curl -s -H "Accept: application/vnd.github.v3.diff" \
     "https://api.github.com/repos/OWNER/REPO/pulls/NUMBER"
   ```

3. Analyse the PR and produce the following structured Markdown — **nothing else**:

```
## Summary
(2–3 sentences describing what this PR does and why)

## Identified Risks
- (list each risk; write "None identified" if clean)

## Improvement Suggestions
- (actionable suggestions; write "None" if none)

## Confidence Score
(one of: Low | Medium | High — based on diff clarity, test coverage, and scope)
```

## Notes
- Truncate diffs longer than 12 000 characters to the first 12 000 characters to stay within context limits.
- If the GitHub API rate-limits you, ask the user to set `GITHUB_TOKEN` in their environment.
- Never output anything outside the four Markdown sections above.
