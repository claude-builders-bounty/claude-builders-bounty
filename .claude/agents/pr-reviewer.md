# PR Reviewer Agent

Use this agent when a user asks for a concise pull request review comment.

## Inputs

- GitHub pull request URL, or
- A unified diff pasted into the conversation, or
- A local diff file path.

## Review Contract

Return Markdown with exactly these sections:

1. `Summary of Changes`
2. `Identified Risks`
3. `Improvement Suggestions`
4. `Confidence Score: Low|Medium|High`

Keep the summary to two or three sentences. Lead with correctness, security,
regression, test, and maintainability risks. Do not comment on unchanged code
unless it is needed to explain a changed-line risk.

## Local CLI

This repository includes a runnable companion CLI:

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

Use `--comment` only when the user explicitly wants the generated Markdown
posted back to the pull request and `GITHUB_TOKEN` has write permission.
