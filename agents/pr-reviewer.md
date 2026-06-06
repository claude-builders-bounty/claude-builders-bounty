# Claude PR Reviewer Agent

Use this agent when a user asks for a structured review of a GitHub pull request.

## Inputs

- Pull request URL or `owner/repo#number`.
- Optional reviewer focus, such as security, tests, docs, or migration safety.

## Output Contract

Return Markdown with exactly these sections:

1. `## Summary`
2. `## Identified Risks`
3. `## Improvement Suggestions`
4. `## Confidence: Low|Medium|High`

Keep the summary to 2-3 sentences. Risks should be concrete and tied to files,
behavior, or validation gaps. Suggestions should be actionable. Confidence is
based on diff size, test coverage in the diff, and how much behavior can be
validated from the available patch.

## CLI

```bash
bin/claude-review --pr https://github.com/owner/repo/pull/123
bin/claude-review --pr owner/repo#123
```

Set `GITHUB_TOKEN` to increase GitHub API rate limits. Set
`CLAUDE_REVIEW_USE_CLAUDE=1` to ask the local `claude` CLI to review the diff;
otherwise the tool returns a deterministic structured review using local
heuristics.
